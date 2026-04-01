import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Equalização de Setores", page_icon="⚖️", layout="wide")

st.title("⚖️ Equalização de Setores (De -> Para)")
st.caption("Ajuste a carga horária dos setores transferindo ruas/horas entre eles.")

# ==========================================
# ⚙️ 1. VALIDAÇÃO E FILTROS DO CENÁRIO
# ==========================================
if "epico_df" not in st.session_state:
    st.warning("⚠️ Nenhuma base carregada. Vá à página principal e carregue o Padrão Ouro.")
    st.stop()

df = st.session_state["epico_df"]
meta_jornada = st.session_state.get("jornada_meta", 7.33)

st.markdown("### 🔍 1. Isole o Cenário")
st.info("Filtre o turno e o dia da semana para não misturar operações incompatíveis.")

c_turno, c_dia = st.columns(2)
with c_turno:
    turnos_disp = ["Todos"] + list(df['Turno'].dropna().unique())
    idx_turno = turnos_disp.index("DIURNO") if "DIURNO" in turnos_disp else 0
    turno_escolhido = st.selectbox("Turno:", options=turnos_disp, index=idx_turno)

with c_dia:
    dias_disp = ["Todos"] + list(df['Dia da Semana'].dropna().unique())
    idx_dia = dias_disp.index("Segunda-feira") if "Segunda-feira" in dias_disp else 0
    dia_escolhido = st.selectbox("Dia da Semana:", options=dias_disp, index=idx_dia)

df_filtrado = df.copy()
if turno_escolhido != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Turno'] == turno_escolhido]
if dia_escolhido != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Dia da Semana'] == dia_escolhido]

if df_filtrado.empty:
    st.warning("⚠️ Nenhum dado encontrado para esta combinação de Turno e Dia. Altere os filtros acima.")
    st.stop()

# ==========================================
# 🧮 2. CÁLCULO DA JORNADA ATUAL COM MÉTRICAS
# ==========================================
def extrair_horas_decimais(hora_str):
    try:
        h, m, s = map(int, str(hora_str).split(':'))
        return h + (m / 60) + (s / 3600)
    except:
        return np.nan

df_calc = df_filtrado.copy()
if 'Horas Trabalhadas' in df_calc.columns:
    df_calc['Horas_Dec'] = df_calc['Horas Trabalhadas'].apply(extrair_horas_decimais)
else:
    df_calc['Horas_Dec'] = 7.33

# Garante que os valores numéricos sejam tratados como float para a média
for col in ['Viagens', 'Km Total', 'Toneladas']:
    if col in df_calc.columns:
        df_calc[col] = pd.to_numeric(df_calc[col], errors='coerce').fillna(0)
    else:
        df_calc[col] = 0

df_jornada = df_calc.groupby('Setor').agg({
    'Horas_Dec': 'mean',
    'Viagens': 'mean',
    'Km Total': 'mean',
    'Toneladas': 'mean'
}).reset_index()

df_jornada.rename(columns={'Horas_Dec': 'Jornada Atual'}, inplace=True)
df_jornada['Jornada Atual'] = df_jornada['Jornada Atual'].round(2)

with st.expander("📊 Ver Planilha do Estado Atual da Operação", expanded=False):
    st.dataframe(df_jornada.style.format({
        "Jornada Atual": "{:.2f}h", "Km Total": "{:.1f} km", "Toneladas": "{:.2f} t"
    }), use_container_width=True)

# ==========================================
# 🤖 3. MOTOR DE TRANSFERÊNCIA AUTOMÁTICA
# ==========================================
def calcular_transferencias_inteligentes(df_base, meta, limite_minimo=0.5):
    doadores = df_base[df_base['Jornada Atual'] > (meta + 0.1)].copy()
    receptores = df_base[df_base['Jornada Atual'] < (meta - 0.1)].copy()
    
    doadores['Excesso'] = doadores['Jornada Atual'] - meta
    receptores['Deficit'] = meta - receptores['Jornada Atual']
    
    doadores = doadores.sort_values(by='Excesso', ascending=False)
    receptores = receptores.sort_values(by='Deficit', ascending=False)
    
    transferencias = []
    
    for i, doador in doadores.iterrows():
        excesso_disp = doador['Excesso']
        for j, receptor in receptores.iterrows():
            if excesso_disp <= 0: break
            
            deficit_nec = receptor['Deficit']
            if deficit_nec <= 0: continue
            
            qtd_transferir = min(excesso_disp, deficit_nec)
            
            if qtd_transferir >= limite_minimo:
                transferencias.append({
                    'Doador (Origem)': doador['Setor'],
                    'Receptor (Destino)': receptor['Setor'],
                    'Horas Transferidas': round(qtd_transferir, 2)
                })
                excesso_disp -= qtd_transferir
                receptores.at[j, 'Deficit'] -= qtd_transferir
                
    return pd.DataFrame(transferencias)

# ==========================================
# 🧮 4. FUNÇÃO DE PROPORÇÃO (A CORREÇÃO MATEMÁTICA)
# ==========================================
def aplicar_proporcoes(df_resultado):
    """Ajusta Km, Toneladas e Viagens proporcionalmente à mudança de Horas"""
    df_resultado['Fator'] = df_resultado['Jornada Projetada'] / df_resultado['Jornada Atual']
    
    # Se não mexeu (Fator == 1), copia o real. Se mexeu, aplica o fator.
    df_resultado['Km Projetado'] = np.where(df_resultado['Fator'] == 1.0, df_resultado['Km Total'], df_resultado['Km Total'] * df_resultado['Fator'])
    df_resultado['Toneladas Projetadas'] = np.where(df_resultado['Fator'] == 1.0, df_resultado['Toneladas'], df_resultado['Toneladas'] * df_resultado['Fator'])
    df_resultado['Viagens Simulado'] = np.where(df_resultado['Fator'] == 1.0, df_resultado['Viagens'], np.ceil(df_resultado['Viagens'] * df_resultado['Fator']))
    
    return df_resultado.drop(columns=['Fator'])

# ==========================================
# 🛠️ 5. INTERFACE DE ABAS
# ==========================================
tab1, tab2 = st.tabs(["🛠️ Otimização Manual", "🤖 Simulação Automática"])

df_resultado_manual = None
df_resultado_auto = None

with tab1:
    st.subheader("Painel de Otimização Manual")
    
    if "transferencias_manuais" not in st.session_state:
        st.session_state["transferencias_manuais"] = []

    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
    with c1:
        origem = st.selectbox("De (Doador):", options=df_jornada['Setor'].tolist(), key="origem_manual")
    with c2:
        destino = st.selectbox("Para (Receptor):", options=df_jornada['Setor'].tolist(), key="destino_manual")
    with c3:
        horas = st.number_input("Horas a transferir:", min_value=0.1, step=0.1, value=1.0)
    with c4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Adicionar
