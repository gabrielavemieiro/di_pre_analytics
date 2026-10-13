"""Componente: Comparação da Estrutura a Termo da Curva de Juros (Início x Fim).
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def renderizar_curvas(df_limpo: pd.DataFrame, df_vertices: pd.DataFrame):
    """Renderiza a visualização comparativa da curva entre a primeira e a última data selecionada.
    """
    st.subheader("Curva de Juros DI x Pré (Comparação Temporal)")

    datas_disponiveis = sorted(df_limpo["data_referencia"].dt.strftime("%Y-%m-%d").unique())
    if len(datas_disponiveis) < 2:
        st.warning("É necessário pelo menos duas datas para realizar a comparação temporal.")
        return

    col1, col2 = st.columns(2)
    with col1:
        data_ini_str = st.selectbox(
            "Data Inicial (Referência)",
            options=datas_disponiveis,
            index=0,
            key="curvas_data_ini"
        )
    with col2:
        data_fim_str = st.selectbox(
            "Data Final (Comparação)",
            options=datas_disponiveis,
            index=len(datas_disponiveis) - 1,
            key="curvas_data_fim"
        )

    # Filtrar dados para as duas datas
    df_ini = df_limpo[df_limpo["data_referencia"] == data_ini_str].sort_values("dias_uteis")
    df_fim = df_limpo[df_limpo["data_referencia"] == data_fim_str].sort_values("dias_uteis")

    # Cálculos para os 3 cards analíticos
    df_vert_ini = df_vertices[df_vertices["data_referencia"] == data_ini_str][["vertice", "dias_uteis", "taxa"]]
    df_vert_fim = df_vertices[df_vertices["data_referencia"] == data_fim_str][["vertice", "dias_uteis", "taxa"]]

    df_comp_vert = pd.merge(
        df_vert_ini,
        df_vert_fim,
        on=["vertice", "dias_uteis"],
        suffixes=("_ini", "_fim")
    ).dropna(subset=["taxa_ini", "taxa_fim"])

    if not df_comp_vert.empty:
        df_comp_vert["diff_taxa_pp"] = df_comp_vert["taxa_fim"] - df_comp_vert["taxa_ini"]
        df_comp_vert["diff_taxa_bps"] = df_comp_vert["diff_taxa_pp"] * 100.0

        media_bps = df_comp_vert["diff_taxa_bps"].mean()

        # Lógica de classificação do movimento médio da curva
        if media_bps <= -5:
            interpretacao = "📉 Fechamento relevante da curva"
        elif media_bps <= -1:
            interpretacao = "↘️ Leve fechamento da curva"
        elif media_bps >= 5:
            interpretacao = "📈 Abertura relevante da curva"
        elif media_bps >= 1:
            interpretacao = "↗️ Leve abertura da curva"
        else:
            interpretacao = "➡️ Variação média próxima de zero"

        # Nomes por extenso dos vértices para exibição amigável
        nomes_vertices = {
            "1M": "Vértice de 1 mês",
            "3M": "Vértice de 3 meses",
            "6M": "Vértice de 6 meses",
            "1A": "Vértice de 1 ano",
            "2A": "Vértice de 2 anos",
            "3A": "Vértice de 3 anos",
            "5A": "Vértice de 5 anos",
            "10A": "Vértice de 10 anos",
        }

        # Filtragem estrita: alta real (> 0) e queda real (< 0)
        df_altas = df_comp_vert[df_comp_vert["diff_taxa_bps"] > 0]
        df_quedas = df_comp_vert[df_comp_vert["diff_taxa_bps"] < 0]

        vertice_maior_alta = df_altas.loc[df_altas["diff_taxa_bps"].idxmax()] if not df_altas.empty else None
        vertice_maior_queda = df_quedas.loc[df_quedas["diff_taxa_bps"].idxmin()] if not df_quedas.empty else None

        # Cálculos do quarto card: Inclinação (1A - 5A)
        # Spread = Taxa(5A) - Taxa(1A)
        row_1a = df_comp_vert[df_comp_vert["vertice"] == "1A"]
        row_5a = df_comp_vert[df_comp_vert["vertice"] == "5A"]

        dados_inclinacao_1a_5a = None
        if not row_1a.empty and not row_5a.empty:
            taxa_1a_ini = row_1a["taxa_ini"].iloc[0]
            taxa_1a_fim = row_1a["taxa_fim"].iloc[0]
            taxa_5a_ini = row_5a["taxa_ini"].iloc[0]
            taxa_5a_fim = row_5a["taxa_fim"].iloc[0]

            inclinacao_ini_bps = (taxa_5a_ini - taxa_1a_ini) * 100.0
            inclinacao_fim_bps = (taxa_5a_fim - taxa_1a_fim) * 100.0
            var_inclinacao_bps = inclinacao_fim_bps - inclinacao_ini_bps

            # Regra de classificação de inclinação
            if var_inclinacao_bps > 1.0:
                subtitulo_inc = "Curva mais inclinada"
                cor_inc = "#dc2626"  # Vermelho para mais inclinada (positiva)
            elif var_inclinacao_bps < -1.0:
                subtitulo_inc = "Curva mais plana"
                cor_inc = "#15803d"  # Verde para mais plana (negativa)
            else:
                subtitulo_inc = "Inclinação estável"
                cor_inc = "#334155"  # Cinza para neutra/estável

            dados_inclinacao_1a_5a = {
                "var_bps": var_inclinacao_bps,
                "subtitulo": subtitulo_inc,
                "cor": cor_inc,
                "inc_ini": inclinacao_ini_bps,
                "inc_fim": inclinacao_fim_bps,
            }

        # Estilos compactos e elegantes com padding interno balanceado
        style_box = "padding: 8px 4px 6px 4px; display: flex; flex-direction: column; justify-content: center;"
        style_titulo = "font-size: 0.8125rem; color: #64748b; font-weight: 500; line-height: 1.2; margin-bottom: 3px;"
        style_valor_base = "font-size: 2.15rem; font-weight: 800; line-height: 1.1; margin: 4px 0;"
        style_subtitulo = "font-size: 0.875rem; color: #1e293b; font-weight: 600; line-height: 1.25; margin-bottom: 3px;"
        style_detalhe = "font-size: 0.75rem; color: #64748b; margin-top: 1px; line-height: 1.2;"

        # Exibição dos 4 cards com design customizado conforme referência
        c1, c2, c3, c4 = st.columns(4)

        # Card 1: Variação Média
        with c1:
            with st.container(border=True):
                cor_media = "#dc2626" if media_bps > 0 else ("#15803d" if media_bps < 0 else "#334155")
                sinal_media = "+" if media_bps > 0 else ""
                val_media_str = f"{sinal_media}{media_bps:.1f} bps".replace(".", ",")
                st.markdown(f"<div style='{style_box}'>"
                            f"<div style='{style_titulo}'>Variação média da curva</div>"
                            f"<div style='{style_valor_base} color: {cor_media};'>{val_media_str}</div>"
                            f"<div style='{style_subtitulo}'>{interpretacao}</div>"
                            f"<div style='{style_detalhe}'>Média dos vértices padronizados</div>"
                            f"</div>", unsafe_allow_html=True)

        # Card 2: Maior Abertura / Alta
        with c2:
            with st.container(border=True):
                if vertice_maior_alta is not None:
                    nome_ext = nomes_vertices.get(vertice_maior_alta['vertice'], f"Vértice {vertice_maior_alta['vertice']}")
                    val_alta_str = f"+{vertice_maior_alta['diff_taxa_bps']:.1f} bps".replace(".", ",")
                    taxas_str = f"{vertice_maior_alta['taxa_ini']:.2f}% → {vertice_maior_alta['taxa_fim']:.2f}% a.a.".replace(".", ",")
                    st.markdown(f"<div style='{style_box}'>"
                                f"<div style='{style_titulo}'>Maior abertura (alta)</div>"
                                f"<div style='{style_valor_base} color: #dc2626;'>{val_alta_str}</div>"
                                f"<div style='{style_subtitulo}'>{nome_ext}</div>"
                                f"<div style='{style_detalhe}'>{taxas_str}</div>"
                                f"</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='{style_box}'>"
                                f"<div style='{style_titulo}'>Maior abertura (alta)</div>"
                                f"<div style='{style_valor_base} color: #94a3b8;'>—</div>"
                                f"<div style='{style_subtitulo}'>Nenhum vértice com alta</div>"
                                f"<div style='{style_detalhe}'>Sem abertura de taxas no período</div>"
                                f"</div>", unsafe_allow_html=True)

        # Card 3: Maior Fechamento / Queda
        with c3:
            with st.container(border=True):
                if vertice_maior_queda is not None:
                    nome_ext = nomes_vertices.get(vertice_maior_queda['vertice'], f"Vértice {vertice_maior_queda['vertice']}")
                    val_queda_str = f"{vertice_maior_queda['diff_taxa_bps']:.1f} bps".replace(".", ",")
                    taxas_str = f"{vertice_maior_queda['taxa_ini']:.2f}% → {vertice_maior_queda['taxa_fim']:.2f}% a.a.".replace(".", ",")
                    st.markdown(f"<div style='{style_box}'>"
                                f"<div style='{style_titulo}'>Maior fechamento (queda)</div>"
                                f"<div style='{style_valor_base} color: #15803d;'>{val_queda_str}</div>"
                                f"<div style='{style_subtitulo}'>{nome_ext}</div>"
                                f"<div style='{style_detalhe}'>{taxas_str}</div>"
                                f"</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='{style_box}'>"
                                f"<div style='{style_titulo}'>Maior fechamento (queda)</div>"
                                f"<div style='{style_valor_base} color: #94a3b8;'>—</div>"
                                f"<div style='{style_subtitulo}'>Sem quedas no período</div>"
                                f"<div style='{style_detalhe}'>Nenhum vértice fechou taxa</div>"
                                f"</div>", unsafe_allow_html=True)

        # Card 4: Variação da Inclinação (1A - 5A)
        with c4:
            with st.container(border=True):
                if dados_inclinacao_1a_5a is not None:
                    var_bps = dados_inclinacao_1a_5a["var_bps"]
                    sinal_inc = "+" if var_bps > 0 else ""
                    val_inc_str = f"{sinal_inc}{var_bps:.1f} bps".replace(".", ",")
                    spread_str = f"Spread: {dados_inclinacao_1a_5a['inc_ini']:+.1f} → {dados_inclinacao_1a_5a['inc_fim']:+.1f} bps".replace(".", ",")
                    st.markdown(f"<div style='{style_box}'>"
                                f"<div style='{style_titulo}'>Variação da inclinação (1A–5A)</div>"
                                f"<div style='{style_valor_base} color: {dados_inclinacao_1a_5a['cor']};'>{val_inc_str}</div>"
                                f"<div style='{style_subtitulo}'>{dados_inclinacao_1a_5a['subtitulo']}</div>"
                                f"<div style='{style_detalhe}'>{spread_str}</div>"
                                f"</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='{style_box}'>"
                                f"<div style='{style_titulo}'>Variação da inclinação (1A–5A)</div>"
                                f"<div style='{style_valor_base} color: #94a3b8;'>—</div>"
                                f"<div style='{style_subtitulo}'>Dados insuficientes</div>"
                                f"<div style='{style_detalhe}'>Vértices 1A e/ou 5A ausentes</div>"
                                f"</div>", unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)

    fig = go.Figure()

    # Curva inicial
    fig.add_trace(
        go.Scatter(
            x=df_ini["dias_uteis"],
            y=df_ini["taxa"],
            mode="lines+markers",
            name=f"Curva em {pd.to_datetime(data_ini_str).strftime('%d/%m/%Y')}",
            line=dict(color="#64748B", width=2.5, dash="dash"),
            marker=dict(size=5),
            hovertemplate="<b>%{x} D.U.</b><br>Taxa: %{y:.2f}%<extra></extra>",
        )
    )

    # Curva final
    fig.add_trace(
        go.Scatter(
            x=df_fim["dias_uteis"],
            y=df_fim["taxa"],
            mode="lines+markers",
            name=f"Curva em {pd.to_datetime(data_fim_str).strftime('%d/%m/%Y')}",
            line=dict(color="#0055A5", width=3),
            marker=dict(size=6),
            hovertemplate="<b>%{x} D.U.</b><br>Taxa: %{y:.2f}%<extra></extra>",
        )
    )

    # Vértices de destaque para marcação vertical
    vertices_destaque = {
        "1M": 21,
        "6M": 126,
        "1A": 252,
        "2A": 504,
        "5A": 1260,
    }

    max_du_dados = max(df_ini["dias_uteis"].max(), df_fim["dias_uteis"].max())

    for label_vertice, du_val in vertices_destaque.items():
        if du_val <= max_du_dados:
            fig.add_vline(
                x=du_val,
                line_width=1.2,
                line_dash="dot",
                line_color="#94A3B8",
                annotation_text=f"<b>{label_vertice}</b> ({du_val} DU)",
                annotation_position="top left",
                annotation_font=dict(size=11, color="#475569"),
                annotation=dict(textangle=-90, yanchor="top"),
            )

    fig.update_layout(
        title="Estrutura a Termo da Taxa de Juros (ETTJ)",
        xaxis_title="Dias Úteis (D.U.)",
        yaxis_title="Taxa de Referência (% a.a.)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=70, b=40),
    )

    st.plotly_chart(fig, use_container_width=True)
