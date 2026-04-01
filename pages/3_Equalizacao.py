import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from helpers import upload_and_filter_page
from kpis import compute_dashboard_data, format_horas_hhmmss

# --- CONFIGURAÇÕES PADRÃO ---
META_PADRAO = 7 + 20/60
LIMITE_PADRAO = 9 + 20/60

st.set_page_config(page_title="Visão Geral / Equalização", page_icon="⚖️", layout="wide")

jornada_meta, df_filtrado = upload_and_filter_page(
    "Visão Geral: Diagnóstico e Equalização",
    "Média real do grupo, doadores, recebedores e regra de km alto."
)

results = compute_dashboard_data(df_filtrado, jornada_meta=jornada_meta)
rotas = results["rotas"].copy()
medias = results["medias"]
kpi = results["kpis"]

if rotas.empty:
    st.warning("Nenhum dado disponível após os filtros.")
    st.stop()

# ==========================================
# 🛠️ CORREÇÕES APLICADAS (LIXA DE DADOS)
# ==========================================
# 1. Limpeza do Setor (Remover .000000 forçando a texto)
rotas["Setor"] = pd.to_numeric(rotas["Setor"], errors="coerce").fillna(0).astype(int).astype(str)

# Forçar numéricos nas colunas principais para evitar erros
for col in ["Toneladas", "Km Total", "Produtividade (t/h)", "Horas Trabalhadas"]:
    rotas[col] = pd.to_numeric(rotas.get(col, 0), errors="coerce").fillna(0)

# 2. Correção Automática de Kg para Toneladas
if rotas["Toneladas"].max() > 100:
    rotas["Toneladas"] = rotas["Toneladas"] / 1000

# ==========================================
# 🧠 LÓGICA ORIGINAL DA SUA PÁGINA
# ==========================================
rotas["Ton/h"] = rotas["Produtividade (t/h)"]
rotas["Desvio Horas"] = rotas["Horas Trabalhadas"] - medias["media_horas"]
rotas["Km Alto"] = rotas["Km Total"] > (medias["media_km_total"] * 1.20)

def papel(row):
    if row["Desvio Horas"] > 0.15:
        return "Doador"
    if row["Desvio Horas"] < -0.15:
        return "Recebedor"
    return "Equilibrado"

rotas["Papel"] = rotas.apply(papel, axis=1)
rotas["Horas Trabalhadas HHMMSS"] = rotas["Horas Trabalhadas"].apply(format_horas_hhmmss)
rotas["Desvio Horas HHMMSS"] = rotas["Desvio Horas"].apply(
    lambda x: "-" + format_horas_hhmmss(abs(x)) if x < 0 else format_horas_hhmmss(abs(x))
)

# ==========================================
# 📊 INTERFACE VISUAL
# ==========================================
st.markdown("### 📋 Indicadores Globais da Frota")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Média de horas", format_horas_hhmmss(medias["media_horas"]))
c2.metric("Meta", format_horas_hhmmss(META_PADRAO))
c3.metric("Limite Legal", format_horas_hhmmss(LIMITE_PADRAO))
c4.metric("Amplitude", format_horas_hhmmss(kpi["amplitude_rotas"]))

st.markdown("---")

st.subheader("📊 Análise Visual de Jornadas")

g1, g2 = st.columns(2)

with g1:
    # GRÁFICO 1: HORAS ABSOLUTAS COM AS LINHAS COLORIDAS
    fig_abs = px.bar(
        rotas.sort_values("Horas Trabalhadas", ascending=False),
        x="Setor",
        y="Horas Trabalhadas",
        color="Papel",
        color_discrete_map={"Doador": "#ef553b", "Recebedor": "#00cc96", "Equilibrado": "#636efa"},
        text="Horas Trabalhadas HHMMSS",
        title="1. Jornada Atual vs Linhas de Meta"
    )
    fig_abs.update_traces(textposition="outside", cliponaxis=False)
    fig_abs.update_layout(xaxis=dict(type="category"), height=450)

    # Adicionando as linhas Verde, Amarela e Vermelha
    fig_abs.add_hline(y=META_PADRAO, line_dash="dash", line_color="green", annotation_text="Meta", annotation_position="top right")
    fig_abs.add_hline(y=medias["media_horas"], line_dash="dot", line_color="yellow", annotation_text="Média Atual", annotation_position="top right")
    fig_abs.add_hline(y=LIMITE_PADRAO, line_dash="dash", line_color="red", annotation_text="Limite Legal", annotation_position="top right")

    # Ajuste de eixo para as labels não cortarem
    max_y = max(rotas["Horas Trabalhadas"].max(), LIMITE_PADRAO)
    fig_abs.update_yaxes(range=[0, max_y * 1.15])

    st.plotly_chart(fig_abs, use_container_width=True)

with g2:
    # GRÁFICO 2: O SEU GRÁFICO ORIGINAL DE DESVIOS
    fig_dev = px.bar(
        rotas.sort_values("Desvio Horas", ascending=False),
        x="Setor",
        y="Desvio Horas",
        color="Papel",
        color_discrete_map={"Doador": "#ef553b", "Recebedor": "#00cc96", "Equilibrado": "#636efa"},
        text="Desvio Horas",
        title="2. Desvio de Horas vs Média da Frota"
    )
    fig_dev.update_traces(texttemplate="%{text:.2f}h", textposition="outside", cliponaxis=False)
    fig_dev.update_layout(xaxis=dict(type="category"), height=450)
    
    if not rotas.empty:
        lim = max(abs(rotas["Desvio Horas"].min()), abs(rotas["Desvio Horas"].max()))
        fig_dev.update_yaxes(range=[-lim * 1.25, lim * 1.25])
        
    st.plotly_chart(fig_dev, use_container_width=True)

st.markdown("---")

st.subheader("📋 Tabela Analítica: Doadores e Recebedores")

# Arredondando os números para a tabela ficar com leitura executiva
tabela_view = rotas.copy()
tabela_view["Toneladas"] = tabela_view["Toneladas"].round(2)
tabela_view["Ton/h"] = tabela_view["Ton/h"].round(2)
tabela_view["Km Total"] = tabela_view["Km Total"].round(2)

st.dataframe(
    tabela_view[
        [
            "Setor",
            "Dias Encontrados",
            "Horas Trabalhadas HHMMSS",
            "Desvio Horas HHMMSS",
            "Toneladas",
            "Ton/h",
            "Km Total",
            "Km Alto",
            "Papel",
        ]
    ],
    use_container_width=True,
    hide_index=True
)
