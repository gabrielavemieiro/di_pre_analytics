"""Utilitários de formatação de datas, taxas e tooltips em português-BR.
"""
from datetime import datetime
import pandas as pd


def formatar_taxa(valor: float | int | None, casas_decimais: int = 2) -> str:
    """Formata uma taxa percentual com vírgula decimal (ex.: 13,75%).
    """
    if valor is None or pd.isna(valor):
        return "-"
    return f"{valor:.{casas_decimais}f}%".replace(".", ",")


def formatar_bps(valor: float | int | None, casas_decimais: int = 1) -> str:
    """Formata valores em pontos-base (bps) (ex.: +12,5 bps ou -5,0 bps).
    """
    if valor is None or pd.isna(valor):
        return "-"
    sinal = "+" if valor > 0 else ""
    return f"{sinal}{valor:.{casas_decimais}f} bps".replace(".", ",")


def formatar_data(data_obj: str | datetime | pd.Timestamp, formato: str = "%d/%m/%Y") -> str:
    """Formata datas para exibição em português (dd/mm/aaaa).
    """
    if pd.isna(data_obj):
        return "-"
    ts = pd.to_datetime(data_obj)
    return ts.strftime(formato)
