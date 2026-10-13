"""Ponto de entrada da aplicação Streamlit (DI x Pré Analytics).
"""
import sys
from pathlib import Path
import streamlit as st
import pandas as pd

# Adiciona o diretório raiz ao sys.path para garantir importação dos módulos locais
PASTA_RAIZ = Path(__file__).resolve().parent.parent
if str(PASTA_RAIZ) not in sys.path:
    sys.path.insert(0, str(PASTA_RAIZ))

from etl.loader import exportar_dados_processados
from app.components.curvas import renderizar_curvas
from app.components.evolucao import renderizar_evolucao
from app.components.heatmap import renderizar_heatmap
from app.components.inclinacao import renderizar_inclinacao


st.set_page_config(
    page_title="DI x Pré Analytics | Análise de Curva B3",
    page_icon="📈",
    layout="wide",
)


@st.cache_data(show_spinner="Carregando dados processados da B3...")
def carregar_dados():
    pasta_proc = PASTA_RAIZ / "data" / "processed"
    arq_curvas = pasta_proc / "curvas_completas.parquet"
    arq_vertices = pasta_proc / "vertices_historico.parquet"
    arq_inclinacao = pasta_proc / "inclinacao_curva.parquet"

    # Se ainda não existirem os processados, roda o pipeline de ETL
    if not (arq_curvas.exists() and arq_vertices.exists() and arq_inclinacao.exists()):
        exportar_dados_processados(PASTA_RAIZ / "data" / "raw", pasta_proc)

    # Carrega dados
    if arq_curvas.exists():
        df_curvas = pd.read_parquet(arq_curvas)
    else:
        df_curvas = pd.read_csv(pasta_proc / "curvas_completas.csv", sep=";", decimal=",")

    if arq_vertices.exists():
        df_vertices = pd.read_parquet(arq_vertices)
    else:
        df_vertices = pd.read_csv(pasta_proc / "vertices_historico.csv", sep=";", decimal=",")

    if arq_inclinacao.exists():
        df_inclinacao = pd.read_parquet(arq_inclinacao)
    else:
        df_inclinacao = pd.read_csv(pasta_proc / "inclinacao_curva.csv", sep=";", decimal=",")

    df_curvas["data_referencia"] = pd.to_datetime(df_curvas["data_referencia"])
    df_vertices["data_referencia"] = pd.to_datetime(df_vertices["data_referencia"])
    df_inclinacao["data_referencia"] = pd.to_datetime(df_inclinacao["data_referencia"])

    return df_curvas, df_vertices, df_inclinacao


def main():
    st.title("📈 DI x Pré Analytics")
    st.caption("Monitoramento e análise quantitativa da estrutura a termo da taxa de juros (B3)")

    try:
        df_curvas, df_vertices, df_inclinacao = carregar_dados()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return

    # Barra lateral
    with st.sidebar:
        st.header("⚙️ Configurações & Ações")
        st.markdown(
            f"""
            - **Período:** {df_curvas['data_referencia'].min().strftime('%d/%m/%Y')} a {df_curvas['data_referencia'].max().strftime('%d/%m/%Y')}
            - **Pregões analisados:** {df_curvas['data_referencia'].nunique()}
            - **Total de registros:** {len(df_curvas):,}
            """
        )
        if st.button("🔄 Reprocessar Dados (ETL)", use_container_width=True):
            st.cache_data.clear()
            exportar_dados_processados(PASTA_RAIZ / "data" / "raw", PASTA_RAIZ / "data" / "processed")
            st.success("ETL executado com sucesso! Atualizando...")
            st.rerun()

        st.markdown("---")
        st.markdown(
            """
            **ℹ️ Informações Metodológicas:**
            - **Fonte:** Taxas Referenciais BM&FBOVESPA (B3)
            - **Curva:** DI x Pré
            - **Interpolação:** Metodologia Flat-Forward 252
            """
        )

    # Abas principais
    aba1, aba2, aba3, aba4 = st.tabs([
        "📊 Curvas (Início x Fim)",
        "⏳ Evolução por Prazo",
        "📐 Inclinação",
        "🔥 Mapa de Calor (Heatmap)",
    ])

    with aba1:
        renderizar_curvas(df_curvas, df_vertices)

    with aba2:
        renderizar_evolucao(df_vertices)

    with aba3:
        renderizar_inclinacao(df_inclinacao, df_vertices)

    with aba4:
        renderizar_heatmap(df_vertices)


if __name__ == "__main__":
    main()
