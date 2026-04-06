import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from kpis import format_horas_hhmmss

st.set_page_config(page_title="Simulador Executivo", page_icon="🛠️", layout="wide")

st.title("🛠️ Simulador Executivo (Manual)")
st.caption("Suas regras ficam salvas na memória. Navegue pelo sistema e, quando pronto, envie o cenário para o Relatório.")

# --- CONFIGURAÇÕES E DADOS ---
if "epico_df" not in st.session_state:
    st.warning("⚠️ Nenhuma base carregada. Vá à página principal.")
    st.stop()

df = st.session_state["epico_df"]
meta = st.session_state.get("meta_operacional", 7 + 20/60)
limite = 9 + 20/60 

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

# --- PREPARAÇÃO E LIMPEZA DE DADOS (MÉTODO SIMPLES E CORRETO) ---
def extrair_horas(hora_str):
    try:
        h, m, s = map(int, str(hora_str).split(':'))
        return h + (m / 60) + (s / 3600)
    except: return np.nan

df_calc = df_filtrado.copy()
df_calc['Setor'] = pd.to_numeric(df_calc['Setor'], errors='coerce').fillna(0).astype(int).astype(str)
df_calc['Horas_Dec'] = df_calc['Horas Trabalhadas'].apply(extrair_horas) if 'Horas Trabalhadas' in df_calc.columns else 7.33

# Força a existência das colunas, sem quebrar os números que já estão corretos
colunas_numericas = ['Viagens', 'Km Total', 'Toneladas', 'Combustível', 'Km Improdutivo', 'Produtividade (t/h)']
for col in colunas_numericas:
    if col not in df_calc.columns:
        df_calc[col] = 0.0
    else:
        # Se por acaso vier como texto com vírgula, arruma. Se já for número, ignora.
        if df_calc[col].dtype == 'object':
            df_calc[col] = df_calc[col].astype(str).str.replace(',', '.', regex=False)
        df_calc[col] = pd.to_numeric(df_calc[col], errors='coerce').fillna(0.0)

df_jornada = df_calc.groupby('Setor').mean(numeric_only=True).reset_index()

if df_jornada['Toneladas'].max() > 100:
    df_jornada['Toneladas'] = df_jornada['Toneladas'] / 1000

# Renomeia o 'Km Total' para 'Km Atual' para padronizar a tabela
df_jornada.rename(columns={
    'Horas_Dec': 'Horas Atual (h)', 'Km Total': 'Km Atual', 'Toneladas': 'Ton Atual',
    'Combustível': 'Combustível Atual', 'Viagens': 'Viagens Atual'
}, inplace=True)

df_jornada['Horas Atual (h)'] = df_jornada['Horas Atual (h)'].round(2)
df_jornada['Viagens Atual'] = np.ceil(df_jornada['Viagens Atual']) 
df_jornada['Capacidade (t)'] = 9.5 

# --- BALANÇO DE NECESSIDADES ---
st.markdown("---")
st.subheader("📋 2. Balanço de Necessidades (Antes da Simulação)")

media_frota = df_jornada['Horas Atual (h)'].mean()
st.info(f"Média atual da frota: **{format_horas_hhmmss(media_frota)}** (Limite legal: 09:20:00)")

df_balanco = df_jornada.copy()
df_balanco['Desvio'] = df_balanco['Horas Atual (h)'] - media_frota
df_balanco['Status'] = np.where(df_balanco['Desvio'] > 0.15, "🚩 Doador (Acima da Média)", 
                       np.where(df_balanco['Desvio'] < -0.15, "✅ Recebedor (Abaixo da Média)", "🟢 Equilibrado"))

df_bal_view = df_balanco.copy()
df_bal_view['Horas Atual'] = df_bal_view['Horas Atual (h)'].apply(format_horas_hhmmss)
df_bal_view['Desvio da Média'] = df_bal_view['Desvio'].apply(lambda x: f"+{format_horas_hhmmss(abs(x))}" if x > 0 else f"-{format_horas_hhmmss(abs(x))}")

st.dataframe(df_bal_view[['Setor', 'Horas Atual', 'Status', 'Desvio da Média', 'Ton Atual', 'Km Atual']].style.format({
    "Ton Atual": "{:.2f} t", "Km Atual": "{:.1f} km"
}).apply(lambda x: ['background-color: #ffcccc' if v == "🚩 Doador (Acima da Média)" else ('background-color: #e6ffe6' if v == "✅ Recebedor (Abaixo da Média)" else '') for v in x], axis=1, subset=['Status']), use_container_width=True, hide_index=True)


# --- OTIMIZAÇÃO MANUAL (MÚLTIPLAS LINHAS COM MEMÓRIA) ---
st.markdown("---")
st.subheader("⚙️ 3. Otimização Manual Múltipla (De -> Para)")

if "regras_dinamicas" not in st.session_state:
    st.session_state["regras_dinamicas"] = [{"doador": "Nenhum", "receptor": "Nenhum", "horas": 1.0}]

b1, b2, b3 = st.columns([2, 2, 6])
with b1:
    if st.button("➕ Adicionar linha", use_container_width=True):
        st.session_state["regras_dinamicas"].append({"doador": "Nenhum", "receptor": "Nenhum", "horas": 1.0})
        st.rerun()
with b2:
    if st.button("➖ Remover linha", use_container_width=True):
        if len(st.session_state["regras_dinamicas"]) > 1:
            st.session_state["regras_dinamicas"].pop()
            st.rerun()
with b3:
    if st.button("🗑️ Limpar Tudo", use_container_width=False):
        st.session_state["regras_dinamicas"] = [{"doador": "Nenhum", "receptor": "Nenhum", "horas": 1.0}]
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

opcoes_setores = ["Nenhum"] + df_jornada['Setor'].tolist()
transferencias_validas = []

for i, regra in enumerate(st.session_state["regras_dinamicas"]):
    c1, c2, c3 = st.columns(3)
    
    def update_rule(index=i):
        st.session_state["regras_dinamicas"][index]["doador"] = st.session_state[f"d_{index}"]
        st.session_state["regras_dinamicas"][index]["receptor"] = st.session_state[f"r_{index}"]
        st.session_state["regras_dinamicas"][index]["horas"] = st.session_state[f"h_{index}"]

    idx_d = opcoes_setores.index(regra["doador"]) if regra["doador"] in opcoes_setores else 0
    idx_r = opcoes_setores.index(regra["receptor"]) if regra["receptor"] in opcoes_setores else 0

    with c1: st.selectbox(f"Doador (Perde horas) - Linha {i+1}:", options=opcoes_setores, index=idx_d, key=f"d_{i}", on_change=update_rule)
    with c2: st.selectbox(f"Receptor (Ganha horas) - Linha {i+1}:", options=opcoes_setores, index=idx_r, key=f"r_{i}", on_change=update_rule)
    with c3: st.number_input(f"Horas a transferir - Linha {i+1}:", min_value=0.1, step=0.1, value=float(regra["horas"]), key=f"h_{i}", on_change=update_rule)

    d, r, h = st.session_state["regras_dinamicas"][i]["doador"], st.session_state["regras_dinamicas"][i]["receptor"], st.session_state["regras_dinamicas"][i]["horas"]
    if d != "Nenhum" and r != "Nenhum":
        if d != r: transferencias_validas.append({"Doador": d, "Receptor": r, "Horas": h})
        else: st.error(f"⚠️ Linha {i+1}: Doador e Receptor não podem ser o mesmo setor.")

# --- FÍSICA E CÁLCULOS ---
df_resultado = df_jornada.copy()
df_resultado['Horas Simulada (h)'] = df_resultado['Horas Atual (h)']

if transferencias_validas:
    for t in transferencias_validas:
        df_resultado.loc[df_resultado['Setor'] == t['Doador'], 'Horas Simulada (h)'] -= t['Horas']
        df_resultado.loc[df_resultado['Setor'] == t['Receptor'], 'Horas Simulada (h)'] += t['Horas']

df_resultado['Fator'] = np.where(df_resultado['Horas Atual (h)'] > 0, df_resultado['Horas Simulada (h)'] / df_resultado['Horas Atual (h)'], 1.0)

df_resultado['Km Simulado'] = df_resultado['Km Atual'] * df_resultado['Fator']
df_resultado['Toneladas Simulada'] = df_resultado['Ton Atual'] * df_resultado['Fator']
df_resultado['Combustível Simulado'] = df_resultado['Combustível Atual'] * df_resultado['Fator']
df_resultado['Km Improdutivo Simulado'] = df_resultado['Km Improdutivo'] * df_resultado['Fator']

df_resultado['Viagens Projetadas'] = np.where(
    abs(df_resultado['Fator'] - 1.0) < 0.001, 
    df_resultado['Viagens Atual'], 
    np.maximum(1, np.ceil(df_resultado['Toneladas Simulada'] / df_resultado['Capacidade (t)']))
)

df_resultado['Alteração (h)'] = df_resultado['Horas Simulada (h)'] - df_resultado['Horas Atual (h)']
df_resultado['Papel Assumido'] = np.where(df_resultado['Alteração (h)'] < -0.01, "🔴 Doou", np.where(df_resultado['Alteração (h)'] > 0.01, "🟢 Recebeu", "⚪ Intacto"))

# --- RESULTADOS ---
st.markdown("---")
st.subheader("📊 4. Resultado do Impacto (Manual)")

long_df = df_resultado[['Setor', 'Horas Atual (h)', 'Horas Simulada (h)']].melt(id_vars="Setor", var_name="Cenário", value_name="Horas")
fig = px.bar(long_df, x="Setor", y="Horas", color="Cenário", barmode="group", color_discrete_map={"Horas Atual (h)": "#1f77b4", "Horas Simulada (h)": "#00cc96"})
fig.update_layout(xaxis=dict(type="category"), height=450)
fig.add_hline(y=meta, line_dash="dash", line_color="green", annotation_text="Meta")
fig.add_hline(y=media_frota, line_dash="dot", line_color="yellow", annotation_text="Média da Frota")
fig.add_hline(y=limite, line_dash="dash", line_color="red", annotation_text="Limite Legal")
st.plotly_chart(fig, use_container_width=True)

df_view_final = df_resultado.copy()
df_view_final['Jornada Atual'] = df_view_final['Horas Atual (h)'].apply(format_horas_hhmmss)
df_view_final['Jornada Projetada'] = df_view_final['Horas Simulada (h)'].apply(format_horas_hhmmss)
df_view_final['Alteração'] = df_view_final['Alteração (h)'].apply(lambda x: f"+{format_horas_hhmmss(abs(x))}" if x > 0 else (f"-{format_horas_hhmmss(abs(x))}" if x < 0 else "-"))

cols_exibicao = ['Setor', 'Papel Assumido', 'Alteração', 'Jornada Atual', 'Jornada Projetada', 'Ton Atual', 'Toneladas Simulada', 'Km Atual', 'Km Simulado', 'Viagens Atual', 'Viagens Projetadas']
st.dataframe(df_view_final[cols_exibicao].style.format({
    "Ton Atual": "{:.2f} t", "Toneladas Simulada": "{:.2f} t", "Km Atual": "{:.1f} km", "Km Simulado": "{:.1f} km", "Viagens Atual": "{:.0f}", "Viagens Projetadas": "{:.0f}"
}), use_container_width=True, hide_index=True)

st.markdown("---")
st.info("💡 Suas regras estão salvas. Você pode olhar o Mapa Operacional e voltar. Quando finalizar a simulação, clique abaixo para oficializar o DRE e os Mapas.")
if st.button("🚀 Confirmar e Enviar para o Relatório Executivo e Mapa", type="primary", use_container_width=True):
    st.session_state["epico_relatorio_cenario"] = df_resultado.copy()
    st.session_state["epico_relatorio_origem"] = "Simulação Manual Cirúrgica"
    st.success("✅ Cenário enviado com sucesso!")
