import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from kpis import format_horas_hhmmss, format_number_br

st.set_page_config(page_title="Simulador Executivo", page_icon="🛠️", layout="wide")

st.title("🛠️ Simulador Executivo (Manual)")
st.caption("Suas regras ficam salvas na memória. Navegue pelo sistema e, quando pronto, envie o cenário final para o Relatório.")

# --- CONFIGURAÇÕES E DADOS ---
if "epico_df" not in st.session_state:
    st.warning("⚠️ Nenhuma base carregada. Vá à página principal.")
    st.stop()

df = st.session_state["epico_df"]
meta = st.session_state.get("meta_operacional", 7 + 20/60)
limite = 9 + 20/60 # Limite legal padrão

st.markdown("### 🔍 1. Isole o Cenário")
c_turno, c_dia = st.columns(2)
with c_turno:
    turnos_disp = ["Todos"] + list(df['Turno'].dropna().unique())
    idx_t = turnos_disp.index("DIURNO") if "DIURNO" in turnos_disp else 0
    turno_escolhido = st.selectbox("Turno:", options=turnos_disp, index=idx_t)
with c_dia:
    dias_disp = ["Todos"] + list(df['Dia da Semana'].dropna().unique())
    idx_d = dias_disp.index("Segunda-feira") if "Segunda-feira" in dias_disp else 0
    dia_escolhido = st.selectbox("Dia da Semana:", options=dias_disp, index=idx_d)

df_filtrado = df.copy()
if turno_escolhido != "Todos": df_filtrado = df_filtrado[df_filtrado['Turno'] == turno_escolhido]
if dia_escolhido != "Todos": df_filtrado = df_filtrado[df_filtrado['Dia da Semana'] == dia_escolhido]

if df_filtrado.empty:
    st.warning("Nenhum dado para este filtro.")
    st.stop()

# --- PREPARAÇÃO E LIMPEZA DE DADOS (PADRONIZAÇÃO EPICO) ---
def extrair_horas(hora_str):
    try:
        h, m, s = map(int, str(hora_str).split(':'))
        return h + (m / 60) + (s / 3600)
    except: return np.nan

df_calc = df_filtrado.copy()
df_calc['Setor'] = pd.to_numeric(df_calc['Setor'], errors='coerce').fillna(0).astype(int).astype(str)
df_calc['Horas_Dec'] = df_calc['Horas Trabalhadas'].apply(extrair_horas) if 'Horas Trabalhadas' in df_calc.columns else 7.33

# Força a existência de todas as colunas que o Relatório e Mapa precisam
for col in ['Viagens', 'Km Total', 'Toneladas', 'Combustível', 'Km Improdutivo', 'Produtividade (t/h)']:
    if col not in df_calc.columns:
        df_calc[col] = 0.0 # Cria a coluna com zeros caso ela não exista na base importada
    
    df_calc[col] = pd.to_numeric(df_calc[col], errors='coerce').fillna(0)

df_jornada = df_calc.groupby('Setor').mean(numeric_only=True).reset_index()

if df_jornada['Toneladas'].max() > 100:
    df_jornada['Toneladas'] = df_jornada['Toneladas'] / 1000

# RENOMEIA PARA O PADRÃO QUE O MAPA E RELATÓRIO ENTENDEM
df_jornada.rename(columns={
    'Horas_Dec': 'Horas Atual (h)',
    'Km Total': 'Km Atual',
    'Toneladas': 'Ton Atual',
    'Combustível': 'Combustível Atual',
    'Viagens': 'Viagens Atual'
}, inplace=True)

df_jornada['Horas Atual (h)'] = df_jornada['Horas Atual (h)'].round(2)
if 'Capacidade (t)' not in df_jornada.columns: df_jornada['Capacidade (t)'] = 9.5 # Fallback para o relatório

# --- BALANÇO DE NECESSIDADES ---
st.markdown("---")
st.subheader("📋 2. Balanço de Necessidades (Antes da Simulação)")

media_frota = df_jornada['Horas Atual (h)'].mean()
st.info(f"Onde precisamos mexer? Média atual da frota: **{format_horas_hhmmss(media_frota)}** (Limite legal: 09:20:00)")

df_balanco = df_jornada.copy()
df_balanco['Desvio'] = df_balanco['Horas Atual (h)'] - media_frota
df_balanco['Status'] = np.where(df_balanco['Desvio'] > 0.15, "🚩 Doador (Acima da Média)", 
                       np.where(df_balanco['Desvio'] < -0.15, "✅ Recebedor (Abaixo da Média)", "🟢 Equilibrado"))

df_bal_view = df_balanco.copy()
df_bal_view['Horas Atual'] = df_bal_view['Horas Atual (h)'].apply(format_horas_hhmmss)
df_bal_view['Desvio da Média'] = df_bal_view['Desvio'].apply(lambda x: f"+{format_horas_hhmmss(abs(x))}" if x > 0 else f"-{format_horas_hhmmss(abs(x))}")

df_bal_view['Ton Atual'] = df_bal_view['Ton Atual'].round(2)
df_bal_view['Km Atual'] = df_bal_view['Km Atual'].round(2)

st.dataframe(df_bal_view[['Setor', 'Horas Atual', 'Status', 'Desvio da Média', 'Ton Atual', 'Km Atual']].style.apply(lambda x: [
    'background-color: #ffcccc' if v == "🚩 Doador (Acima da Média)" else ('background-color: #e6ffe6' if v == "✅ Recebedor (Abaixo da Média)" else '') for v in x
], axis=1, subset=['Status']), use_container_width=True, hide_index=True)


# --- MOTOR DE TRANSFERÊNCIAS DINÂMICO ---
st.markdown("---")
st.subheader("⚙️ 3. Otimização Manual Múltipla (De -> Para)")
st.caption("Adicione linhas. Suas regras ficam na memória temporária se você for olhar o mapa e voltar.")

if "num_linhas_manuais" not in st.session_state: 
    st.session_state["num_linhas_manuais"] = 1
if "transferencias_manuais" not in st.session_state: 
    st.session_state["transferencias_manuais"] = []

b1, b2, _ = st.columns([2, 2, 6])
with b1:
    if st.button("➕ Adicionar linha de equalização", use_container_width=True):
        st.session_state["num_linhas_manuais"] += 1
        st.rerun()
with b2:
    if st.button("➖ Remover última linha", use_container_width=True):
        if st.session_state["num_linhas_manuais"] > 1:
            st.session_state["num_linhas_manuais"] -= 1
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)
transferencias_validas = []

# Gera os inputs mantendo as seleções antigas na tela
for i in range(st.session_state["num_linhas_manuais"]):
    c1, c2, c3 = st.columns(3)
    with c1: 
        origem = st.selectbox(f"Doador (Perde horas) - Regra {i+1}:", options=["Nenhum"] + df_jornada['Setor'].tolist(), key=f"origem_{i}")
    with c2: 
        destino = st.selectbox(f"Receptor (Ganha horas) - Regra {i+1}:", options=["Nenhum"] + df_jornada['Setor'].tolist(), key=f"destino_{i}")
    with c3: 
        horas_trans = st.number_input(f"Horas a transferir - Regra {i+1}:", min_value=0.1, step=0.1, value=1.0, key=f"horas_{i}")
    
    if origem != "Nenhum" and destino != "Nenhum":
        if origem != destino:
            transferencias_validas.append({"Doador": origem, "Receptor": destino, "Horas": horas_trans})
        else:
            st.warning(f"⚠️ Regra {i+1}: Doador e Receptor não podem ser o mesmo setor.")

df_resultado = df_jornada.copy()
df_resultado['Horas Simulada (h)'] = df_resultado['Horas Atual (h)']

# Aplica os cálculos na hora
if transferencias_validas:
    st.success(f"**{len(transferencias_validas)} regra(s) ativa(s) em memória! Veja o resultado projetado abaixo.**")
    for t in transferencias_validas:
        idx_d = df_resultado.index[df_resultado['Setor'] == t['Doador']].tolist()[0]
        idx_r = df_resultado.index[df_resultado['Setor'] == t['Receptor']].tolist()[0]
        df_resultado.at[idx_d, 'Horas Simulada (h)'] -= t['Horas']
        df_resultado.at[idx_r, 'Horas Simulada (h)'] += t['Horas']
else:
    st.info("Preencha o Doador e o Receptor acima para ver a simulação acontecendo.")

# --- FÍSICA PROPORCIONAL BLINDADA (NOMES CORRETOS PARA O MAPA E RELATÓRIO) ---
df_resultado['Fator'] = np.where(df_resultado['Horas Atual (h)'] > 0, df_resultado['Horas Simulada (h)'] / df_resultado['Horas Atual (h)'], 1.0)

df_resultado['Km Simulado'] = df_resultado['Km Atual'] * df_resultado['Fator']
df_resultado['Toneladas Simulada'] = df_resultado['Ton Atual'] * df_resultado['Fator']
df_resultado['Combustível Simulado'] = df_resultado['Combustível Atual'] * df_resultado['Fator']
df_resultado['Viagens Projetadas'] = np.ceil(df_resultado['Viagens Atual'] * df_resultado['Fator'])

# Proteção para o Mapa
df_resultado['Km Improdutivo Simulado'] = df_resultado.get('Km Improdutivo', 0) * df_resultado['Fator']

# --- DIAGNÓSTICO PÓS-SIMULAÇÃO (O QUE MUDOU?) ---
df_resultado['Alteração (h)'] = df_resultado['Horas Simulada (h)'] - df_resultado['Horas Atual (h)']
df_resultado['Papel Assumido'] = np.where(df_resultado['Alteração (h)'] < -0.01, "🔴 Doou Horas", 
                                 np.where(df_resultado['Alteração (h)'] > 0.01, "🟢 Recebeu Horas", "⚪ Intacto"))

st.markdown("---")
st.subheader("📊 4. Resultado do Impacto (Manual)")

# GRÁFICO LADO A LADO
long_df = df_resultado[['Setor', 'Horas Atual (h)', 'Horas Simulada (h)']].melt(id_vars="Setor", var_name="Cenário", value_name="Horas")
fig = px.bar(long_df, x="Setor", y="Horas", color="Cenário", barmode="group", 
             color_discrete_map={"Horas Atual (h)": "#1f77b4", "Horas Simulada (h)": "#00cc96"},
             title="Comparativo de Jornada: Antes vs Depois")

fig.update_layout(xaxis=dict(type="category"), height=450)
fig.add_hline(y=meta, line_dash="dash", line_color="green", annotation_text="Meta (07:20)")
fig.add_hline(y=media_frota, line_dash="dot", line_color="yellow", annotation_text="Média da Frota")
fig.add_hline(y=limite, line_dash="dash", line_color="red", annotation_text="Limite Legal (09:20)")
st.plotly_chart(fig, use_container_width=True)

# TABELA FINAL COM COMPARATIVO ATUAL VS PROJETADO
df_view_final = df_resultado.copy()
df_view_final['Jornada Atual'] = df_view_final['Horas Atual (h)'].apply(format_horas_hhmmss)
df_view_final['Jornada Projetada'] = df_view_final['Horas Simulada (h)'].apply(format_horas_hhmmss)
df_view_final['Alteração'] = df_view_final['Alteração (h)'].apply(lambda x: f"+{format_horas_hhmmss(abs(x))}" if x > 0 else (f"-{format_horas_hhmmss(abs(x))}" if x < 0 else "-"))

cols_exibicao = ['Setor', 'Papel Assumido', 'Alteração', 'Jornada Atual', 'Jornada Projetada', 'Ton Atual', 'Toneladas Simulada', 'Km Atual', 'Km Simulado']
st.dataframe(df_view_final[cols_exibicao].style.format({
    "Ton Atual": "{:.2f} t", "Toneladas Simulada": "{:.2f} t", "Km Atual": "{:.1f} km", "Km Simulado": "{:.1f} km"
}), use_container_width=True, hide_index=True)

# --- SALVAMENTO ---
st.markdown("---")
st.info("⚠️ O cenário que você montou acima está **salvo temporariamente na memória**. Você pode ir olhar o Mapa Operacional e voltar, as regras continuarão aí. Quando tiver certeza, clique abaixo para oficializar.")
if st.button("🚀 Confirmar e Enviar para o Relatório Executivo e Mapa", type="primary", use_container_width=True):
    st.session_state["epico_relatorio_cenario"] = df_resultado.copy()
    st.session_state["epico_relatorio_origem"] = "Simulação Manual Cirúrgica"
    st.success("✅ Cenário guardado e enviado! Agora você pode visualizar o DRE no Relatório Executivo e o visual no Mapa Operacional.")
