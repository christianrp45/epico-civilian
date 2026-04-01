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
    df_resultado['Fator'] = df_resultado['Jornada Projetada'] / df_resultado['Jornada Atual']
    
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
        if st.button("➕ Adicionar", use_container_width=True):
            if origem == destino:
                st.error("Origem e Destino devem ser diferentes.")
            else:
                st.session_state["transferencias_manuais"].append({
                    "Doador (Origem)": origem,
                    "Receptor (Destino)": destino,
                    "Horas Transferidas": horas
                })
                st.rerun()

    df_resultado_manual = df_jornada.copy()
    df_resultado_manual['Jornada Projetada'] = df_resultado_manual['Jornada Atual']

    if st.session_state["transferencias_manuais"]:
        st.markdown("**Movimentações Planejadas:**")
        df_trans_manual = pd.DataFrame(st.session_state["transferencias_manuais"])
        st.dataframe(df_trans_manual, use_container_width=True)
        
        if st.button("🗑️ Limpar Movimentações Manuais"):
            st.session_state["transferencias_manuais"] = []
            st.rerun()
            
        for t in st.session_state["transferencias_manuais"]:
            idx_doador = df_resultado_manual.index[df_resultado_manual['Setor'] == t['Doador (Origem)']].tolist()[0]
            idx_receptor = df_resultado_manual.index[df_resultado_manual['Setor'] == t['Receptor (Destino)']].tolist()[0]
            
            df_resultado_manual.at[idx_doador, 'Jornada Projetada'] -= t['Horas Transferidas']
            df_resultado_manual.at[idx_receptor, 'Jornada Projetada'] += t['Horas Transferidas']

    df_resultado_manual = aplicar_proporcoes(df_resultado_manual)

    st.markdown("---")
    st.markdown("### 📊 Resultado do Impacto (Manual)")
    st.dataframe(df_resultado_manual.style.format({
        "Jornada Atual": "{:.2f}h", "Jornada Projetada": "{:.2f}h",
        "Km Projetado": "{:.1f} km", "Toneladas Projetadas": "{:.2f} t"
    }), use_container_width=True)
    st.bar_chart(df_resultado_manual.set_index('Setor')[['Jornada Atual', 'Jornada Projetada']], use_container_width=True)

with tab2:
    st.subheader("Motor de Inteligência Artificial")
    st.write(f"A tentar nivelar todos os setores para a meta de **{meta_jornada} horas**.")
    st.caption("Regra ativa: O robô não faz transferências menores que 30 minutos (0.5h).")
    
    df_trans_auto = calcular_transferencias_inteligentes(df_jornada, meta_jornada)
    df_resultado_auto = df_jornada.copy()
    df_resultado_auto['Jornada Projetada'] = df_resultado_auto['Jornada Atual']
    
    if df_trans_auto.empty:
        st.success("A operação já está equilibrada dentro da margem de tolerância!")
    else:
        st.markdown("**Transferências Sugeridas pelo Robô:**")
        st.dataframe(df_trans_auto, use_container_width=True)
        
        for _, t in df_trans_auto.iterrows():
            idx_doador = df_resultado_auto.index[df_resultado_auto['Setor'] == t['Doador (Origem)']].tolist()[0]
            idx_receptor = df_resultado_auto.index[df_resultado_auto['Setor'] == t['Receptor (Destino)']].tolist()[0]
            
            df_resultado_auto.at[idx_doador, 'Jornada Projetada'] -= t['Horas Transferidas']
            df_resultado_auto.at[idx_receptor, 'Jornada Projetada'] += t['Horas Transferidas']

    df_resultado_auto = aplicar_proporcoes(df_resultado_auto)

    st.markdown("---")
    st.markdown("### 📊 Resultado do Impacto (Automático)")
    st.dataframe(df_resultado_auto.style.format({
        "Jornada Atual": "{:.2f}h", "Jornada Projetada": "{:.2f}h",
        "Km Projetado": "{:.1f} km", "Toneladas Projetadas": "{:.2f} t"
    }), use_container_width=True)
    st.bar_chart(df_resultado_auto.set_index('Setor')[['Jornada Atual', 'Jornada Projetada']], use_container_width=True)

# ==========================================
# 💾 6. PAINEL DE GESTÃO PARA O RELATÓRIO
# ==========================================
st.markdown("---")
st.header("💾 Gestão de Cenários e Relatório Executivo")
st.caption("Salve suas simulações e escolha qual cenário vai para a Visão Executiva.")

if "proposta_manual" not in st.session_state: st.session_state["proposta_manual"] = None
if "proposta_automatica" not in st.session_state: st.session_state["proposta_automatica"] = None
if "cenario_oficial" not in st.session_state: st.session_state["cenario_oficial"] = "Atual"

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("### 🛠️ Proposta Manual")
    if st.button("💾 Salvar Proposta Manual", use_container_width=True):
        st.session_state["proposta_manual"] = df_resultado_manual.copy() 
        st.success("Salva com sucesso!")
        
    if st.session_state["proposta_manual"] is not None:
        st.success("✅ Cenário Manual na memória.")
        if st.button("🗑️ Limpar Manual", use_container_width=True):
            st.session_state["proposta_manual"] = None
            if st.session_state["cenario_oficial"] == "Manual": st.session_state["cenario_oficial"] = "Atual"
            st.rerun()

with c2:
    st.markdown("### 🤖 Proposta Automática")
    if st.button("💾 Salvar Proposta Automática", use_container_width=True):
        st.session_state["proposta_automatica"] = df_resultado_auto.copy()
        st.success("Salva com sucesso!")
            
    if st.session_state["proposta_automatica"] is not None:
        st.success("✅ Cenário Automático na memória.")
        if st.button("🗑️ Limpar Automática", use_container_width=True):
            st.session_state["proposta_automatica"] = None
            if st.session_state["cenario_oficial"] == "Automática": st.session_state["cenario_oficial"] = "Atual"
            st.rerun()

with c3:
    st.markdown("### 📑 Enviar para Relatório")
    st.info("Escolha qual cenário gerar os gráficos na Visão Executiva.")
    
    opcoes_relatorio = ["Atual"]
    if st.session_state["proposta_manual"] is not None: opcoes_relatorio.append("Manual")
    if st.session_state["proposta_automatica"] is not None: opcoes_relatorio.append("Automática")
    
    index_atual = opcoes_relatorio.index(st.session_state["cenario_oficial"]) if st.session_state["cenario_oficial"] in opcoes_relatorio else 0
    
    escolha = st.selectbox(
        "Selecione o cenário oficial:", 
        options=opcoes_relatorio, 
        index=index_atual
    )
    
    if escolha != st.session_state["cenario_oficial"]:
        st.session_state["cenario_oficial"] = escolha
        st.success(f"Cenário **{escolha}** ativado no Relatório!")
        st.rerun()
