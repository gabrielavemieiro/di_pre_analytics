"""Componente: Inclinação da Curva de Juros (Spread Personalizável entre Vértices).
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from etl.transformer import calcular_inclinacao_curva


def renderizar_inclinacao(df_inclinacao: pd.DataFrame, df_vertices: pd.DataFrame | None = None):
    """Renderiza a análise de spread e inclinação da curva com flexibilidade de datas e vértices.
    """
    st.subheader("Inclinação da Curva (Análise de Spreads)")

    # Se df_vertices não for passado diretamente, usa o histórico padrão ou gera
    df_base_vertices = df_vertices if df_vertices is not None else None

    if df_base_vertices is None or df_base_vertices.empty:
        st.warning("Não há dados de vértices disponíveis para cálculo de inclinação.")
        return

    # Lista de vértices disponíveis com ordenação padrão
    ordem_padrao = ["1M", "3M", "6M", "1A", "2A", "3A", "5A", "10A"]
    vertices_disp = [v for v in ordem_padrao if v in df_base_vertices["vertice"].unique()]
    if not vertices_disp:
        vertices_disp = sorted(df_base_vertices["vertice"].unique())

    nomes_vertices = {
        "1M": "Vértice de 1 mês (21 DU)",
        "3M": "Vértice de 3 meses (63 DU)",
        "6M": "Vértice de 6 meses (126 DU)",
        "1A": "Vértice de 1 ano (252 DU)",
        "2A": "Vértice de 2 anos (504 DU)",
        "3A": "Vértice de 3 anos (756 DU)",
        "5A": "Vértice de 5 anos (1260 DU)",
        "10A": "Vértice de 10 anos (2520 DU)",
    }

    # -------------------------------------------------------------
    # Controles: Seleção de Vértices e Data de Referência
    # -------------------------------------------------------------
    datas_disponiveis = sorted(df_base_vertices["data_referencia"].dt.strftime("%Y-%m-%d").unique())
    if len(datas_disponiveis) < 1:
        st.warning("Não há datas disponíveis para análise.")
        return

    c_v1, c_v2, c_d = st.columns(3)

    with c_v1:
        idx_longo = vertices_disp.index("5A") if "5A" in vertices_disp else len(vertices_disp) - 1
        vertice_longo = st.selectbox(
            "Vértice Longo",
            options=vertices_disp,
            index=idx_longo,
            key="inc_vertice_longo",
            help="Ponta longa do spread (ex.: 5A)"
        )

    with c_v2:
        idx_curto = vertices_disp.index("1M") if "1M" in vertices_disp else 0
        vertice_curto = st.selectbox(
            "Vértice Curto",
            options=vertices_disp,
            index=idx_curto,
            key="inc_vertice_curto",
            help="Ponta curta do spread (ex.: 1M)"
        )

    with c_d:
        data_ref_str = st.selectbox(
            "Data Referência",
            options=datas_disponiveis,
            index=len(datas_disponiveis) - 1,
            key="inclinacao_data_ref",
            help="Data pontual para apuração das taxas e do spread"
        )

    if vertice_longo == vertice_curto:
        st.error("Selecione dois vértices distintos para calcular o spread de inclinação.")
        return

    # Calcular o spread dinâmico para todo o histórico
    try:
        df_spread = calcular_inclinacao_curva(
            df_base_vertices,
            vertice_longo=vertice_longo,
            vertice_curto=vertice_curto
        )
    except Exception as e:
        st.error(f"Erro ao calcular inclinação entre {vertice_longo} e {vertice_curto}: {e}")
        return

    # Obter dados pontuais da Data Referência selecionada
    df_spread["data_str"] = df_spread["data_referencia"].dt.strftime("%Y-%m-%d")
    row_ref = df_spread[df_spread["data_str"] == data_ref_str]

    if row_ref.empty:
        st.warning("Dados não localizados para a data de referência selecionada.")
        return

    ref_data = row_ref.iloc[0]
    taxa_curto_val = ref_data["taxa_curto"]
    taxa_longo_val = ref_data["taxa_longo"]
    spread_ref_bps = ref_data["spread_bps"]
    data_formatada = pd.to_datetime(data_ref_str).strftime("%d/%m/%Y")

    # Estilos compactos e elegantes com padding interno balanceado
    style_box = "padding: 8px 4px 6px 4px; display: flex; flex-direction: column; justify-content: center;"
    style_titulo = "font-size: 0.8125rem; color: #64748b; font-weight: 500; line-height: 1.2; margin-bottom: 3px;"
    style_valor_base = "font-size: 2.15rem; font-weight: 800; line-height: 1.1; margin: 4px 0;"
    style_subtitulo = "font-size: 0.875rem; color: #1e293b; font-weight: 600; line-height: 1.25; margin-bottom: 3px;"
    style_detalhe = "font-size: 0.75rem; color: #64748b; margin-top: 1px; line-height: 1.2;"

    # -------------------------------------------------------------
    # 3 Cards focados na Data Referência (cores neutras e padrão da tela 1)
    # -------------------------------------------------------------
    c1, c2, c3 = st.columns(3)

    # Card 1: Taxa da Ponta Curta na Data Referência
    with c1:
        with st.container(border=True):
            nome_ext_curto = nomes_vertices.get(vertice_curto, f"Vértice {vertice_curto}")
            val_curto_str = f"{taxa_curto_val:.2f}% a.a.".replace(".", ",")
            st.markdown(
                f"<div style='{style_box}'>"
                f"<div style='{style_titulo}'>Taxa Ponta Curta ({vertice_curto})</div>"
                f"<div style='{style_valor_base} color: #1e293b;'>{val_curto_str}</div>"
                f"<div style='{style_subtitulo}'>{nome_ext_curto}</div>"
                f"<div style='{style_detalhe}'>Taxa apurada em {data_formatada}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

    # Card 2: Taxa da Ponta Longa na Data Referência
    with c2:
        with st.container(border=True):
            nome_ext_longo = nomes_vertices.get(vertice_longo, f"Vértice {vertice_longo}")
            val_longo_str = f"{taxa_longo_val:.2f}% a.a.".replace(".", ",")
            st.markdown(
                f"<div style='{style_box}'>"
                f"<div style='{style_titulo}'>Taxa Ponta Longa ({vertice_longo})</div>"
                f"<div style='{style_valor_base} color: #1e293b;'>{val_longo_str}</div>"
                f"<div style='{style_subtitulo}'>{nome_ext_longo}</div>"
                f"<div style='{style_detalhe}'>Taxa apurada em {data_formatada}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

    # Card 3: Spread entre as taxas na Data Referência
    with c3:
        with st.container(border=True):
            sinal_spr = "+" if spread_ref_bps > 0 else ""
            val_spr_str = f"{sinal_spr}{spread_ref_bps:.1f} bps".replace(".", ",")
            sub_spr_str = f"Spread {vertice_longo} - {vertice_curto}"
            detalhe_spr = f"{taxa_longo_val:.2f}% - {taxa_curto_val:.2f}% em {data_formatada}".replace(".", ",")
            st.markdown(
                f"<div style='{style_box}'>"
                f"<div style='{style_titulo}'>Spread ({vertice_longo} - {vertice_curto})</div>"
                f"<div style='{style_valor_base} color: #1e293b;'>{val_spr_str}</div>"
                f"<div style='{style_subtitulo}'>{sub_spr_str}</div>"
                f"<div style='{style_detalhe}'>{detalhe_spr}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # Gráfico Histórico Completo do Spread (não filtrado pela data)
    # -------------------------------------------------------------
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_spread["data_referencia"],
            y=df_spread["spread_bps"],
            mode="lines+markers",
            name=f"Spread {vertice_longo} - {vertice_curto}",
            line=dict(color="#0055A5", width=2.5),
            marker=dict(size=5),
            hovertemplate="Data: %{x|%d/%m/%Y}<br>Spread: %{y:.1f} bps<extra></extra>",
        )
    )

    fig.add_hline(
        y=0,
        line_dash="dot",
        line_color="#94A3B8",
        annotation_text="Curva Flat (0 bps)",
        annotation_position="bottom right"
    )

    fig.update_layout(
        title=f"Histórico Completo do Spread de Inclinação ({vertice_longo} - {vertice_curto}) em bps",
        xaxis_title="Data",
        yaxis_title="Spread (bps)",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)
