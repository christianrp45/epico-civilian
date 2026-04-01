import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Equalização de Setores", page_icon="⚖️", layout="wide")

st.title("⚖️ Equalização de Setores (De -> Para)")
st.caption("Ajuste a carga horária dos setores transferindo ruas/horas entre eles.")

# ==========================================
# ⚙️ 1. VALIDAÇÃO DA BASE E CÁLCULO INICIAL
# ==========================================
if "epico_df" not in st.session_state:
    st.warning("⚠️ Nenhuma base carregada. Vá à página principal e carregue o Padrão Ouro.")
    st.stop()

df = st.session_state["epico_df"]
meta_jornada = st.session_state.get("jornada_meta", 7.33)

# Função para garantir que temos as horas em decimal para fazer contas
def extrair_horas_decimais(hora_str):
    try:
        h, m, s = map(int, str(hora_str).split(':'))
        return h + (m / 60) + (s / 3600)
    except:
        return np.nan

# Prepara a base de cálculo (Jornada Atual)
df_calc = df.copy()
if 'Horas Trabalhadas' in df_calc.columns:
    df_calc['Horas_Dec'] = df_calc['Horas Trabalhadas'].apply(extrair_horas_decimais)
else:
    df_calc['Horas_Dec'] = 7.33 # Fallback se não achar a coluna

# Calcula a média da jornada por setor
df_jornada = df_calc.groupby('Setor')['Horas_Dec'].mean().reset_index()
df_jornada.rename(columns={'Horas_Dec': 'Jornada Atual'}, inplace=True)
df_jornada['Jornada Atual'] = df_jornada['Jornada Atual'].round(2)

# ==========================================
# 🧮 2. MOTOR DE TRANSFERÊNCIA AUTOMÁTICA (COM TRAVA DE 30 MIN)
# ==========================================
def calcular_transferencias_inteligentes(df_base, meta, limite_minimo=0.5):
    """Calcula transferências bloqueando pedaços pequenos (fracionamento)."""
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
            
            # TRAVA ANTI-FRACIONAMENTO (Só passa se for > 0.5h)
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
# 🛠️ 3. INTERFACE DE ABAS (MANUAL vs AUTOMÁTICA)
# ==========================================
tab1, tab2 = st.tabs(["🛠️ Otimização
