import streamlit as st
import pandas as pd
import os
import numpy as np
# 📍 IMPORTANTE: Adicionada a importação de _normalize_headers do kpis.py
from kpis import apply_filters, get_filter_options, _normalize_headers


def _options_from_series(series, cast_str=False):
    if cast_str:
        series = series.astype(str)
    return sorted(series.dropna().unique())


def _keep_existing(selected, options):
    return [item for item in selected if item in options]


def load_automated_city_data(cidade_ativa):
    """
    Função de bastidor: Tenta buscar os arquivos automaticamente nas pastas.
    Se a pasta ou o arquivo não existirem ainda, retorna um DataFrame vazio
    para que o sistema use o upload manual padrão do app.py.
    """
    nome_base = cidade_ativa.lower().replace('í', 'i').replace('á', 'a')
    caminho_csv = f"data/base_{nome_base}.csv"
    caminho_xlsx = f"data/base_{nome_base}.xlsx"
    
    df_principal = pd.DataFrame()
    
    # 1. Tenta carregar a base operacional da pasta data/
    if os.path.exists(caminho_csv):
        df_principal = pd.read_csv(caminho_csv, sep=';', encoding='utf-8')
        if len(df_principal.columns) < 5: 
            df_principal = pd.read_csv(caminho_csv, sep=',', encoding='utf-8')
    elif os.path.exists(caminho_xlsx):
        df_principal = pd.read_excel(caminho_xlsx)
    else:
        return pd.DataFrame() # Retorna vazio se você ainda não criou as pastas

    # 📍 CORREÇÃO: Aplica a lixa de cabeçalhos oficial do kpis.py para unificar "Combústivel" -> "Combustível"
    df_principal = _normalize_headers(df_principal)
    
    # Garante que números vindo do padrão Inlog/Br (com vírgula) virem float americano
    colunas_para_limpar = ['Km Produtivo', 'Km Improdutivo', 'Km Total', 'Toneladas', 'Viagens']
    for col in colunas_para_limpar:
        if col in df_principal.columns and df_principal[col].dtype == 'object':
            df_principal[col] = df_principal[col].astype(str).str.replace(',', '.', regex=False)
            df_principal[col] = df_principal[col].str.replace(r'[^\d.]', '', regex=True)
            df_principal[col] = pd.to_numeric(df_principal[col].replace('', '0'), errors='coerce').fillna(0)

    # 2. Tenta carregar as distâncias reais da garagem/aterro da pasta distancia/
    caminho_dist = f"distancia/anapolis_apapolis.csv" if cidade_ativa == "Anápolis" else f"distancia/distancia_{nome_base}.csv"
    
    if os.path.exists(caminho_dist):
        try:
            df_dist = pd.read_csv(caminho_dist, sep=';')
            df_dist.columns = df_dist.columns.str.strip()
            
            col_setor_dist = [c for c in df_dist.columns if 'SETOR' in c.upper() and 'DISTANCIA' not in c.upper()][0]
            col_garagem = [c for c in df_dist.columns if 'GARAGEM' in c.upper()][0]
            col_aterro = [c for c in df_dist.columns if 'ATERRO' in c.upper()][0]
            
            df_dist[col_setor_dist] = df_dist[col_setor_dist].astype(str).str.strip()
            df_principal['Setor'] = df_principal['Setor'].astype(str).str.strip()
            
            for col in [col_garagem, col_aterro]:
                df_dist[col] = df_dist[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df_dist[col] = pd.to_numeric(df_dist[col].str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
                if df_dist[col].max() > 1000: 
                    df_dist[col] = df_dist[col] / 1000

            df_dist.rename(columns={
                col_setor_dist: 'Setor', 
                col_garagem: 'Dist Garagem (km)', 
                col_aterro: 'Dist Aterro (km)'
            }, inplace=True)
            
            df_principal = pd.merge(df_principal, df_dist[['Setor', 'Dist Garagem (km)', 'Dist Aterro (km)']], on='Setor', how='left')
        except Exception as e:
            st.sidebar.warning(f"Aviso: Matriz de distância de {cidade_ativa} ignorada devido a: {e}")

    # Garante a existência das colunas para evitar quebras no simulador
    if 'Dist Garagem (km)' not in df_principal.columns: df_principal['Dist Garagem (km)'] = 0.0
    if 'Dist Aterro (km)' not in df_principal.columns: df_principal['Dist Aterro (km)'] = 0.0

    return df_principal


def upload_and_filter_page(title, caption):
    st.title(title)
    st.caption(caption)

    state = st.session_state

    # --- INJEÇÃO DA SELEÇÃO DE UNIDADE (SIDEBAR) ---
    st.sidebar.header("🏢 Unidade em Análise")
    cidade_ativa = st.sidebar.selectbox(
        "Selecione a Cidade:",
        options=["Anápolis", "Trindade", "Jataí", "Goiânia"],
        key="global_cidade_ativa"
    )

    # Tenta carregar automaticamente das pastas locais
    df_auto = load_automated_city_data(cidade_ativa)

    if not df_auto.empty:
        df = df_auto
        state["epico_df"] = df # Sincroniza com a memória global
        state["epico_nome_arquivo"] = f"Pasta Local: base_{cidade_ativa.lower().replace('í','i').replace('á','a')}"
    else:
        # Se você ainda não criou as pastas ou arquivos, recorre ao upload manual antigo do app.py
        if "epico_df" not in state:
            st.warning(f"Nenhuma base de dados automática encontrada para {cidade_ativa}. Vá para a página inicial (app.py) e envie o arquivo Inlog manualmente.")
            st.stop()
        df = state["epico_df"]

    unidades, turnos, dias, setores = get_filter_options(df)

    state.setdefault("jornada_meta", 7.33)
    state.setdefault("filtro_unidades", unidades)
    state.setdefault("filtro_turnos", turnos)
    state.setdefault("filtro_dias", dias)
    state.setdefault("filtro_setores", setores)

    st.sidebar.subheader("Configuração Global")
    state["jornada_meta"] = st.sidebar.number_input(
        "Jornada contratual/meta (horas)",
        min_value=1.0,
        max_value=24.0,
        value=float(state["jornada_meta"]),
        step=0.01,
        key=f"global_jornada_meta_{title}"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"**Base ativa:** \n{state.get('epico_nome_arquivo', 'arquivo carregado')}"
    )

    st.subheader("Filtros Globais da Plataforma")

    selected_unidades = _keep_existing(state["filtro_unidades"], unidades)
    col1, col2, col3, col4 = st.columns(4)

    state["filtro_unidades"] = col1.multiselect(
        "🏢 Unidade",
        unidades,
        default=selected_unidades,
        key=f"global_unidades_{title}"
    )

    df_temp1 = df[df["Unidade"].isin(state["filtro_unidades"])] if state["filtro_unidades"] else df
    opcoes_turnos = _options_from_series(df_temp1["Turno"])
    selected_turnos = _keep_existing(state["filtro_turnos"], opcoes_turnos)

    state["filtro_turnos"] = col2.multiselect(
        "⏱️ Turno",
        opcoes_turnos,
        default=selected_turnos,
        key=f"global_turnos_{title}"
    )

    df_temp2 = df_temp1[df_temp1["Turno"].isin(state["filtro_turnos"])] if state["filtro_turnos"] else df_temp1
    opcoes_dias = _options_from_series(df_temp2["Dia da Semana"])
    selected_dias = _keep_existing(state["filtro_dias"], opcoes_dias)

    state["filtro_dias"] = col3.multiselect(
        "📅 Dia da Semana",
        opcoes_dias,
        default=selected_dias,
        key=f"global_dias_{title}"
    )

    df_temp3 = df_temp2[df_temp2["Dia da Semana"].isin(state["filtro_dias"])] if state["filtro_dias"] else df_temp2
    opcoes_setores = _options_from_series(df_temp3["Setor"], cast_str=True)
    selected_setores = [s for s in state["filtro_setores"] if str(s) in opcoes_setores]

    state["filtro_setores"] = col4.multiselect(
        "📍 Setor",
        opcoes_setores,
        default=selected_setores,
        key=f"global_setores_{title}"
    )

    df_filtrado = apply_filters(
        df,
        state["filtro_unidades"],
        state["filtro_turnos"],
        state["filtro_dias"],
        state["filtro_setores"],
    )

    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
        st.stop()

    return state["jornada_meta"], df_filtrado