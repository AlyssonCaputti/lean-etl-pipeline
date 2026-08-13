"""
Transform: le o CSV bruto, limpa e agrega custo por tipo de servico e regional.

O fluxo passa por duas portas de qualidade (ver quality_checks.py): uma no dado
cru, outra no agregado. A segunda recebe tambem o df de origem pra reconciliar
a soma - sem isso, um groupby com chave errada passa despercebido.
"""

from pathlib import Path

import pandas as pd

from src.quality_checks import validar_entrada, validar_saida

# Precisa vir antes dos def: valor default de parametro e avaliado quando a
# funcao e definida, nao quando e chamada.
RAW_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "manutencoes.csv"


def carregar_dados_brutos(caminho=RAW_PATH):
    df = pd.read_csv(caminho)
    df["data_servico"] = pd.to_datetime(df["data_servico"], format="%d/%m/%Y")
    # export do SAP B1 vem com vírgula decimal, sem isso o pandas lê "custo" como string
    df["custo"] = df["custo"].astype(str).str.replace(",", ".").astype(float)
    return df


def limpar_dados(df):
    """Tira linha sem placa/tipo/custo, e custo zerado ou negativo.

    Conto o descarte e imprimo em vez de sumir com ele calado: a diferenca
    entre o que entrou e o que saiu daqui e a unica pista de que a origem
    mandou sujeira.
    """
    antes = len(df)
    df = df.dropna(subset=["placa", "tipo_servico", "custo"])
    df = df[df["custo"] > 0]
    descartadas = antes - len(df)

    if descartadas:
        print(f"limpar_dados: {descartadas} de {antes} linha(s) descartada(s)")

    return df


def agregar_por_tipo_regional(df):
    agrupado = (
        df.groupby(["tipo_servico", "regional"])
        .agg(
            custo_total=("custo", "sum"),
            qtd_servicos=("custo", "count"),
            custo_medio=("custo", "mean"),
        )
        .reset_index()
        .sort_values("custo_total", ascending=False)
    )
    agrupado["custo_total"] = agrupado["custo_total"].round(2)
    agrupado["custo_medio"] = agrupado["custo_medio"].round(2)
    return agrupado


def pipeline_transform(caminho=RAW_PATH):
    df = carregar_dados_brutos(caminho)

    validar_entrada(df)                   # Porta 1: o dado como veio da origem
    df_limpo = limpar_dados(df)
    agregado = agregar_por_tipo_regional(df_limpo)
    validar_saida(agregado, df_limpo)     # Porta 2: agregado + reconciliacao da soma

    return agregado


if __name__ == "__main__":
    print(pipeline_transform().head(10))
