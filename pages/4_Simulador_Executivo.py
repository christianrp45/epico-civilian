import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from kpis import format_horas_hhmmss, format_number_br

st.set_page_config(page_title="Simulador Executivo", page_icon="🛠️", layout="wide")

st.title("🛠️ Simulador Executivo (Manual)")
st.caption("Consulte o balanço de necessidades e faça ajustes cirúrgicos transferindo horas entre setores.")

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

# --- PREPARAÇÃO E LIMPEZA DE DADOS ---
def extrair_horas(hora_str):
    try:
        h, m, s = map(int, str(hora_str).split(':'))
        return h + (m / 60) + (s / 3600)
    except: return np.nan

df_calc = df_filtrado.copy()
df_calc['Setor'] = pd.to_numeric(df_calc['Setor'], errors='coerce').fillna(0).astype(int).astype(str)
df_calc['Horas_Dec'] = df_calc['Horas Trabalhadas'].apply(extrair_horas) if 'Horas Trabalhadas' in df_calc.columns else 7.33
for col in ['Viagens', 'Km Total', 'Toneladas']:
    df_calc[col] = pd.to_numeric(df_calc.get(col, 0), errors='coerce').fillna(0)

df_jornada = df_calc.groupby('Setor').mean(numeric_only=True).reset_index()

if df_jornada['Toneladas'].max() > 100:
    df_jornada['Toneladas'] = df_jornada['Toneladas'] / 1000

df_jornada.rename(columns={'Horas_Dec': 'Jornada Atual'}, inplace=True)
df_jornada['Jornada Atual'] = df_jornada['Jornada Atual'].round(2)

# --- BALANÇO DE NECESSIDADES ---
st.markdown("---")
st.subheader("📋 2. Balanço de Necessidades (Antes da Simulação)")

media_frota = df_jornada['Jornada Atual'].mean()
st.info(f"Onde precisamos mexer? Média atual da frota: **{format_horas_hhmmss(media_frota)}** (Limite legal p/ passivo: 09:20:00)")

df_balanco = df_jornada.copy()
df_balanco['Desvio'] = df_balanco['Jornada Atual'] - media_frota
df_balanco['Status'] = np.where(df_balanco['Desvio'] > 0.15, "🚩 Doador (Acima da Média)", 
                       np.where(df_balanco['Desvio'] < -0.15, "✅ Recebedor (Abaixo da Média)", "🟢 Equilibrado"))

df_bal_view = df_balanco.copy()
df_bal_view['Jornada Atual'] = df_bal_view['Jornada Atual'].apply(format_horas_hhmmss)
df_bal_view['Desvio da Média'] = df_bal_view['Desvio'].apply(lambda x: f"+{format_horas_hhmmss(abs(x))}" if x > 0 else f"-{format_horas_hhmmss(abs(x))}")

df_bal_view['Toneladas'] = df_bal_view['Toneladas'].round(2)
df_bal_view['Km Total'] = df_bal_view['Km Total'].round(2)

st.dataframe(df_bal_view[['Setor', 'Jornada Atual', 'Status', 'Desvio da Média', 'Toneladas', 'Km Total']].style.apply(lambda x: [
    'background-color: #ffcccc' if v == "🚩 Doador (Acima da Média)" else ('background-color: #e6ffe6' if v == "✅ Recebedor (Abaixo da Média)" else '') for v in x
], axis=1, subset=['Status']), use_container_width=True, hide_index=True)


# --- MOTOR DE TRANSFERÊNCIAS DINÂMICO ---
st.markdown("---")
st.subheader("⚙️ 3. Otimização Manual Múltipla (De -> Para)")
st.caption("Adicione quantas linhas precisar. O gráfico calculará o impacto de todas elas em tempo real.")

# Inicializa o contador de linhas na memória
if "num_linhas_manuais" not in st.session_state: 
    st.session_state["num_linhas_manuais"] = 1

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

# Gera os campos de seleção dinamicamente
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
df_resultado['Jornada Projetada'] = df_resultado['Jornada Atual']

# Aplica os cálculos na hora
if transferencias_validas:
    st.success(f"**{len(transferencias_validas)} regra(s) ativa(s)! Veja o resultado projetado abaixo.**")
    for t in transferencias_validas:
        idx_d = df_resultado.index[df_resultado['Setor'] == t['Doador']].tolist()[0]
        idx_r = df_resultado.index[df_resultado['Setor'] == t['Receptor']].tolist()[0]
        df_resultado.at[idx_d, 'Jornada Projetada'] -= t['Horas']
        df_resultado.at[idx_r, 'Jornada Projetada'] += t['Horas']
else:
    st.info("Preencha o Doador e o Receptor acima para ver a simulação acontecendo.")

# --- FÍSICA PROPORCIONAL BLINDADA ---
df_resultado['Fator'] = np.where(df_resultado['Jornada Atual'] > 0, df_resultado['Jornada Projetada'] / df_resultado['Jornada Atual'], 1.0)
df_resultado['Km Projetado'] = df_resultado['Km Total'] * df_resultado['Fator']
df_resultado['Ton Projetada'] = df_resultado['Toneladas'] * df_resultado['Fator']
df_resultado['Viagens Simulado'] = np.ceil(df_resultado['Viagens'] * df_resultado['Fator'])

# --- DIAGNÓSTICO PÓS-SIMULAÇÃO (O QUE MUDOU?) ---
df_resultado['Alteração (h)'] = df_resultado['Jornada Projetada'] - df_resultado['Jornada Atual']
df_resultado['Papel Assumido'] = np.where(df_resultado['Alteração (h)'] < -0.01, "🔴 Doou Horas", 
                                 np.where(df_resultado['Alteração (h)'] > 0.01, "🟢 Recebeu Horas", "⚪ Intacto"))

st.markdown("---")
st.subheader("📊 4. Resultado do Impacto (Manual)")

# GRÁFICO LADO A LADO COM LINHAS INDICATIVAS
long_df = df_resultado[['Setor', 'Jornada Atual', 'Jornada Projetada']].melt(id_vars="Setor", var_name="Cenário", value_name="Horas")
fig = px.bar(long_df, x="Setor", y="Horas", color="Cenário", barmode="group", 
             color_discrete_map={"Jornada Atual": "#1f77b4", "Jornada Projetada": "#00cc96"},
             title="Comparativo de Jornada: Antes vs Depois")

fig.update_layout(xaxis=dict(type="category"), height=450)
fig.add_hline(y=meta, line_dash="dash", line_color="green", annotation_text="Meta (07:20)")
fig.add_hline(y=media_frota, line_dash="dot", line_color="yellow", annotation_text="Média da Frota")
fig.add_hline(y=limite, line_dash="dash", line_color="red", annotation_text="Limite Legal (09:20)")
st.plotly_chart(fig, use_container_width=True)

# TABELA FINAL LIMPA
df_view_final = df_resultado.copy()
df_view_final['Jornada Atual'] = df_view_final['Jornada Atual'].apply(format_horas_hhmmss)
df_view_final['Jornada Projetada'] = df_view_final['Jornada Projetada'].apply(format_horas_hhmmss)
df_view_final['Alteração'] = df_view_final['Alteração (h)'].apply(lambda x: f"+{format_horas_hhmmss(abs(x))}" if x > 0 else (f"-{format_horas_hhmmss(abs(x))}" if x < 0 else "-"))

cols_exibicao = ['Setor', 'Papel Assumido', 'Alteração', 'Jornada Atual', 'Jornada Projetada', 'Km Projetado', 'Ton Projetada']
st.dataframe(df_view_final[cols_exibicao].style.format({
    "Km Projetado": "{:.1f} km", "Ton Projetada": "{:.2f} t"
}), use_container_width=True, hide_index=True)

# --- SALVAMENTO ---
st.markdown("---")
st.info("Gostou deste cenário? Salve para que ele seja a sua Proposta Oficial no Relatório Executivo.")
if st.button("💾 Salvar MANUAL como Oficial", type="primary", use_container_width=True):
    st.session_state["epico_relatorio_cenario"] = df_resultado.copy()
    st.session_state["epico_relatorio_origem"] = "Simulação Manual Cirúrgica"
    st.success("✅ Cenário guardado com sucesso! A página de Relatório e o Mapa vão usar estes dados agora.")
