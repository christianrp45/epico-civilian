import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Simulador Executivo", page_icon="🛠️", layout="wide")

st.title("🛠️ Simulador Executivo (Manual)")
st.caption("Faça ajustes cirúrgicos transferindo horas de um setor para outro.")

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
st.subheader("Painel de Otimização Manual")

if "transferencias_manuais" not in st.session_state: st.session_state["transferencias_manuais"] = []

c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
with c1: origem = st.selectbox("De (Doador - Perde horas):", options=df_jornada['Setor'].tolist())
with c2: destino = st.selectbox("Para (Receptor - Ganha horas):", options=df_jornada['Setor'].tolist())
with c3: horas = st.number_input("Horas a transferir:", min_value=0.1, step=0.1, value=1.0)
with c4:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➕ Adicionar", use_container_width=True):
        if origem != destino:
            st.session_state["transferencias_manuais"].append({"Doador": origem, "Receptor": destino, "Horas": horas})
            st.rerun()
        else:
            st.error("O Doador e Receptor não podem ser o mesmo!")

df_resultado = df_jornada.copy()
df_resultado['Jornada Projetada'] = df_resultado['Jornada Atual']

if st.session_state["transferencias_manuais"]:
    st.markdown("**Movimentações Planejadas:**")
    st.dataframe(pd.DataFrame(st.session_state["transferencias_manuais"]), use_container_width=True)
    if st.button("🗑️ Limpar Simulação Manual"):
        st.session_state["transferencias_manuais"] = []
        st.rerun()
        
    for t in st.session_state["transferencias_manuais"]:
        idx_d = df_resultado.index[df_resultado['Setor'] == t['Doador']].tolist()[0]
        idx_r = df_resultado.index[df_resultado['Setor'] == t['Receptor']].tolist()[0]
        df_resultado.at[idx_d, 'Jornada Projetada'] -= t['Horas']
        df_resultado.at[idx_r, 'Jornada Projetada'] += t['Horas']

# MATEMÁTICA BLINDADA
df_resultado['Jornada Atual'] = df_resultado['Jornada Atual'].astype(float)
df_resultado['Jornada Projetada'] = df_resultado['Jornada Projetada'].astype(float)
df_resultado['Fator'] = np.where(df_resultado['Jornada Atual'] > 0, df_resultado['Jornada Projetada'] / df_resultado['Jornada Atual'], 1.0)

df_resultado['Km Projetado'] = df_resultado['Km Total'] * df_resultado['Fator']
df_resultado['Ton Projetada'] = df_resultado['Toneladas'] * df_resultado['Fator']
df_resultado['Viagens Simulado'] = np.ceil(df_resultado['Viagens'] * df_resultado['Fator'])
df_resultado = df_resultado.drop(columns=['Fator'])

st.markdown("### 📊 Resultado do Impacto (Manual)")
st.dataframe(df_resultado[['Setor', 'Jornada Atual', 'Jornada Projetada', 'Km Projetado', 'Ton Projetada', 'Viagens Simulado']].style.format({
    "Jornada Atual": "{:.2f}h", "Jornada Projetada": "{:.2f}h", "Km Projetado": "{:.1f} km", "Ton Projetada": "{:.2f} t"
}), use_container_width=True)

st.bar_chart(df_resultado.set_index('Setor')[['Jornada Atual', 'Jornada Projetada']], use_container_width=True)

st.markdown("---")
st.info("Gostou deste cenário? Salve para que ele seja a sua Proposta Oficial no Relatório Executivo.")
if st.button("💾 Salvar MANUAL como Oficial", type="primary", use_container_width=True):
    st.session_state["proposta_oficial"] = df_resultado.copy()
    st.session_state["nome_cenario"] = "Manual"
    st.success("✅ Cenário guardado com sucesso!")
