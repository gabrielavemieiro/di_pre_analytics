"""Componente: Evolução Histórica das Taxas por Prazo/Vértice.
"""
import streamlit as st
import plotly.express as px
import pandas as pd


def renderizar_evolucao(df_vertices: pd.DataFrame):
    """Renderiza a série temporal da taxa de juros para vértices selecionados.
    """
    st.subheader("Evolução Histórica por Prazo (Vértices)")

    vertices_disponiveis = sorted(df_vertices["vertice"].unique())
    vertices_padrao = [v for v in ["1M", "1A", "2A", "5A"] if v in vertices_disponiveis]

    selecionados = st.multiselect(
        "Selecione os vértices de prazo para visualizar:",
        options=vertices_disponiveis,
        default=vertices_padrao or vertices_disponiveis[:4],
        key="evolucao_vertices_sel"
    )

    if not selecionados:
        st.info("Selecione pelo menos um vértice para exibir a evolução histórica.")
        return

    df_filtrado = df_vertices[df_vertices["vertice"].isin(selecionados)].copy()
    df_filtrado["data_formatada"] = df_filtrado["data_referencia"].dt.strftime("%d/%m/%Y")

    fig = px.line(
        df_filtrado,
        x="data_referencia",
        y="taxa",
        color="vertice",
        markers=True,
        title="Histórico de Taxas por Vértice (% a.a.)",
        labels={"data_referencia": "Data", "taxa": "Taxa (% a.a.)", "vertice": "Vértice"},
    )

    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig.update_traces(
        hovertemplate="<b>Vértice: %{fullData.name}</b><br>Taxa: %{y:.2f}%<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)

    # -------------------------------------------------------------
    # Seção: Variação das Taxas por Vértice entre Datas Selecionadas
    # -------------------------------------------------------------
    st.markdown("---")
    st.subheader("Variação por Vértice Padronizado no Período")

    datas_disponiveis = sorted(df_vertices["data_referencia"].dt.strftime("%Y-%m-%d").unique())
    if len(datas_disponiveis) < 2:
        st.warning("É necessário pelo menos duas datas para calcular a variação dos vértices.")
        return

    col1, col2 = st.columns(2)
    with col1:
        data_ini_str = st.selectbox(
            "Data Inicial (Referência)",
            options=datas_disponiveis,
            index=0,
            key="evolucao_data_ini"
        )
    with col2:
        data_fim_str = st.selectbox(
            "Data Final (Comparação)",
            options=datas_disponiveis,
            index=len(datas_disponiveis) - 1,
            key="evolucao_data_fim"
        )

    # Ordem e nomes oficiais dos 8 vértices padronizados
    vertices_ordem = ["1M", "3M", "6M", "1A", "2A", "3A", "5A", "10A"]
    nomes_vertices = {
        "1M": ("Vértice de 1 mês", 21),
        "3M": ("Vértice de 3 meses", 63),
        "6M": ("Vértice de 6 meses", 126),
        "1A": ("Vértice de 1 ano", 252),
        "2A": ("Vértice de 2 anos", 504),
        "3A": ("Vértice de 3 anos", 756),
        "5A": ("Vértice de 5 anos", 1260),
        "10A": ("Vértice de 10 anos", 2520),
    }

    df_ini = df_vertices[df_vertices["data_referencia"] == data_ini_str].set_index("vertice")
    df_fim = df_vertices[df_vertices["data_referencia"] == data_fim_str].set_index("vertice")

    # Estilos padronizados dos cards (harmônicos com a primeira tela)
    style_box = "padding: 8px 4px 6px 4px; display: flex; flex-direction: column; justify-content: center;"
    style_titulo = "font-size: 0.8125rem; color: #64748b; font-weight: 500; line-height: 1.2; margin-bottom: 3px;"
    style_valor_base = "font-size: 1.85rem; font-weight: 800; line-height: 1.1; margin: 4px 0;"
    style_subtitulo = "font-size: 0.875rem; color: #1e293b; font-weight: 600; line-height: 1.25; margin-bottom: 3px;"
    style_detalhe = "font-size: 0.75rem; color: #64748b; margin-top: 1px; line-height: 1.2;"

    # Exibição em duas linhas de 4 colunas (8 cards uniformes)
    linhas = [vertices_ordem[:4], vertices_ordem[4:]]

    for linha_vertices in linhas:
        cols = st.columns(4)
        for col, vert in zip(cols, linha_vertices):
            with col:
                with st.container(border=True):
                    nome_ext, du_val = nomes_vertices.get(vert, (f"Vértice {vert}", ""))
                    if vert in df_ini.index and vert in df_fim.index:
                        taxa_ini = df_ini.loc[vert, "taxa"]
                        taxa_fim = df_fim.loc[vert, "taxa"]

                        diff_bps = (taxa_fim - taxa_ini) * 100.0
                        cor_bps = "#dc2626" if diff_bps > 0 else ("#15803d" if diff_bps < 0 else "#334155")
                        sinal_bps = "+" if diff_bps > 0 else ""
                        val_str = f"{sinal_bps}{diff_bps:.1f} bps".replace(".", ",")
                        taxas_str = f"{taxa_ini:.2f}% → {taxa_fim:.2f}% a.a.".replace(".", ",")

                        st.markdown(
                            f"<div style='{style_box}'>"
                            f"<div style='{style_titulo}'>{vert} ({du_val} DU)</div>"
                            f"<div style='{style_valor_base} color: {cor_bps};'>{val_str}</div>"
                            f"<div style='{style_subtitulo}'>{nome_ext}</div>"
                            f"<div style='{style_detalhe}'>{taxas_str}</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"<div style='{style_box}'>"
                            f"<div style='{style_titulo}'>{vert} ({du_val} DU)</div>"
                            f"<div style='{style_valor_base} color: #94a3b8;'>—</div>"
                            f"<div style='{style_subtitulo}'>{nome_ext}</div>"
                            f"<div style='{style_detalhe}'>Dados não disponíveis</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
