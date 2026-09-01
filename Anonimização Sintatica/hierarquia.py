import csv
import json
import unicodedata
from datetime import datetime

ESTADO_PADRAO = "Ceara"


def normalizar_nome(texto):
    """
    Remove acentos e normaliza maiusculas/espacos de um nome de municipio,
    para permitir comparar 'BATURITÉ' (no dataset) com 'BATURITE' (no mapa
    de municipio->regiao), que usam grafias ligeiramente diferentes.
    """
    texto = texto.strip().upper()
    sem_acentos = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sem_acentos if not unicodedata.combining(c))


# ---------------------------------------------------------------------------
# HIERARQUIA DE municipioCaso (3 niveis: municipio -> regiao -> estado)
# ---------------------------------------------------------------------------

def carregar_mapeamento_municipio_regiao(caminho_mapa_csv):
    """
    Le o arquivo 'map_municipio_regiao.csv' fornecido para o trabalho e monta
    um dicionario que relaciona a versao normalizada (sem acento, maiuscula)
    do nome do municipio a sua regiao e ao nome original como aparece no
    mapa (para exibir no JSON final com a grafia do mapa).

    O CSV tem colunas: (indice sem nome), municipio, regiao.

    Retorna:
        dict no formato:
        {
            "ABAIARA": {"regiao": "CARIRI", "nome_mapa": "ABAIARA"},
            ...
        }
        onde a chave e o nome do municipio normalizado (sem acento).
    """
    mapeamento = {}

    with open(caminho_mapa_csv, mode="r", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            municipio = linha["municipio"].strip()
            regiao = linha["regiao"].strip()

            chave = normalizar_nome(municipio)
            mapeamento[chave] = {"regiao": regiao, "nome_mapa": municipio}

    return mapeamento


def extrair_municipios_do_dataset(caminho_dataset_csv, coluna="municipioCaso"):
    """
    Percorre o dataset original (covid.csv) e retorna o conjunto (set) de
    valores distintos encontrados na coluna de municipio.
    """
    municipios = set()

    with open(caminho_dataset_csv, mode="r", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            valor = linha.get(coluna, "").strip()
            if valor:
                municipios.add(valor)

    return municipios


def gerar_hierarquia_municipio(caminho_dataset_csv, caminho_mapa_csv,
                                caminho_saida_json):
    """
    Constroi a hierarquia de 3 niveis para 'municipioCaso' e salva em JSON:
        nivel 0: municipio original
        nivel 1: regiao do municipio
        nivel 2: estado do municipio

    Municipios presentes no dataset mas sem correspondencia no mapa de
    municipio->regiao sao reportados (para que sejam excluidos depois,
    na etapa de anonimizacao, conforme pede o enunciado).

    Retorna a lista de municipios SEM mapeamento encontrado (para uso no
    modulo de anonimizacao, que deve excluir esses registros).
    """
    mapa = carregar_mapeamento_municipio_regiao(caminho_mapa_csv)
    municipios_dataset = extrair_municipios_do_dataset(caminho_dataset_csv)

    nivel_0 = {}
    nivel_1 = {}
    nivel_2 = {}
    sem_mapeamento = []

    for municipio in municipios_dataset:
        chave = normalizar_nome(municipio)

        if chave not in mapa:
            sem_mapeamento.append(municipio)
            continue

        # Mantem a chave do JSON com a grafia original do dataset, como no
        # exemplo do enunciado (ex.: "Fortaleza": "Fortaleza")
        nivel_0[municipio] = municipio
        nivel_1[municipio] = mapa[chave]["regiao"]
        nivel_2[municipio] = ESTADO_PADRAO

    hierarquia = {
        "nivel 0": nivel_0,
        "nivel 1": nivel_1,
        "nivel 2": nivel_2,
    }

    with open(caminho_saida_json, mode="w", encoding="utf-8") as arquivo:
        json.dump(hierarquia, arquivo, ensure_ascii=False, indent=2)

    if sem_mapeamento:
        print(f"[AVISO] {len(sem_mapeamento)} municipio(s) sem mapeamento "
              f"de regiao/estado: {sem_mapeamento}")

    return sem_mapeamento


# ---------------------------------------------------------------------------
# HIERARQUIA DE dataNascimento (4 niveis)
# ---------------------------------------------------------------------------

def calcular_faixa_5_anos(ano):
    """
    Dado um ano (int), retorna a faixa de 5 anos correspondente no formato
    'aaaa-aaaa'. Ex.: 2003 -> '2001-2005'; 2010 -> '2006-2010'.
    """
    # Ajusta o ano para o inicio do bloco de 5 anos mais proximo
    inicio = ((ano - 1) // 5) * 5 + 1
    fim = inicio + 4
    return f"{inicio}-{fim}"


def extrair_datas_do_dataset(caminho_dataset_csv, coluna="dataNascimento"):
    """
    Percorre o dataset original e retorna o conjunto de datas distintas
    (strings no formato dd/mm/aaaa) encontradas na coluna informada.
    """
    datas = set()

    with open(caminho_dataset_csv, mode="r", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            valor = linha.get(coluna, "").strip()
            # Ha registros com data vazia ('') no dataset real -- sao
            # tratados como ausentes e ignorados.
            if valor:
                datas.add(valor)

    return datas


def gerar_hierarquia_data_nascimento(caminho_dataset_csv, caminho_saida_json,
                                      formato_entrada="%Y-%m-%d"):
    """
    Constroi a hierarquia de 4 niveis para 'dataNascimento' e salva em JSON:
        nivel 0: data completa (dd/mm/aaaa)
        nivel 1: mes/ano (mm/aaaa)
        nivel 2: ano (aaaa)
        nivel 3: faixa de 5 anos (ex.: 2001-2005)
    """
    datas = extrair_datas_do_dataset(caminho_dataset_csv)

    nivel_0 = {}
    nivel_1 = {}
    nivel_2 = {}
    nivel_3 = {}
    invalidas = []

    for data_str in datas:
        try:
            data = datetime.strptime(data_str, formato_entrada)
        except ValueError:
            invalidas.append(data_str)
            continue

        nivel_0[data_str] = data_str
        nivel_1[data_str] = data.strftime("%m/%Y")
        nivel_2[data_str] = data.strftime("%Y")
        nivel_3[data_str] = calcular_faixa_5_anos(data.year)

    hierarquia = {
        "nivel 0": nivel_0,
        "nivel 1": nivel_1,
        "nivel 2": nivel_2,
        "nivel 3": nivel_3,
    }

    with open(caminho_saida_json, mode="w", encoding="utf-8") as arquivo:
        json.dump(hierarquia, arquivo, ensure_ascii=False, indent=2)

    if invalidas:
        print(f"[AVISO] {len(invalidas)} data(s) em formato invalido: "
              f"{invalidas}")

    return invalidas


# ---------------------------------------------------------------------------
# EXECUCAO DIRETA (para testar o modulo isoladamente)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Ajustar os caminhos conforme a estrutura real de pastas do projeto
    CAMINHO_DATASET = "dataset/covid.csv"
    CAMINHO_MAPA_MUNICIPIO_REGIAO = "dataset/map_municipio_regiao.csv"
    # 'covid.csv' (colunas incluem 'municipioCaso', 'dataNascimento' em
    # formato aaaa-mm-dd) e 'map_municipio_regiao.csv' (colunas: indice,
    # municipio, regiao -- sem coluna de estado).
    CAMINHO_SAIDA_MUNICIPIO_JSON = "hierarquia_municipioCaso.json"
    CAMINHO_SAIDA_DATA_JSON = "hierarquia_dataNascimento.json"

    print("Gerando hierarquia de municipioCaso...")
    gerar_hierarquia_municipio(
        CAMINHO_DATASET,
        CAMINHO_MAPA_MUNICIPIO_REGIAO,
        CAMINHO_SAIDA_MUNICIPIO_JSON,
    )

    print("Gerando hierarquia de dataNascimento...")
    gerar_hierarquia_data_nascimento(
        CAMINHO_DATASET,
        CAMINHO_SAIDA_DATA_JSON,
    )

    print("Concluido.")
