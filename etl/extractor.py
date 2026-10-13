"""Leitura e parsing dos arquivos CSV brutos da B3.
"""
from pathlib import Path
import re
import pandas as pd


def extrair_data_do_nome(caminho_arquivo: Path | str) -> str:
    """Extrai a data no formato YYYY-MM-DD a partir do nome do arquivo (ex.: TaxaReferencia_PRE_20260902.csv).
    """
    nome = Path(caminho_arquivo).name
    match = re.search(r"(\d{4})(\d{2})(\d{2})", nome)
    if not match:
        raise ValueError(f"Não foi possível extrair a data do arquivo: {nome}")
    ano, mes, dia = match.groups()
    return f"{ano}-{mes}-{dia}"


def ler_csv_b3(caminho_arquivo: Path | str) -> pd.DataFrame:
    """Lê um arquivo CSV de Taxa de Referência Pré da B3.
    """
    caminho = Path(caminho_arquivo)
    
    # Tenta ler com diferentes encodings usuais para arquivos legados e UTF-8
    df = None
    for encoding in ["latin1", "cp1252", "utf-8", "iso-8859-1"]:
        try:
            df = pd.read_csv(
                caminho,
                sep=";",
                decimal=",",
                encoding=encoding,
                dtype=str
            )
            break
        except Exception:
            continue
            
    if df is None:
        raise ValueError(f"Falha ao ler o arquivo {caminho}")

    # Renomear colunas para padrão limpo
    colunas_map = {}
    for col in df.columns:
        col_norm = col.lower().strip()
        if "descri" in col_norm:
            colunas_map[col] = "descricao"
        elif "úteis" in col_norm or "uteis" in col_norm:
            colunas_map[col] = "dias_uteis"
        elif "corridos" in col_norm:
            colunas_map[col] = "dias_corridos"
        elif "taxa" in col_norm or "preço" in col_norm or "preco" in col_norm:
            colunas_map[col] = "taxa"

    df = df.rename(columns=colunas_map)
    data_referencia = extrair_data_do_nome(caminho)
    df["data_referencia"] = data_referencia
    df["arquivo_origem"] = caminho.name

    return df


def carregar_todos_csvs_brutos(diretorio_raw: Path | str = "data/raw") -> pd.DataFrame:
    """Lê todos os CSVs da pasta raw e concatena em um único DataFrame bruto.
    """
    caminho_dir = Path(diretorio_raw)
    arquivos_csv = sorted(caminho_dir.glob("*.csv"))
    
    if not arquivos_csv:
        raise FileNotFoundError(f"Nenhum arquivo CSV encontrado em {caminho_dir}")

    dfs = [ler_csv_b3(arq) for arq in arquivos_csv]
    return pd.concat(dfs, ignore_index=True)
