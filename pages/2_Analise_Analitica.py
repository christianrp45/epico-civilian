import pandas as pd
import streamlit as st
import plotly.express as px
from helpers import upload_and_filter_page
from kpis import compute_dashboard_data, format_number_br, format_horas_hhmmss

jornada_meta, df_filtrado = upload_and_filter_page(
    "Analise Analitica",
    "Produtividade, km improdutivo, combustível e ranking de eficiência."
)

results = compute_dashboard_data(df_filtrado, jornada_meta=jornada_meta)
rotas = results["rotas"]
kpi = results["kpis"]

a1, a2, a3, a4 = st.columns(4)
a1.metric("Ton/Viagem média", format_number_br(kpi["ton_viagem_media"], 2))
a2.metric("Horas extras/dia", format_horas_hhmmss(kpi["horas_extras_total"]))
a3.metric(
    "% Km improdutivo",
    f"{kpi['km_improdutivo_pct_total']:.1%}" if pd.notna(kpi["km_improdutivo_pct_total"]) else "-"
)
a4.metric("Km/L", format_number_br(kpi["km_por_litro"], 2))

rotas["Ranking Eficiência"] = (
    rotas["Produtividade (t/h)"] /
    ((rotas["% Km Improdutivo"].fillna(0) + 0.01) + (rotas["L/ton"].fillna(0) + 0.01))
)

c1, c2 = st.columns(2)

with c1:
    fig_prod = px.bar(
        rotas.sort_values("Produtividade (t/h)", ascending=False),
        x="Setor",
        y="Produtividade (t/h)",
        text="Produtividade (t/h)",
        title="Produtividade média diária por setor"
    )
    fig_prod.update_traces(texttemplate="%{text:.2f}", textposition="outside", cliponaxis=False)
    fig_prod.update_layout(xaxis=dict(type="category"), height=420, margin=dict(t=70, b=40, l=40, r=20))
    if not rotas.empty:
        fig_prod.update_yaxes(range=[0, rotas["Produtividade (t/h)"].max() * 1.20])
    st.plotly_chart(fig_prod, use_container_width=True)

with c2:
    fig_km = px.bar(
        rotas.sort_values("% Km Improdutivo", ascending=False),
        x="Setor",
        y="% Km Improdutivo",
        text="% Km Improdutivo",
        title="% de Km improdutivo por setor"
    )
    fig_km.update_traces(texttemplate="%{text:.1%}", textposition="outside", cliponaxis=False)
    fig_km.update_layout(
        xaxis=dict(type="category"),
        yaxis_tickformat=".0%",
        height=420,
        margin=dict(t=70, b=40, l=40, r=20)
    )
    if not rotas.empty:
        fig_km.update_yaxes(range=[0, rotas["% Km Improdutivo"].max() * 1.20])
    st.plotly_chart(fig_km, use_container_width=True)

st.subheader("Tabela Analítica")
rotas_exib = rotas.copy()
rotas_exib["Horas Trabalhadas"] = rotas_exib["Horas Trabalhadas"].apply(format_horas_hhmmss)
rotas_exib["% Km Improdutivo"] = (rotas_exib["% Km Improdutivo"] * 100).round(1)

st.dataframe(
    rotas_exib[
        [
            "Setor",
            "Dias Encontrados",
            "Toneladas",
            "Horas Trabalhadas",
            "Produtividade (t/h)",
            "Ton/Viagem",
            "Km Total",
            "% Km Improdutivo",
            "L/ton",
            "Km/L",
            "Ranking Eficiência",
        ]
    ],
    use_container_width=True,
    hide_index=True
)