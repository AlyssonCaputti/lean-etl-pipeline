"""
As duas portas de qualidade do pipeline.

Porta 1 (validar_entrada) roda no dado que acabou de chegar da origem. Se
falhar aqui, o problema nao e meu codigo - e o dado que chegou.

Porta 2 (validar_saida) roda no agregado, antes de gravar. Se falhar aqui,
o problema E meu codigo: a origem passou na Porta 1, entao alguma coisa
entre uma porta e outra estragou o numero.

Separar as duas importa por causa do diagnostico: erro na Porta 1 eu cobro
da origem, erro na Porta 2 eu depuro no transform.

Usei "if + raise" em vez de assert de proposito. assert some quando o
Python roda em modo otimizado (-O), entao pra qualquer coisa que eu queira
que rode sempre, raise e o jeito certo.
"""

import pandas as pd


class FalhaQualidadeDados(Exception):
    """Erro proprio pra falha de qualidade, fica mais facil de filtrar no log depois."""


# --------------------------------------------------------------------------
# checagens individuais - servem pras duas portas
# --------------------------------------------------------------------------

def checar_nao_vazio(df: pd.DataFrame) -> None:
    if len(df) == 0:
        raise FalhaQualidadeDados(
            "[completude] DataFrame veio vazio - a extracao trouxe 0 linhas."
        )


def checar_colunas_esperadas(df: pd.DataFrame, colunas: list[str]) -> None:
    """Confere o layout antes de tocar em qualquer coluna.

    Sem isso, coluna renomeada na origem vira KeyError no meio da validacao -
    traceback ruim de ler, e que nao diz que o problema foi layout.
    """
    faltando = [c for c in colunas if c not in df.columns]
    if faltando:
        raise FalhaQualidadeDados(
            f"[layout] faltam colunas: {faltando}. "
            f"Vieram estas: {list(df.columns)}."
        )


def checar_chave_nao_nula(df: pd.DataFrame, coluna: str) -> None:
    qtd_nulos = df[coluna].isnull().sum()
    if qtd_nulos > 0:
        raise FalhaQualidadeDados(
            f"[completude] {qtd_nulos} registro(s) com '{coluna}' nulo."
        )


def checar_chave_unica(df: pd.DataFrame, coluna: str) -> None:
    qtd_dup = df[coluna].duplicated().sum()
    if qtd_dup > 0:
        raise FalhaQualidadeDados(
            f"[unicidade] {qtd_dup} registro(s) duplicado(s) na coluna '{coluna}'."
        )


def checar_combinacao_unica(df: pd.DataFrame, colunas: list[str]) -> None:
    """Unicidade de chave composta - e assim que eu declaro o grao da tabela.

    No agregado, tipo_servico + regional aparece uma vez so. Se aparecer
    duas, o groupby nao agrupou o que eu pensei que agrupava.
    """
    qtd_dup = df.duplicated(subset=colunas).sum()
    if qtd_dup > 0:
        raise FalhaQualidadeDados(
            f"[unicidade] {qtd_dup} linha(s) repetida(s) em {colunas} - "
            f"o grao da tabela nao e o que eu declarei."
        )


def checar_valor_nao_negativo(df: pd.DataFrame, coluna: str) -> None:
    qtd_neg = (df[coluna] < 0).sum()
    if qtd_neg > 0:
        raise FalhaQualidadeDados(
            f"[validade] {qtd_neg} registro(s) com '{coluna}' negativo."
        )


def checar_data_nao_futura(df: pd.DataFrame, coluna: str) -> None:
    hoje = pd.Timestamp.now().normalize()
    datas = pd.to_datetime(df[coluna], errors="coerce", dayfirst=True)
    qtd_futuro = (datas > hoje).sum()
    if qtd_futuro > 0:
        raise FalhaQualidadeDados(
            f"[validade] {qtd_futuro} registro(s) com '{coluna}' no futuro - "
            "provavel bug de parsing."
        )


def checar_soma_preservada(
    df_origem: pd.DataFrame,
    df_agregado: pd.DataFrame,
    coluna_origem: str,
    coluna_agregada: str,
    tolerancia: float = 0.01,
) -> None:
    """Confere se a soma sobreviveu a agregacao.

    E o unico check que pega groupby com chave errada, join que multiplicou
    linha ou filtro que comeu dado sem avisar. Total antes e total depois tem
    que fechar - quando nao fecha, o numero que vai pro dashboard esta errado
    e continua parecendo plausivel, que e o pior tipo de erro.

    A tolerancia e pra arredondamento de float, nao pra perdoar diferenca de
    verdade: 1 centavo no total inteiro.
    """
    total_antes = float(df_origem[coluna_origem].sum())
    total_depois = float(df_agregado[coluna_agregada].sum())
    diferenca = abs(total_antes - total_depois)

    if diferenca > tolerancia:
        raise FalhaQualidadeDados(
            f"[reconciliacao] a soma nao fechou: origem={total_antes:.2f}, "
            f"agregado={total_depois:.2f}, diferenca={diferenca:.2f}. "
            f"Alguma coisa entre a Porta 1 e a Porta 2 comeu ou duplicou dado."
        )


# --------------------------------------------------------------------------
# as duas portas
# --------------------------------------------------------------------------

COLUNAS_ENTRADA = ["data_servico", "placa", "tipo_servico", "regional", "custo"]
COLUNAS_SAIDA = ["tipo_servico", "regional", "custo_total", "qtd_servicos", "custo_medio"]


def validar_entrada(df: pd.DataFrame) -> dict:
    """
    Porta 1 - o dado como veio da origem.

    Ordem proposital (escada de pressupostos): existencia antes de forma. Nao
    faz sentido checar nulo numa coluna que nem veio no arquivo, nem checar
    valor numa tabela vazia.

    Nao checo unicidade aqui porque a origem nao tem chave unica: a mesma
    placa faz varias manutencoes, e duas podem cair no mesmo dia. Unicidade
    e assunto do agregado - ver validar_saida.
    """
    checar_nao_vazio(df)
    checar_colunas_esperadas(df, COLUNAS_ENTRADA)
    checar_chave_nao_nula(df, "placa")
    checar_chave_nao_nula(df, "custo")
    checar_valor_nao_negativo(df, "custo")
    checar_data_nao_futura(df, "data_servico")

    return {
        "status": "ok",
        "linhas_validadas": len(df),
    }


def validar_saida(df: pd.DataFrame, df_origem: pd.DataFrame | None = None) -> dict:
    """
    Porta 2 - o agregado, imediatamente antes de gravar.

    Se df_origem vier, tambem reconcilia a soma. Vale passar sempre: e o
    unico check que pega erro de agregacao, que e o erro que passa batido
    justamente porque o resultado continua parecendo um numero razoavel.
    """
    checar_nao_vazio(df)
    checar_colunas_esperadas(df, COLUNAS_SAIDA)
    checar_combinacao_unica(df, ["tipo_servico", "regional"])
    checar_valor_nao_negativo(df, "custo_total")
    checar_valor_nao_negativo(df, "custo_medio")

    if (df["qtd_servicos"] < 1).any():
        raise FalhaQualidadeDados(
            "[validade] grupo com qtd_servicos < 1 - agregacao gerou linha fantasma."
        )

    if df_origem is not None:
        checar_soma_preservada(df_origem, df, "custo", "custo_total")

    return {
        "status": "ok",
        "grupos_validados": len(df),
        "custo_total": round(float(df["custo_total"].sum()), 2),
    }
