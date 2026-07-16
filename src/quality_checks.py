"""
Porta 1 - validacao na ENTRADA.

A ideia aqui e pegar problema que veio da origem, antes de eu processar
qualquer coisa. Se essas checagens falharem, o problema nao e meu codigo,
e o dado que chegou.

Usei "if + raise" em vez de assert de proposito. assert some quando o
Python roda em modo otimizado (-O), entao pra qualquer coisa que eu queira
que rode sempre, raise e o jeito certo.
"""

import pandas as pd


class FalhaQualidadeDados(Exception):
    """Erro proprio pra falha de qualidade, fica mais facil de filtrar no log depois."""


def checar_nao_vazio(df: pd.DataFrame) -> None:
    if len(df) == 0:
        raise FalhaQualidadeDados(
            "[completude] DataFrame veio vazio - a extracao trouxe 0 linhas."
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


def checar_valor_nao_negativo(df: pd.DataFrame, coluna: str) -> None:
    qtd_neg = (df[coluna] < 0).sum()
    if qtd_neg > 0:
        raise FalhaQualidadeDados(
            f"[validade] {qtd_neg} registro(s) com '{coluna}' negativo."
        )


def checar_data_nao_futura(df: pd.DataFrame, coluna: str) -> None:
    hoje = pd.Timestamp.now().normalize()
    datas = pd.to_datetime(df[coluna], errors="coerce")
    qtd_futuro = (datas > hoje).sum()
    if qtd_futuro > 0:
        raise FalhaQualidadeDados(
            f"[validade] {qtd_futuro} registro(s) com '{coluna}' no futuro - "
            "provavel bug de parsing."
        )


def validar_entrada(df: pd.DataFrame) -> dict:
    """
    Roda a bateria de checagens da Porta 1 na ordem certa (escada de
    pressupostos: existencia primeiro, depois forma do dado).

    Se passar em tudo, devolve um resumo. Se falhar em qualquer coisa,
    para na primeira falha e estoura FalhaQualidadeDados com a mensagem
    especifica.
    """
    checar_nao_vazio(df)
    checar_chave_nao_nula(df, "id_manutencao")
    checar_chave_unica(df, "id_manutencao")
    checar_valor_nao_negativo(df, "custo")
    checar_data_nao_futura(df, "data_manutencao")

    return {
        "status": "ok",
        "linhas_validadas": len(df),
    }
