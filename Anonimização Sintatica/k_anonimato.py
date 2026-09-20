"""
Trabalho 2 - k-Anonimato

Aplica k-anonimato aos atributos semi-identificadores municipioCaso e
dataNascimento do covid.csv, tratando racaCor como atributo sensível.

Reaproveita as hierarquias de generalização construídas no Trabalho 1
(módulo hierarquia.py).
"""

import os
import itertools
import pandas as pd
import matplotlib.pyplot as plt

from hierarquia import construir_hierarquia_municipio, construir_hierarquia_data


COLUNAS_INTERESSE = ["municipioCaso", "dataNascimento", "racaCor"]
ALTURA_MUNICIPIO = 2  # níveis 0, 1, 2
ALTURA_DATA = 3       # níveis 0, 1, 2, 3
LIMIAR_SUPRESSAO = 0.05  # até 5% dos registros podem ser suprimidos por nível


def preprocessar(caminho_covid):
    """
    Mantém apenas municipioCaso, dataNascimento e racaCor, e remove
    registros com valor nulo ou vazio em qualquer um desses atributos,
    conforme pede o enunciado.
    """
    df = pd.read_csv(caminho_covid, usecols=COLUNAS_INTERESSE)
    df = df.dropna(subset=COLUNAS_INTERESSE)
    for col in COLUNAS_INTERESSE:
        df = df[df[col].astype(str).str.strip() != ""]
    return df.reset_index(drop=True)


def gerar_reticulado():
    """
    Gera o reticulado de combinações (nm, nd) de níveis de generalização
    para os dois quase-identificadores, ordenado por altura total
    crescente (menor distorção primeiro).
    """
    combinacoes = list(itertools.product(
        range(ALTURA_MUNICIPIO + 1), range(ALTURA_DATA + 1)
    ))
    combinacoes.sort(key=lambda par: par[0] + par[1])
    return combinacoes


def generalizar(df, hierarquia_municipio, hierarquia_data, nm, nd):
    """Aplica a generalização de nível nm/nd aos dois quase-identificadores."""
    df_gen = df.copy()
    df_gen["municipioCaso"] = df_gen["municipioCaso"].map(
        hierarquia_municipio[f"nivel {nm}"]
    )
    df_gen["dataNascimento"] = df_gen["dataNascimento"].map(
        hierarquia_data[f"nivel {nd}"]
    )
    return df_gen


def tamanho_minimo_classe(df_gen):
    """
    Agrupa pelo par (municipioCaso, dataNascimento) generalizado e
    retorna o tamanho da menor classe de equivalência, junto com as
    contagens de todas as classes.
    """
    contagens = df_gen.groupby(["municipioCaso", "dataNascimento"]).size()
    return contagens.min(), contagens


def calcular_precisao(nm, nd):
    """
    Prec(D) = 1 - (1/Na) * sum(h_i / H_i)

    Como a generalização é feita a nível de atributo (mesmo nível para
    todas as linhas), o somatório duplo da fórmula original se reduz a
    esta forma fechada, com Na = 2 (municipioCaso e dataNascimento).
    """
    Na = 2
    return 1 - (1 / Na) * ((nm / ALTURA_MUNICIPIO) + (nd / ALTURA_DATA))


def encontrar_generalizacao_minima(df, hierarquia_municipio, hierarquia_data, k):
    """
    Percorre o reticulado em ordem crescente de altura total. Para cada
    nível, se todas as classes de equivalência já satisfazem k, aceita
    esse nível sem supressão. Caso contrário, verifica se a fração de
    registros em classes menores que k (candidatos à supressão) fica
    dentro de LIMIAR_SUPRESSAO — se sim, suprime só esses registros e
    aceita o nível, evitando generalizar tudo até o topo por causa de
    poucos casos raros (ex.: uma data de nascimento isolada).

    Se nenhum nível do reticulado ficar dentro do limiar, usa como
    último recurso o nível cuja taxa de supressão foi a menor entre os
    testados (combinando generalização e supressão, conforme Sweeney,
    2002).

    Retorna: (nm, nd, df_resultado, contagens, n_suprimidos)
    """
    total = len(df)
    melhor_fallback = None

    for nm, nd in gerar_reticulado():
        df_gen = generalizar(df, hierarquia_municipio, hierarquia_data, nm, nd)
        contagens = df_gen.groupby(["municipioCaso", "dataNascimento"]).size()

        if contagens.min() >= k:
            return nm, nd, df_gen, contagens, 0

        classes_pequenas = set(contagens[contagens < k].index)
        chave = list(zip(df_gen["municipioCaso"], df_gen["dataNascimento"]))
        mascara_suprimir = pd.Series(chave, index=df_gen.index).isin(classes_pequenas)
        n_suprimidos = int(mascara_suprimir.sum())
        taxa_supressao = n_suprimidos / total

        if taxa_supressao <= LIMIAR_SUPRESSAO:
            df_result = df_gen[~mascara_suprimir].reset_index(drop=True)
            contagens_result = df_result.groupby(["municipioCaso", "dataNascimento"]).size()
            return nm, nd, df_result, contagens_result, n_suprimidos

        if melhor_fallback is None or taxa_supressao < melhor_fallback[-1]:
            melhor_fallback = (nm, nd, df_gen, mascara_suprimir, n_suprimidos, taxa_supressao)

    nm, nd, df_gen, mascara_suprimir, n_suprimidos, _ = melhor_fallback
    df_result = df_gen[~mascara_suprimir].reset_index(drop=True)
    contagens_result = df_result.groupby(["municipioCaso", "dataNascimento"]).size()
    return nm, nd, df_result, contagens_result, n_suprimidos


def gerar_histograma_classes(contagens, k, pasta_saida="."):
    """Plota a distribuição de tamanhos das classes de equivalência."""
    plt.figure(figsize=(10, 6))
    contagens.value_counts().sort_index().plot(kind="bar")
    plt.title(f"Tamanho das classes de equivalência - k={k}")
    plt.xlabel("Tamanho da classe")
    plt.ylabel("Número de classes")
    plt.tight_layout()

    nome_arquivo = os.path.join(pasta_saida, f"HIST_classes_k{k}.png")
    plt.savefig(nome_arquivo)
    plt.close()
    print(f"Histograma gerado: {nome_arquivo}")


def main():
    caminho_covid = "dataset/covid.csv"
    caminho_mapa = "dataset/map_municipio_regiao.csv"

    df = preprocessar(caminho_covid)
    print(f"Registros após pré-processamento: {len(df)}")

    hierarquia_municipio, _sem_mapeamento = construir_hierarquia_municipio(
        caminho_covid, caminho_mapa
    )
    hierarquia_data = construir_hierarquia_data(caminho_covid)

    for k in (2, 4, 8, 16):
        nm, nd, df_gen, contagens, n_suprimidos = encontrar_generalizacao_minima(
            df, hierarquia_municipio, hierarquia_data, k
        )
        precisao = calcular_precisao(nm, nd)
        tamanho_medio = len(df_gen) / len(contagens)

        nome_dataset = f"covid_{k}.csv"
        df_gen.to_csv(nome_dataset, index=False)

        gerar_histograma_classes(contagens, k)

        print(f"\nDataset: {nome_dataset}")
        print(f"  nm={nm}, nd={nd}")
        print(f"  Precisão: {precisao:.4f}")
        print(f"  Tamanho médio das classes de equivalência: {tamanho_medio:.2f}")
        print(f"  Número de classes de equivalência: {len(contagens)}")
        if n_suprimidos:
            print(f"  [AVISO] {n_suprimidos} registro(s) suprimido(s) por ficarem "
                  f"em classes de equivalência menores que k={k} neste nível.")


if __name__ == "__main__":
    main()