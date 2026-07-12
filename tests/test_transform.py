import pandas as pd
import pytest

from src.transform import agregar_por_tipo_regional, limpar_dados


@pytest.fixture
def df_bruto():
    return pd.DataFrame(
        {
            "placa": ["PR0001", "PR0001", "PR0002", "PR0002"],
            "tipo_servico": ["Freios", "Freios", "Pneus", "Pneus"],
            "regional": ["Curitiba", "Curitiba", "Londrina", "Londrina"],
            "custo": [500.0, 300.0, -50.0, 200.0],
        }
    )


def test_limpar_dados_remove_custo_negativo(df_bruto):
    resultado = limpar_dados(df_bruto)
    assert len(resultado) == 3
    assert (resultado["custo"] > 0).all()


def test_agregar_por_tipo_regional_soma_correta(df_bruto):
    df_limpo = limpar_dados(df_bruto)
    agregado = agregar_por_tipo_regional(df_limpo)

    linha_freios = agregado[agregado["tipo_servico"] == "Freios"].iloc[0]
    assert linha_freios["custo_total"] == 800.0
    assert linha_freios["qtd_servicos"] == 2
