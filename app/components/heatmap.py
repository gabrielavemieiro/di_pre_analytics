"""Componente: Mapa de Calor (Heatmap) de Variações Diárias em Pontos-Base.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from etl.transformer import calcular_variacoes_diarias


def renderizar_heatmap(df_vertices: pd.DataFrame):
    """Renderiza um mapa de calor das variações diárias (bps) ao longo dos vértices.
    """
    st.subheader("Mapa de Calor de Variações Diárias (bps)")

    variacoes = calcular_variacoes_diarias(df_vertices)
    # Remove primeira linha com NaN decorrente do diff
    variacoes = variacoes.dropna(how="all")

    if variacoes.empty:
        st.info("Dados insuficientes para cálculo do mapa de calor.")
        return

    # 1. Ordenação estrita dos vértices do menor para o maior prazo (DU)
    ordem_padrao = ["1M", "3M", "6M", "1A", "2A", "3A", "5A", "10A"]
    colunas_ordenadas = [v for v in ordem_padrao if v in variacoes.columns]
    # Caso haja vértices adicionais não contemplados na lista padrão:
    outros_vertices = [v for v in variacoes.columns if v not in colunas_ordenadas]
    colunas_finais = colunas_ordenadas + outros_vertices
    variacoes = variacoes[colunas_finais]

    # Lista de datas disponíveis para seleção
    datas_disponiveis = sorted(variacoes.index.strftime("%Y-%m-%d").unique())
    if len(datas_disponiveis) < 1:
        st.warning("Não há datas suficientes para exibição do mapa de calor.")
        return

    # Controles de seleção de intervalo de datas da amostra
    c1, c2 = st.columns(2)
    with c1:
        data_ini_str = st.selectbox(
            "Data Inicial",
            options=datas_disponiveis,
            index=0,
            key="heatmap_data_ini"
        )
    with c2:
        data_fim_str = st.selectbox(
            "Data Final",
            options=datas_disponiveis,
            index=len(datas_disponiveis) - 1,
            key="heatmap_data_fim"
        )

    # Validar ordem cronológica das datas selecionadas
    dt_inicio = pd.to_datetime(data_ini_str)
    dt_fim = pd.to_datetime(data_fim_str)

    if dt_inicio > dt_fim:
        st.error("A Data Inicial não pode ser posterior à Data Final. Por favor, ajuste o intervalo.")
        return

    # Filtrar amostra de variações pelo intervalo selecionado
    variacoes_filtradas = variacoes.loc[(variacoes.index >= dt_inicio) & (variacoes.index <= dt_fim)]

    if variacoes_filtradas.empty:
        st.warning("Nenhum dado encontrado para o intervalo de datas selecionado.")
        return

    data_inicio_formatada = dt_inicio.strftime("%d/%m/%Y")
    data_fim_formatada = dt_fim.strftime("%d/%m/%Y")
    total_pregoes = len(variacoes_filtradas)

    # Subtítulo discreto com intervalo e explicação da métrica
    st.markdown(
        f"<div style='font-size: 0.875rem; color: #475569; margin-top: -6px; margin-bottom: 12px; line-height: 1.4;'>"
        f"<b>Intervalo da amostra:</b> {data_inicio_formatada} a {data_fim_formatada} ({total_pregoes} pregões selecionados).<br>"
        f"<span style='color: #64748b;'>Cada célula representa a diferença (em pontos-base, bps) entre a taxa do vértice na data de negociação e a taxa no pregão imediatamente anterior (D - D-1).</span>"
        f"</div>",
        unsafe_allow_html=True
    )

    datas_formatadas = [d.strftime("%d/%m/%Y") for d in variacoes_filtradas.index]
    colunas_vertices = list(variacoes_filtradas.columns)
    valores_z = variacoes_filtradas.values

    # Convenção: Vermelho para alta (+bps) e Azul para queda (-bps)
    fig = go.Figure(
        data=go.Heatmap(
            z=valores_z,
            x=colunas_vertices,
            y=datas_formatadas,
            colorscale=[
                [0.0, "#0055A5"],   # Azul para queda / fechamento
                [0.5, "#f8fafc"],   # Neutro / próximo de zero
                [1.0, "#dc2626"],   # Vermelho para alta / abertura
            ],
            zmid=0,
            colorbar=dict(title="Var (bps)"),
            hovertemplate="Data: %{y}<br>Vértice: %{x}<br>Variação diária: %{z:+.1f} bps<extra></extra>",
        )
    )

    titulo_grafico = f"Variação Diária da Taxa por Vértice (bps) — {data_inicio_formatada} a {data_fim_formatada}"

    fig.update_layout(
        title=titulo_grafico,
        xaxis_title="Vértice da Curva (Prazo Crescente)",
        yaxis_title="Data de Negociação",
        template="plotly_white",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=40, r=40, t=60, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)
