"""
Testes das checagens de qualidade. Uso DataFrames pequenos montados na mao
mesmo, nao preciso do CSV gerado pra testar a logica isolada.
"""

import pandas as pd
import pytest

from src.extract import separar_quarentena
from src.quality_checks import (
    FalhaQualidadeDados,
    checar_chave_nao_nula,
    checar_chave_unica,
    checar_nao_vazio,
    checar_valor_nao_negativo,
    validar_entrada,
)


def df_base() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id_manutencao": [1, 2, 3],
            "custo": [100.0, 200.0, 300.0],
            "data_manutencao": ["2026-01-01", "2026-02-01", "2026-03-01"],
        }
    )


def test_dataframe_vazio_estoura_erro():
    with pytest.raises(FalhaQualidadeDados):
        checar_nao_vazio(pd.DataFrame())


def test_chave_nula_estoura_erro():
    df = df_base()
    df.loc[0, "id_manutencao"] = None
    with pytest.raises(FalhaQualidadeDados):
        checar_chave_nao_nula(df, "id_manutencao")


def test_chave_duplicada_estoura_erro():
    df = pd.concat([df_base(), df_base().iloc[[0]]], ignore_index=True)
    with pytest.raises(FalhaQualidadeDados):
        checar_chave_unica(df, "id_manutencao")


def test_custo_negativo_estoura_erro():
    df = df_base()
    df.loc[0, "custo"] = -50.0
    with pytest.raises(FalhaQualidadeDados):
        checar_valor_nao_negativo(df, "custo")


def test_dataframe_limpo_passa_em_tudo():
    resultado = validar_entrada(df_base())
    assert resultado["status"] == "ok"
    assert resultado["linhas_validadas"] == 3


def test_quarentena_separa_linha_ruim_da_boa():
    df = df_base()
    df.loc[1, "custo"] = -999.0  # essa linha deve ir pra quarentena

    df_ok, df_quarentena = separar_quarentena(df)

    assert len(df_quarentena) == 1
    assert len(df_ok) == 2
    assert "custo_negativo" in df_quarentena.iloc[0]["motivo_quarentena"]
