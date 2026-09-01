# Módulo que aplica a generalização, gera os datasets DT_nm_nd.csv e os histogramas HIST_<atributo>_<nivel>.png


import os
import pandas as pd
import matplotlib.pyplot as plt

from hierarquia import construir_hierarquia_municipio, construir_hierarquia_data


def carregar_dataset_valido(caminho_covid, hierarquia_municipio):
    """Remove registros cujo município não possui mapeamento na hierarquia."""
    df = pd.read_csv(caminho_covid)
    municipios_validos = set(hierarquia_municipio["nivel 0"].keys())
    return df[df["municipioCaso"].isin(municipios_validos)].copy()


def gerar_histograma(serie, atributo, nivel, pasta_saida="."):
    plt.figure(figsize=(10, 6))
    contagem = serie.value_counts()
    contagem.plot(kind="bar")

    if atributo == "municipioCaso" and nivel == 0:
        # muitos municípios distintos: oculta os rótulos no nível 0
        plt.xticks([])
    else:
        plt.xticks(rotation=45, ha="right")

    plt.title(f"{atributo} - nível {nivel}")
    plt.ylabel("Frequência")
    plt.tight_layout()

    nome_arquivo = os.path.join(pasta_saida, f"HIST_{atributo}_{nivel}.png")
    plt.savefig(nome_arquivo)
    plt.close()
    print(f"Histograma gerado: {nome_arquivo}")


def generalizar(df, hierarquia_municipio, hierarquia_data, nm, nd):
    df_gen = df.copy()
    df_gen["municipioCaso"] = df_gen["municipioCaso"].map(hierarquia_municipio[f"nivel {nm}"])
    df_gen["dataNascimento"] = df_gen["dataNascimento"].map(hierarquia_data[f"nivel {nd}"])
    return df_gen


def main():
    caminho_covid = "dataset/covid.csv"
    caminho_mapa = "dataset/map_municipio_regiao.csv"

    hierarquia_municipio, _ = construir_hierarquia_municipio(caminho_covid, caminho_mapa)
    hierarquia_data = construir_hierarquia_data(caminho_covid)

    df_valido = carregar_dataset_valido(caminho_covid, hierarquia_municipio)

    # histogramas do dataset original (nível 0)
    gerar_histograma(df_valido["municipioCaso"], "municipioCaso", 0)
    gerar_histograma(df_valido["dataNascimento"], "dataNascimento", 0)

    while True:
        try:
            nm = int(input("Nível de generalização para municipioCaso (0-2, -1 para sair): "))
            nd = int(input("Nível de generalização para dataNascimento (0-3, -1 para sair): "))
        except ValueError:
            print("Digite valores inteiros.")
            continue

        if nm == -1 and nd == -1:
            print("Encerrando.")
            break

        if not (0 <= nm <= 2) or not (0 <= nd <= 3):
            print("Níveis fora do intervalo permitido.")
            continue

        df_pub = generalizar(df_valido, hierarquia_municipio, hierarquia_data, nm, nd)

        nome_dataset = f"DT_{nm}_{nd}.csv"
        df_pub.to_csv(nome_dataset, index=False)
        print(f"Dataset gerado: {nome_dataset}")

        gerar_histograma(df_pub["municipioCaso"], "municipioCaso", nm)
        gerar_histograma(df_pub["dataNascimento"], "dataNascimento", nd)


if __name__ == "__main__":
    main()