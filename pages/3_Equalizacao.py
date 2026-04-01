import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Visão Geral da Operação", page_icon="📊", layout="wide")

st.title("📊 Visão Geral: Estado da Operação")
st.caption("Diagnóstico atual das jornadas, quilometragens e toneladas antes de qualquer simulação.")

if "epico_df" not in st.session_state:
    st.warning("⚠️ Nenhuma base carregada. Vá à página principal.")
    st.stop()

df = st.session_state["epico_df"]
meta = st.session_state.get("jornada_meta", 7.33)

st.markdown("### 🔍 Isole o Cenário")
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

def extrair_horas(hora_str):
    try:
        h, m, s = map(int, str(hora_str).split(':'))
        return h + (m / 60) + (s / 3600)
    except: return np.nan

df_calc = df_filtrado.copy()
df_calc['Horas_Dec'] = df_calc['Horas Trabalhadas'].apply(extrair_horas) if 'Horas Trabalhadas' in df_calc.columns else 7.33
for col in ['Viagens', 'Km Total', 'Toneladas']:
    df_calc[col] = pd.to_numeric(df_calc.get(col, 0), errors='coerce').fillna(0)

df_jornada = df_calc.groupby('Setor').mean(numeric_only=True).reset_index()
df_jornada.rename(columns={'Horas_Dec': 'Jornada Atual'}, inplace=True)
df_jornada['Jornada Atual'] = df_jornada['Jornada Atual'].round(2)

st.markdown("---")
st.markdown(f"### 📋 Indicadores da Operação (Meta: {meta}h)")

df_jornada['Status'] = np.where(df_jornada['Jornada Atual'] > (meta + 0.1), "🔴 Excesso", 
                       np.where(df_jornada['Jornada Atual'] < (meta - 0.1), "🟡 Ocioso", "🟢 Ideal"))

st.dataframe(df_jornada[['Setor', 'Jornada Atual', 'Status', 'Km Total', 'Toneladas', 'Viagens']].style.format({
    "Jornada Atual": "{:.2f}h", "Km Total": "{:.1f} km", "Toneladas": "{:.2f} t", "Viagens": "{:.1f}"
}), use_container_width=True)

st.bar_chart(df_jornada.set_index('Setor')['Jornada Atual'], use_container_width=True)
