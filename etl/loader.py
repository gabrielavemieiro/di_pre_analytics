"""Exportação e persistência dos dados tratados para data/processed/.
"""
from pathlib import Path
import pandas as pd
from etl.extractor import carregar_todos_csvs_brutos
from etl.transformer import (
    limpar_dados,
    gerar_curva_vertices_historica,
    calcular_inclinacao_curva,
)


def exportar_dados_processados(
    diretorio_raw: Path | str = "data/raw",
    diretorio_processed: Path | str = "data/processed",
) -> dict[str, Path]:
    """Executa o pipeline completo de ETL e salva os arquivos prontos em data/processed.
    """
    caminho_raw = Path(diretorio_raw)
    caminho_proc = Path(diretorio_processed)
    caminho_proc.mkdir(parents=True, exist_ok=True)

    print("-> 1. Extraindo dados brutos...")
    df_bruto = carregar_todos_csvs_brutos(caminho_raw)

    print("-> 2. Limpando e padronizando dados...")
    df_limpo = limpar_dados(df_bruto)

    print("-> 3. Calculando vértices padronizados...")
    df_vertices = gerar_curva_vertices_historica(df_limpo)

    print("-> 4. Calculando inclinação da curva (5A - 1M)...")
    df_inclinacao = calcular_inclinacao_curva(df_vertices, vertice_longo="5A", vertice_curto="1M")

    # Salvando em formatos otimizados (CSV e Parquet)
    caminho_curvas = caminho_proc / "curvas_completas.csv"
    caminho_curvas_parquet = caminho_proc / "curvas_completas.parquet"
    caminho_vert = caminho_proc / "vertices_historico.csv"
    caminho_vert_parquet = caminho_proc / "vertices_historico.parquet"
    caminho_inc = caminho_proc / "inclinacao_curva.csv"
    caminho_inc_parquet = caminho_proc / "inclinacao_curva.parquet"

    df_limpo.to_csv(caminho_curvas, index=False, sep=";", decimal=",")
    df_vertices.to_csv(caminho_vert, index=False, sep=";", decimal=",")
    df_inclinacao.to_csv(caminho_inc, index=False, sep=";", decimal=",")

    try:
        df_limpo.to_parquet(caminho_curvas_parquet, index=False)
        df_vertices.to_parquet(caminho_vert_parquet, index=False)
        df_inclinacao.to_parquet(caminho_inc_parquet, index=False)
    except Exception as e:
        print(f"Aviso: Não foi possível salvar em Parquet ({e}). Mantidos arquivos CSV.")

    print(f"Sucesso! Arquivos processados salvos em {caminho_proc}")
    return {
        "curvas_completas": caminho_curvas,
        "vertices_historico": caminho_vert,
        "inclinacao_curva": caminho_inc,
    }


if __name__ == "__main__":
    exportar_dados_processados()
