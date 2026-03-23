import streamlit as st
import plotly.express as px
from helpers import upload_and_filter_page
from kpis import compute_dashboard_data, format_horas_hhmmss

jornada_meta, df_filtrado = upload_and_filter_page(
    "Equalizacao",
    "Média real do grupo, doadores, recebedores e regra de km alto."
)

results = compute_dashboard_data(df_filtrado, jornada_meta=jornada_meta)
rotas = results["rotas"]
medias = results["medias"]
kpi = results["kpis"]

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

c1, c2, c3, c4 = st.columns(4)
c1.metric("Média de horas", format_horas_hhmmss(medias["media_horas"]))
c2.metric("Meta", format_horas_hhmmss(7 + 20/60))
c3.metric("Limite", format_horas_hhmmss(9 + 20/60))
c4.metric("Amplitude", format_horas_hhmmss(kpi["amplitude_rotas"]))

st.dataframe(
    rotas[
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

fig = px.bar(
    rotas.sort_values("Desvio Horas", ascending=False),
    x="Setor",
    y="Desvio Horas",
    color="Papel",
    text="Desvio Horas",
    title="Desvio de horas por setor"
)
fig.update_traces(texttemplate="%{text:.2f}", textposition="outside", cliponaxis=False)
fig.update_layout(xaxis=dict(type="category"), height=420, margin=dict(t=70, b=40, l=40, r=20))
if not rotas.empty:
    lim = max(abs(rotas["Desvio Horas"].min()), abs(rotas["Desvio Horas"].max()))
    fig.update_yaxes(range=[-lim * 1.25, lim * 1.25])
st.plotly_chart(fig, use_container_width=True)