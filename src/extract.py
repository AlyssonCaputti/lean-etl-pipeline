"""
Simula a extração de ordens de manutenção de frota vindas do ERP (SAP B1).

Obs: o export real do SAP costuma vir com separador decimal em vírgula
(padrão pt-BR), então geramos os dados aqui do mesmo jeito pra testar
o pipeline com um cenário mais próximo da realidade.

Tem também a quarentena: em vez de abortar a carga inteira por causa de
algumas linhas ruins, separo o que presta do que não presta e sigo com o que
presta — mas guardo o motivo de cada descarte, porque descarte sem motivo
registrado é perda de dado silenciosa com outro nome.
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

RAW_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "manutencoes.csv"

TIPOS_SERVICO = ["Troca de óleo", "Freios", "Suspensão", "Pneus", "Revisão elétrica"]
REGIONAIS = ["Curitiba", "Sao Paulo", "Joinville", "Londrina"]
PLACAS = [f"PR{n:04d}" for n in range(1, 31)]


def gerar_dados_brutos(n_linhas=400, seed=7):
    random.seed(seed)
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    inicio = datetime(2025, 6, 1)

    with open(RAW_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["data_servico", "placa", "tipo_servico", "regional", "custo"])

        for _ in range(n_linhas):
            data = inicio + timedelta(days=random.randint(0, 300))
            placa = random.choice(PLACAS)
            tipo = random.choice(TIPOS_SERVICO)
            regional = random.choice(REGIONAIS)
            custo = round(random.uniform(80.0, 2400.0), 2)
            # formato pt-BR igual ao export do ERP (vírgula decimal)
            custo_str = str(custo).replace(".", ",")
            writer.writerow([data.strftime("%d/%m/%Y"), placa, tipo, regional, custo_str])

    return RAW_PATH


def separar_quarentena(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa as linhas boas das ruins, anotando o motivo de cada descarte.

    Devolve (df_ok, df_quarentena). A quarentena leva uma coluna
    'motivo_quarentena' com o que reprovou — quando vem mais de um problema na
    mesma linha, os motivos ficam separados por ';'.

    A diferenca em relacao a Porta 1 (validar_entrada) e a intencao: a Porta 1
    aborta a carga toda quando o dado esta estruturalmente errado; a quarentena
    e pra quando algumas linhas estao ruins mas o arquivo, no geral, presta.
    Uma dispensa o dado do dia, a outra salva 99% dele.

    Quem chama decide o que fazer com a quarentena: gravar em tabela separada,
    mandar pra origem corrigir, ou so contar. O que nao pode e jogar fora sem
    ninguem ver.
    """
    if df.empty:
        vazio = df.copy()
        vazio["motivo_quarentena"] = pd.Series(dtype="object")
        return df.copy(), vazio

    motivos = pd.Series([""] * len(df), index=df.index, dtype="object")

    def marcar(mascara, motivo: str) -> None:
        mascara = mascara.fillna(False)
        motivos.loc[mascara] = motivos.loc[mascara].apply(
            lambda atual: f"{atual};{motivo}" if atual else motivo
        )

    if "custo" in df.columns:
        marcar(df["custo"].isna(), "custo_nulo")
        # comparacao numerica so nas linhas que sao numero de fato, senao
        # custo em texto viraria TypeError em vez de virar quarentena
        custo_num = pd.to_numeric(df["custo"], errors="coerce")
        marcar(custo_num < 0, "custo_negativo")
        marcar(custo_num == 0, "custo_zerado")

    for coluna in ("placa", "tipo_servico"):
        if coluna in df.columns:
            vazia = df[coluna].isna() | (
                df[coluna].astype(str).str.strip().eq("")
            )
            marcar(vazia, f"{coluna}_vazia" if coluna == "placa" else f"{coluna}_vazio")

    ruim = motivos.ne("")
    df_ok = df.loc[~ruim].copy()
    df_quarentena = df.loc[ruim].copy()
    df_quarentena["motivo_quarentena"] = motivos.loc[ruim]

    return df_ok, df_quarentena


if __name__ == "__main__":
    caminho = gerar_dados_brutos()
    print(f"gerado: {caminho}")
