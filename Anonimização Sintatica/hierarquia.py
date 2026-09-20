import csv
import unicodedata
from datetime import datetime


# Todo o dataset e do estado do Ceara (nao ha coluna de estado no arquivo
# de mapeamento), entao o nivel 2 da hierarquia de municipio e fixo.
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

def _carregar_mapa_municipio_regiao(caminho_mapa_csv):
    """
    Le 'map_municipio_regiao.csv' e monta um dicionario que relaciona a
    versao normalizada (sem acento, maiuscula) do nome do municipio a sua
    regiao. Colunas esperadas: municipio, regiao.
    """
    mapa = {}
    with open(caminho_mapa_csv, mode="r", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            municipio = linha["municipio"].strip()
            regiao = linha["regiao"].strip()
            mapa[normalizar_nome(municipio)] = regiao
    return mapa


def construir_hierarquia_municipio(caminho_covid, caminho_mapa):
    """
    Constroi a hierarquia de 3 niveis para 'municipioCaso':
        nivel 0: municipio original
        nivel 1: regiao do municipio
        nivel 2: estado (fixo, "Ceara")

    Parametros:
        caminho_covid: caminho para o covid.csv
        caminho_mapa: caminho para o map_municipio_regiao.csv

    Retorna:
        (hierarquia_municipio, sem_mapeamento)

        hierarquia_municipio: dict {"nivel 0": {...}, "nivel 1": {...},
                                     "nivel 2": {...}}, com o municipio
                               original do dataset como chave.
        sem_mapeamento: lista de municipios do dataset que nao possuem
                        correspondencia no mapa (para exclusao posterior).
    """
    mapa_regiao = _carregar_mapa_municipio_regiao(caminho_mapa)

    municipios_dataset = set()
    with open(caminho_covid, mode="r", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            valor = linha.get("municipioCaso", "").strip()
            if valor:
                municipios_dataset.add(valor)

    nivel_0, nivel_1, nivel_2 = {}, {}, {}
    sem_mapeamento = []

    for municipio in municipios_dataset:
        chave = normalizar_nome(municipio)

        if chave not in mapa_regiao:
            sem_mapeamento.append(municipio)
            continue

        nivel_0[municipio] = municipio
        nivel_1[municipio] = mapa_regiao[chave]
        nivel_2[municipio] = ESTADO_PADRAO

    hierarquia_municipio = {
        "nivel 0": nivel_0,
        "nivel 1": nivel_1,
        "nivel 2": nivel_2,
    }

    if sem_mapeamento:
        print(f"[AVISO] {len(sem_mapeamento)} municipio(s) sem mapeamento "
              f"de regiao: {sem_mapeamento}")

    return hierarquia_municipio, sem_mapeamento


# ---------------------------------------------------------------------------
# HIERARQUIA DE dataNascimento (4 niveis)
# ---------------------------------------------------------------------------

def _calcular_faixa_5_anos(ano):
    """
    Dado um ano (int), retorna a faixa de 5 anos correspondente no formato
    'aaaa-aaaa'. Ex.: 2003 -> '2001-2005'; 2010 -> '2006-2010'.
    """
    inicio = ((ano - 1) // 5) * 5 + 1
    fim = inicio + 4
    return f"{inicio}-{fim}"


def construir_hierarquia_data(caminho_covid, formato_entrada="%Y-%m-%d"):
    """
    Constroi a hierarquia de 4 niveis para 'dataNascimento':
        nivel 0: data completa (aaaa-mm-dd, formato do covid.csv)
        nivel 1: mes/ano (mm/aaaa)
        nivel 2: ano (aaaa)
        nivel 3: faixa de 5 anos (ex.: 2001-2005)

    Datas vazias ou em formato invalido sao ignoradas (o registro
    correspondente deve ser tratado como ausente pelo modulo de
    anonimizacao).

    Retorna:
        hierarquia_data: dict {"nivel 0": {...}, ..., "nivel 3": {...}},
                          com a data original (string) como chave.
    """
    datas = set()
    with open(caminho_covid, mode="r", encoding="utf-8") as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            valor = linha.get("dataNascimento", "").strip()
            if valor:
                datas.add(valor)

    nivel_0, nivel_1, nivel_2, nivel_3 = {}, {}, {}, {}
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
        nivel_3[data_str] = _calcular_faixa_5_anos(data.year)

    hierarquia_data = {
        "nivel 0": nivel_0,
        "nivel 1": nivel_1,
        "nivel 2": nivel_2,
        "nivel 3": nivel_3,
    }

    if invalidas:
        print(f"[AVISO] {len(invalidas)} data(s) em formato invalido: "
              f"{invalidas}")

    return hierarquia_data


# ---------------------------------------------------------------------------
# EXECUCAO DIRETA (para testar o modulo isoladamente)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    CAMINHO_DATASET = "dataset/covid.csv"
    CAMINHO_MAPA = "dataset/map_municipio_regiao.csv"

    print("Construindo hierarquia de municipioCaso...")
    hierarquia_municipio, sem_mapeamento = construir_hierarquia_municipio(
        CAMINHO_DATASET, CAMINHO_MAPA
    )
    print(f"  {len(hierarquia_municipio['nivel 0'])} municipios mapeados.")

    print("Construindo hierarquia de dataNascimento...")
    hierarquia_data = construir_hierarquia_data(CAMINHO_DATASET)
    print(f"  {len(hierarquia_data['nivel 0'])} datas mapeadas.")

    print("Concluido.")