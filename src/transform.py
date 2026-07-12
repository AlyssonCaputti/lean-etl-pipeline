from pathlib import Path

import pandas as pd

RAW_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "manutencoes.csv"


def carregar_dados_brutos(caminho=RAW_PATH):
    df = pd.read_csv(caminho)
    df["data_servico"] = pd.to_datetime(df["data_servico"], format="%d/%m/%Y")
    # export do SAP B1 vem com vírgula decimal, sem isso o pandas lê "custo" como string
    df["custo"] = df["custo"].astype(str).str.replace(",", ".").astype(float)
    return df


def limpar_dados(df):
    # tira linha sem placa/tipo/custo e custo negativo (não deveria existir mas segue o jogo)
    df = df.dropna(subset=["placa", "tipo_servico", "custo"])
    df = df[df["custo"] > 0]
    return df


def agregar_por_tipo_regional(df):
    agrupado = (
        df.groupby(["tipo_servico", "regional"])
        .agg(custo_total=("custo", "sum"), qtd_servicos=("custo", "count"), custo_medio=("custo", "mean"))
        .reset_index()
        .sort_values("custo_total", ascending=False)
    )
    agrupado["custo_total"] = agrupado["custo_total"].round(2)
    agrupado["custo_medio"] = agrupado["custo_medio"].round(2)
    return agrupado


def pipeline_transform(caminho=RAW_PATH):
    df = carregar_dados_brutos(caminho)
    df = limpar_dados(df)
    return agregar_por_tipo_regional(df)


if __name__ == "__main__":
    print(pipeline_transform().head(10))
