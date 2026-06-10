import json
import os
import pandas as pd
import streamlit as st
import plotly.express as px

from helpers import upload_and_filter_page
from kpis import compute_dashboard_data, format_horas_hhmmss, format_number_br

# Força a página a usar 100% da largura da tela (Layout Wide)
st.set_page_config(page_title="EPICO - Mapa Operacional", layout="wide")

# --- CONFIGURAÇÕES PADRÃO ---
META_PADRAO = 7 + 20 / 60
LIMITE_PADRAO = 9 + 20 / 60

# --- COORDENADAS CENTRAIS DAS UNIDADES OPERACIONAIS ---
CENTROS_CIDADES = {
    "Anápolis": {"lat": -16.3267, "lon": -48.9528},
    "Trindade": {"lat": -16.645, "lon": -49.495},
    "Jataí": {"lat": -17.8814, "lon": -51.7144},
    "Goiânia": {"lat": -16.6869, "lon": -49.2648}
}

# --- DETECÇÃO DINÂMICA DA CIDADE ATIVA ---
cidade_selecionada = st.session_state.get("global_cidade_ativa", "Trindade")
nome_slug = cidade_selecionada.lower().replace('í', 'i').replace('á', 'a').replace('ã', 'a')

# --- INICIALIZAÇÃO DA PÁGINA ---
jornada_meta, df_filtrado = upload_and_filter_page(
    "Mapa Operacional", 
    f"Visão geoespacial interativa de {cidade_selecionada}. Identifique os gargalos visualizando a cidade de cima."
)
results = compute_dashboard_data(df_filtrado, jornada_meta=jornada_meta)
rotas = results["rotas"].copy()

if rotas.empty:
    st.warning("Nenhum dado disponível após os filtros.")
    st.stop()

# --- VERIFICAÇÃO E CARGA DO GEOJSON DINÂMICO ---
geojson_path = f"maps/base_{nome_slug}.geojson"

if not os.path.exists(geojson_path):
    st.error(f"⚠️ O arquivo de mapa geográfico '{geojson_path}' não foi encontrado na pasta 'maps/'.")
    st.info(f"Por favor, salve a malha de setores como 'base_{nome_slug}.geojson' na pasta 'maps/' para ativar esta tela.")
    st.stop()

with open(geojson_path, "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

# --- BUSCAR DADOS DO SIMULADOR (MEMÓRIA) ---
cenario_otimizado = st.session_state.get("epico_relatorio_cenario")
origem_mapa = st.session_state.get("epico_relatorio_origem", "Atual")

usa_otimizado = False

if isinstance(cenario_otimizado, pd.DataFrame) and not cenario_otimizado.empty:
    st.success(f"✅ **Modo Otimizado Ativo:** O mapa está a exibir a projeção oficial salva: **{origem_mapa}**.")
    df_mapa = cenario_otimizado.copy()
    usa_otimizado = True
else:
    st.info("ℹ️ **Modo Atual Ativo:** O mapa está a exibir a realidade crua da operação. (Rode os simuladores e salve um cenário para ver a mudança).")
    df_mapa = rotas.copy()

# Tratamento para garantir o código do setor igual ao geojson ("apelido")
df_mapa["Setor"] = df_mapa["Setor"].astype(str).str.zfill(4)

# --- PREPARAÇÃO DE VARIÁVEIS PARA O MAPA ---
if usa_otimizado:
    df_mapa["Horas_Plot"] = df_mapa["Horas Simulada (h)"]
    df_mapa["Ton_Plot"] = df_mapa["Toneladas Simulada"]
    df_mapa["Km_Imp_Plot"] = df_mapa["Km Improdutivo Simulado"]
    df_mapa["Horas_Formatadas"] = df_mapa["Horas Simulada (h)"].apply(format_horas_hhmmss)
else:
    df_mapa["Horas_Plot"] = df_mapa["Horas Trabalhadas"]
    df_mapa["Ton_Plot"] = df_mapa["Toneladas"]
    df_mapa["Km_Imp_Plot"] = df_mapa["Km Improdutivo"]
    df_mapa["Horas_Formatadas"] = df_mapa["Horas Trabalhadas"].apply(format_horas_hhmmss)

df_mapa["Produtividade_Plot"] = df_mapa["Produtividade (t/h)"].fillna(0)

# --- CONTROLES DO MAPA ---
st.subheader("1. Camadas de Inteligência Geoespacial")

opcao_mapa = st.selectbox(
    f"Selecione o indicador que deseja pintar no mapa de {cidade_selecionada}:",
    [
        "⏳ Mapa de Jornada (Horas de Trabalho)",
        "⛽ Mapa de Desperdício (Km Improdutivo)",
        "⚖️ Mapa de Densidade de Peso (Toneladas)",
        "🚀 Mapa de Produtividade Efetiva (t/h)"
    ]
)

# Configuração condicional baseada na escolha do usuário
if "⏳ Mapa de Jornada" in opcao_mapa:
    coluna_cor = "Horas_Plot"
    escala_cor = "RdYlGn_r" 
    titulo_mapa = f"Distribuição da Jornada de Trabalho em {cidade_selecionada} (Meta Ideal: 07:20)"
    ponto_medio = META_PADRAO
elif "⛽ Mapa de Desperdício" in opcao_mapa:
    coluna_cor = "Km_Imp_Plot"
    escala_cor = "Reds"
    titulo_mapa = "Pontos de Sangramento: Rodagem Vazia até o Aterro"
    ponto_medio = df_mapa[coluna_cor].mean()
elif "⚖️ Mapa de Densidade" in opcao_mapa:
    coluna_cor = "Ton_Plot"
    escala_cor = "Blues"
    titulo_mapa = "Concentração de Coleta: Carga Total Gerada"
    ponto_medio = df_mapa[coluna_cor].mean()
else:
    coluna_cor = "Produtividade_Plot"
    escala_cor = "Viridis" 
    titulo_mapa = "Mapa de Velocidade de Coleta (Toneladas por Hora)"
    ponto_medio = df_mapa[coluna_cor].mean()

# Busca as coordenadas de centro correspondentes à cidade ativa (Evita mapas perdidos no oceano)
coordenadas_centro = CENTROS_CIDADES.get(cidade_selecionada, {"lat": -16.645, "lon": -49.495})

# --- GERAÇÃO DO MAPA PLOTLY CHOROPLETH MAPBOX ---
fig = px.choropleth_mapbox(
    df_mapa,
    geojson=geojson_data,
    locations="Setor",
    featureidkey="properties.apelido", 
    color=coluna_cor,
    color_continuous_scale=escala_cor,
    color_continuous_midpoint=ponto_medio,
    mapbox_style="carto-positron",
    zoom=12, 
    center=coordenadas_centro, 
    opacity=0.35, # Transparência para enxergar o mapa de fundo (ruas)
    hover_name="Setor",
    hover_data={
        "Setor": False,
        "Horas_Formatadas": True,
        "Ton_Plot": ":.2f",
        "Km_Imp_Plot": ":.2f",
        "Produtividade_Plot": ":.2f"
    },
    labels={
        coluna_cor: "Indicador",
        "Horas_Formatadas": "Tempo Gasto",
        "Ton_Plot": "Toneladas",
        "Km_Imp_Plot": "Km Vazios",
        "Produtividade_Plot": "t/h"
    }
)

fig.update_layout(
    title=titulo_mapa,
    margin={"r": 0, "t": 40, "l": 0, "b": 0},
    height=700 
)

st.plotly_chart(fig, use_container_width=True)

st.markdown(f"""
**💡 Dica de Navegação:** Você pode dar zoom usando a roda do mouse e clicar/segurar para arrastar a cidade. 
Passe o mouse por cima de qualquer setor colorido de {cidade_selecionada} para ver os dados vitais instantâneos dessa equipe operando na rua.
""")

st.markdown("---")
st.subheader("2. Detalhamento (Dados do Mapa)")
cols_view = ["Setor", "Horas_Formatadas", "Ton_Plot", "Km_Imp_Plot", "Produtividade_Plot"]
df_view = df_mapa[cols_view].copy()
df_view.columns = ["Setor", "Jornada", "Toneladas", "Km Improdutivo", "Produtividade (t/h)"]
st.dataframe(df_view, use_container_width=True, hide_index=True)