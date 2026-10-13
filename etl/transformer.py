"""Limpeza, padronização e cálculos das taxas de juros DI x Pré.
"""
import pandas as pd
import numpy as np


# Mapeamento padrão de vértices/prazos em dias úteis (252 d.u./ano)
VERTICES_DIAS_UTEIS = {
    "1M": 21,
    "3M": 63,
    "6M": 126,
    "1A": 252,
    "2A": 504,
    "3A": 756,
    "5A": 1260,
    "10A": 2520,
}


def limpar_dados(df_bruto: pd.DataFrame) -> pd.DataFrame:
    """Padroniza tipos de dados e limpa valores nulos e strings.
    """
    df = df_bruto.copy()

    # Converter datas
    df["data_referencia"] = pd.to_datetime(df["data_referencia"])

    # Limpar e converter numéricos
    df["taxa"] = (
        df["taxa"]
        .astype(str)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )

    df["dias_uteis"] = pd.to_numeric(df["dias_uteis"], errors="coerce")
    df["dias_corridos"] = pd.to_numeric(df["dias_corridos"], errors="coerce")

    # Filtrar valores consistentes
    df = df.dropna(subset=["data_referencia", "dias_uteis", "taxa"])
    df["dias_uteis"] = df["dias_uteis"].astype(int)
    df["dias_corridos"] = df["dias_corridos"].astype(int)

    # Ordenar
    df = df.sort_values(by=["data_referencia", "dias_uteis"]).reset_index(drop=True)
    return df


def interpolar_flat_forward_252(du_alvo: int | float, x_du: np.ndarray, y_taxas: np.ndarray) -> float:
    """Calcula a taxa interpolada para um número de dias úteis `du_alvo`
    utilizando a metodologia Flat-Forward da B3 com base de 252 dias úteis.

    Fórmula da B3:
      Fator acumulado até o vértice k:
        F_k = (1 + r_k / 100) ** (DU_k / 252)
      Taxa a termo constante entre DU_1 e DU_2:
        (1 + r_termo) = (F_2 / F_1) ** (1 / ((DU_2 - DU_1) / 252))
      Fator acumulado no prazo alvo DU:
        F_alvo = F_1 * (1 + r_termo) ** ((DU - DU_1) / 252)
               = F_1 * (F_2 / F_1) ** ((DU - DU_1) / (DU_2 - DU_1))
      Taxa anualizada interpolada:
        r_alvo = ((F_alvo) ** (252 / DU) - 1) * 100
    """
    if du_alvo < x_du.min() or du_alvo > x_du.max():
        return np.nan

    # Ponto exato
    if du_alvo in x_du:
        idx = np.where(x_du == du_alvo)[0][0]
        return float(y_taxas[idx])

    # Encontrar os vértices anterior (du1) e posterior (du2)
    idx_post = np.searchsorted(x_du, du_alvo)
    idx_ant = idx_post - 1

    du1, du2 = x_du[idx_ant], x_du[idx_post]
    r1, r2 = y_taxas[idx_ant] / 100.0, y_taxas[idx_post] / 100.0

    # Fatores de capitalização compostos (base 252)
    fator1 = (1.0 + r1) ** (du1 / 252.0)
    fator2 = (1.0 + r2) ** (du2 / 252.0)

    # Interpolação do fator via taxa forward constante no período
    razao = (du_alvo - du1) / (du2 - du1)
    fator_alvo = fator1 * ((fator2 / fator1) ** razao)

    # Taxa composta anualizada da B3
    r_alvo = (fator_alvo ** (252.0 / du_alvo) - 1.0) * 100.0
    return float(r_alvo)


def interpolar_vertices_curva(df_dia: pd.DataFrame, vertices: dict[str, int] = VERTICES_DIAS_UTEIS) -> pd.DataFrame:
    """Interpola a curva de juros para vértices fixos em um dia específico
    utilizando a metodologia Flat-Forward 252 da B3.
    """
    df_sorted = df_dia.sort_values("dias_uteis")
    x = df_sorted["dias_uteis"].to_numpy(dtype=float)
    y = df_sorted["taxa"].to_numpy(dtype=float)

    registros = []
    data_ref = df_dia["data_referencia"].iloc[0]

    for label_vertice, du_alvo in vertices.items():
        taxa_interp = interpolar_flat_forward_252(du_alvo, x, y)

        registros.append({
            "data_referencia": data_ref,
            "vertice": label_vertice,
            "dias_uteis": du_alvo,
            "taxa": taxa_interp,
        })

    return pd.DataFrame(registros)


def gerar_curva_vertices_historica(df_limpo: pd.DataFrame, vertices: dict[str, int] = VERTICES_DIAS_UTEIS) -> pd.DataFrame:
    """Gera o histórico com todos os dias interpolados nos vértices de interesse.
    """
    dfs = []
    for _, grupo in df_limpo.groupby("data_referencia"):
        dfs.append(interpolar_vertices_curva(grupo, vertices))
    
    df_vertices = pd.concat(dfs, ignore_index=True)
    df_vertices = df_vertices.sort_values(by=["data_referencia", "dias_uteis"]).reset_index(drop=True)
    return df_vertices


def calcular_inclinacao_curva(df_vertices: pd.DataFrame, vertice_longo: str = "5A", vertice_curto: str = "1M") -> pd.DataFrame:
    """Calcula a inclinação (spread em pontos-base ou pontos percentuais) entre dois vértices ao longo do tempo.
    Spread = Taxa(Longo) - Taxa(Curto). Em bps (pontos-base) = (Taxa(Longo) - Taxa(Curto)) * 100.
    """
    piv = df_vertices.pivot(index="data_referencia", columns="vertice", values="taxa")
    if vertice_longo not in piv.columns or vertice_curto not in piv.columns:
        raise ValueError(f"Vértices {vertice_longo} e/ou {vertice_curto} não encontrados.")

    df_inc = pd.DataFrame(index=piv.index)
    df_inc["taxa_curto"] = piv[vertice_curto]
    df_inc["taxa_longo"] = piv[vertice_longo]
    df_inc["spread_pp"] = df_inc["taxa_longo"] - df_inc["taxa_curto"]
    df_inc["spread_bps"] = df_inc["spread_pp"] * 100
    df_inc = df_inc.reset_index()
    return df_inc


def calcular_variacoes_diarias(df_vertices: pd.DataFrame) -> pd.DataFrame:
    """Calcula a variação diária (em bps) de cada vértice para uso em mapas de calor.
    """
    piv = df_vertices.pivot(index="data_referencia", columns="vertice", values="taxa")
    # Variação diária em bps (diferença da taxa * 100)
    diff_bps = piv.diff() * 100
    return diff_bps
