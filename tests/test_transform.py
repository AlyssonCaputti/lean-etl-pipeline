import pandas as pd
import pytest

from src.transform import agregar_por_tipo_regional, carregar_dados_brutos, limpar_dados


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


def test_carregar_dados_brutos_converte_custo_com_virgula(tmp_path):
    # regressão: o CSV do SAP B1 vem com vírgula decimal (ex: "248,05").
    # sem o replace em carregar_dados_brutos, "custo" fica como string e
    # quebra qualquer comparação numérica lá na frente.
    csv_path = tmp_path / "manutencoes.csv"
    csv_path.write_text(
        "data_servico,placa,tipo_servico,regional,custo\n"
        "10/01/2025,PR0001,Freios,Curitiba,\"248,05\"\n"
    )
    df = carregar_dados_brutos(csv_path)
    assert df["custo"].dtype == float
    assert df["custo"].iloc[0] == 248.05
