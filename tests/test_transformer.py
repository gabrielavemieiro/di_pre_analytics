"""Testes de validação dos cálculos do módulo de transformação (ETL).
"""
import pandas as pd
import numpy as np
import pytest
from etl.transformer import (
    limpar_dados,
    interpolar_vertices_curva,
    gerar_curva_vertices_historica,
    calcular_inclinacao_curva,
    calcular_variacoes_diarias,
)


@pytest.fixture
def dados_brutos_mock():
    return pd.DataFrame({
        "descricao": ["DI x pré", "DI x pré", "DI x pré", "DI x pré", "DI x pré", "DI x pré"],
        "dias_uteis": ["1", "21", "252", "1", "21", "252"],
        "dias_corridos": ["1", "30", "365", "1", "30", "365"],
        "taxa": ["13,50", "13,60", "14,00", "13,55", "13,70", "14,10"],
        "data_referencia": ["2026-09-02", "2026-09-02", "2026-09-02", "2026-09-03", "2026-09-03", "2026-09-03"],
        "arquivo_origem": ["arq1.csv"] * 3 + ["arq2.csv"] * 3,
    })


def test_limpar_dados(dados_brutos_mock):
    df_limpo = limpar_dados(dados_brutos_mock)
    
    assert pd.api.types.is_datetime64_any_dtype(df_limpo["data_referencia"])
    assert pd.api.types.is_float_dtype(df_limpo["taxa"])
    assert pd.api.types.is_integer_dtype(df_limpo["dias_uteis"])
    assert len(df_limpo) == 6
    assert df_limpo["taxa"].iloc[0] == 13.50


def test_interpolar_vertices_curva(dados_brutos_mock):
    df_limpo = limpar_dados(dados_brutos_mock)
    df_dia1 = df_limpo[df_limpo["data_referencia"] == "2026-09-02"]
    
    vertices_teste = {"1M": 21, "6M": 126, "1A": 252}
    df_interp = interpolar_vertices_curva(df_dia1, vertices=vertices_teste)

    assert len(df_interp) == 3
    taxa_1m = df_interp[df_interp["vertice"] == "1M"]["taxa"].iloc[0]
    taxa_6m = df_interp[df_interp["vertice"] == "6M"]["taxa"].iloc[0]
    taxa_1a = df_interp[df_interp["vertice"] == "1A"]["taxa"].iloc[0]

    # Vértices exatos
    assert pytest.approx(taxa_1m, 0.001) == 13.60
    assert pytest.approx(taxa_1a, 0.001) == 14.00

    # Interpolação intermediária Flat Forward 252 entre 21 DU (13.60%) e 252 DU (14.00%) em 126 DU:
    f1 = (1 + 0.1360) ** (21 / 252)
    f2 = (1 + 0.1400) ** (252 / 252)
    razao = (126 - 21) / (252 - 21)
    f_esperado = f1 * ((f2 / f1) ** razao)
    r_esperado = ((f_esperado ** (252 / 126)) - 1) * 100
    assert pytest.approx(taxa_6m, 0.0001) == r_esperado


def test_calcular_inclinacao_curva(dados_brutos_mock):
    df_limpo = limpar_dados(dados_brutos_mock)
    vertices_teste = {"1M": 21, "1A": 252}
    df_vert = gerar_curva_vertices_historica(df_limpo, vertices=vertices_teste)
    
    df_inc = calcular_inclinacao_curva(df_vert, vertice_longo="1A", vertice_curto="1M")

    assert len(df_inc) == 2
    # Dia 1: 14.00 - 13.60 = 0.40 pp = 40 bps
    assert pytest.approx(df_inc["spread_pp"].iloc[0], 0.001) == 0.40
    assert pytest.approx(df_inc["spread_bps"].iloc[0], 0.001) == 40.0
