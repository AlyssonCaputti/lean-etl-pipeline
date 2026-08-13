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
    """Mesmas colunas do CSV que a origem manda de verdade.

    Antes esse fixture usava id_manutencao/data_manutencao, que nao existem no
    export do ERP - os testes passavam contra um schema imaginario enquanto o
    pipeline real quebrava com KeyError.
    """
    return pd.DataFrame(
        {
            "data_servico": ["01/01/2026", "01/02/2026", "01/03/2026"],
            "placa": ["PR0001", "PR0002", "PR0003"],
            "tipo_servico": ["Freios", "Pneus", "Suspensão"],
            "regional": ["Curitiba", "Londrina", "Joinville"],
            "custo": [100.0, 200.0, 300.0],
        }
    )


def test_dataframe_vazio_estoura_erro():
    with pytest.raises(FalhaQualidadeDados):
        checar_nao_vazio(pd.DataFrame())


def test_chave_nula_estoura_erro():
    df = df_base()
    df.loc[0, "placa"] = None
    with pytest.raises(FalhaQualidadeDados):
        checar_chave_nao_nula(df, "placa")


def test_chave_duplicada_estoura_erro():
    df = pd.concat([df_base(), df_base().iloc[[0]]], ignore_index=True)
    with pytest.raises(FalhaQualidadeDados):
        checar_chave_unica(df, "placa")


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
