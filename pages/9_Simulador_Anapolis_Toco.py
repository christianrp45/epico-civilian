import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from kpis import format_number_br, format_horas_hhmmss

st.set_page_config(page_title="ÉPICO - Redesenho Anápolis (Toco)", layout="wide")

st.title("🚚 Dimensionamento Estratégico: Transição Trucado ➔ Toco")
st.caption("Estudo de viabilidade técnica para a Unidade de Anápolis: Redistribuição de carga para 15 Rotas por Turno.")

# --- 📍 MOTOR DE BUSCA FLEXÍVEL DE DIRETÓRIOS ---
@st.cache_data
def carregar_dados_anapolis():
    caminhos_base = ["base_anapolis.csv", "data/base_anapolis.csv", "data\\base_anapolis.csv"]
    caminhos_dist = ["anapolis_apapolis.csv", "distancia/anapolis_apapolis.csv", "distancia\\anapolis_apapolis.csv"]
    
    path_base = None
    for p in caminhos_base:
        if os.path.exists(p):
            path_base = p
            break
            
    path_dist = None
    for p in caminhos_dist:
        if os.path.exists(p):
            path_dist = p
            break
            
    if not path_base or not path_dist:
        return None, None
    
    try:
        df_operacao = pd.read_csv(path_base, encoding="utf-8")
    except UnicodeDecodeError:
        df_operacao = pd.read_csv(path_base, encoding="latin1")
        
    try:
        df_distancias = pd.read_csv(path_dist, encoding="utf-8")
    except UnicodeDecodeError:
        df_distancias = pd.read_csv(path_dist, encoding="latin1")
        
    return df_operacao, df_distancias

df_op, df_dist = carregar_dados_anapolis()

if df_op is None:
    st.error("⚠️ **Arquivos não encontrados!** O sistema buscou na raiz e nas pastas '/data' e '/distancia', mas não localizou os arquivos de Anápolis.")
    st.stop()

# --- 🧠 LIMPEZA E RASTREAMENTO DINÂMICO DE COLUNAS (FIM DO KEYERROR) ---
df_op.columns = df_op.columns.str.strip()
df_dist.columns = df_dist.columns.str.strip()

# Localiza as colunas de identificação de Setor sem depender de letras maiúsculas/minúsculas
col_setor_op = [c for c in df_op.columns if 'SETOR' in c.upper()][0]

# Na tabela de distâncias, filtra para pegar a coluna do código do setor (ignorando as colunas de distância)
col_setor_dist_lista = [c for c in df_dist.columns if c.upper() == 'SETOR' or (('SETOR' in c.upper() or 'COD' in c.upper()) and 'DIST' not in c.upper())]
col_setor_dist = col_setor_dist_lista[0] if col_setor_dist_lista else df_dist.columns[0]

# Força a criação das colunas padronizadas que o motor utiliza
df_op['Setor'] = pd.to_numeric(df_op[col_setor_op], errors='coerce').fillna(0).astype(int).astype(str).str.zfill(4)
df_dist['SETOR'] = pd.to_numeric(df_dist[col_setor_dist], errors='coerce').fillna(0).astype(int).astype(str).str.zfill(4)

# Tratamento de quilometragem, toneladas e viagens
for c in ['Km Total', 'Toneladas', 'Viagens']:
    if c in df_op.columns:
        df_op[c] = pd.to_numeric(df_op[c].astype(str).str.replace(',', '.', regex=False), errors='coerce').fillna(0.0)

# Localiza as colunas de distância de garagem e aterro de forma inteligente
col_garagem = [c for c in df_dist.columns if 'GARAGEM' in c.upper()][0]
col_aterro = [c for c in df_dist.columns if 'ATERRO' in c.upper()][0]

df_dist['Dist_Garagem_Km'] = pd.to_numeric(df_dist[col_garagem], errors='coerce').fillna(0.0)
df_dist['Dist_Aterro_Km'] = pd.to_numeric(df_dist[col_aterro], errors='coerce').fillna(0.0)

# Ajuste de escala caso esteja em metros (maior que 100)
if df_dist['Dist_Garagem_Km'].max() > 100: df_dist['Dist_Garagem_Km'] /= 1000.0
if df_dist['Dist_Aterro_Km'].max() > 100: df_dist['Dist_Aterro_Km'] /= 1000.0

# --- SEÇÃO 1: DIAGNÓSTICO BASELINE (FROTA TRUCADO ATUAL) ---
st.subheader("📊 1. Diagnóstico de Rodagem por Setor (Frota Trucado Atual)")
st.markdown("Média de quilometragem diária e projeção mensal consolidada baseada em 26 dias operacionais.")

baseline_setores = df_op.groupby('Setor').agg({
    'Km Total': 'mean',
    'Toneladas': 'mean',
    'Viagens': 'mean'
}).reset_index()

baseline_completa = pd.merge(baseline_setores, df_dist[['SETOR', 'Dist_Garagem_Km', 'Dist_Aterro_Km']], left_on='Setor', right_on='SETOR', how='left').fillna(7.5)
baseline_completa['Km Mensal Projetado'] = baseline_completa['Km Total'] * 26

df_baseline_view = baseline_completa.copy()
df_baseline_view.rename(columns={
    'Km Total': 'Média Km Diário',
    'Km Mensal Projetado': 'Km Mensal Projetado (26 dias)',
    'Toneladas': 'Média Peso Diário'
}, inplace=True)

st.dataframe(df_baseline_view[['Setor', 'Média Km Diário', 'Km Mensal Projetado (26 dias)', 'Média Peso Diário', 'Dist_Aterro_Km']].style.format({
    "Média Km Diário": "{:.2f} km",
    "Km Mensal Projetado (26 dias)": "{:,.2f} km",
    "Média Peso Diário": "{:.2f} t",
    "Dist_Aterro_Km": "{:.2f} km"
}), use_container_width=True, hide_index=True)

# --- SEÇÃO 2: MODELAGEM E REDISTRIBUIÇÃO (15 ROTAS TOCO POR TURNO) ---
st.markdown("---")
st.subheader("🎯 2. Redimensionamento e Redistribuição Magnética (Cenário: 15 Rotas Toco)")
st.markdown("Agrupamento do volume total de Anápolis por Turno e divisão matemática igualitária entre **15 novas equipes**, aplicando a penalidade física de cubagem do caminhão Toco ($V_{\\text{toco}} = 1.5 \\times V_{\\text{trucado}}$).")

resumo_turnos = df_op.groupby('Turno').agg({
    'Toneladas': 'sum',
    'Km Total': 'sum',
    'Viagens': 'sum'
}).reset_index()

novas_rotas_lista = []

for _, row_turno in resumo_turnos.iterrows():
    turno = row_turno['Turno']
    ton_total_turno = row_turno['Toneladas']
    viagens_trucado_total = row_turno['Viagens']
    km_total_trucado = row_turno['Km Total']
    
    viagens_toco_total = viagens_trucado_total * 1.5
    dist_aterro_media = baseline_completa['Dist_Aterro_Km'].mean()
    viagens_adicionais = viagens_toco_total - viagens_trucado_total
    km_extra_aterro_total = viagens_adicionais * (dist_aterro_media * 2)
    
    km_total_toco_turno = km_total_trucado + km_extra_aterro_total
    
    for i in range(1, 16):
        nome_rota = f"TOCO-{turno[:3].upper()}-{str(i).zfill(2)}"
        novas_rotas_lista.append({
            "Nova Rota": nome_rota,
            "Turno": turno,
            "Perfil Veículo": "Toco (Simulado)",
            "Carga Diária Distribuída": ton_total_turno / 15.0,
            "Viagens Toco Projetadas": viagens_toco_total / 15.0,
            "Km Diário Projetado": km_total_toco_turno / 15.0,
            "Km Mensal Projetado": (km_total_toco_turno / 15.0) * 26
        })

df_simulado_toco = pd.DataFrame(novas_rotas_lista)

st.dataframe(df_simulado_toco.style.format({
    "Carga Diária Distribuída": "{:.2f} t",
    "Viagens Toco Projetadas": "{:.1f}",
    "Km Diário Projetado": "{:.2f} km",
    "Km Mensal Projetado": "{:,.2f} km"
}), use_container_width=True, hide_index=True)

# --- GRÁFICO COMPARATIVO ---
st.markdown("---")
st.subheader("📈 3. Impacto Macroeconômico na Rodagem de Anápolis")

km_atual_total = baseline_completa['Km Mensal Projetado'].sum()
km_simulado_total = df_simulado_toco['Km Mensal Projetado'].sum()
delta_km_total = km_simulado_total - km_atual_total

m1, m2, m3 = st.columns(3)
m1.metric("KMs Mensais Atuais (Trucado)", f"{km_atual_total:,.1f} km")
m2.metric("KMs Mensais Projetados (Toco)", f"{km_simulado_total:,.1f} km")
m3.metric("Acréscimo de Rodagem (Transição)", f"+{delta_km_total:,.1f} km", delta_color="inverse")

fig_comp = px.bar(
    df_simulado_toco.groupby('Turno')['Km Diário Projetado'].sum().reset_index(),
    x='Turno', y='Km Diário Projetado',
    title="Distribuição de Quilometragem Diária por Turno (Modelo Nova Frota 15 Rotas)",
    color='Turno', color_continuous_scale="Blugrn"
)
st.plotly_chart(fig_comp, use_container_width=True)