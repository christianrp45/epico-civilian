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

def extrair_horas_decimais(hora_str):
    try:
        h, m, s = map(int, str(hora_str).split(':'))
        return h + (m / 60) + (s / 3600)
    except:
        return np.nan

df_calc = df.copy()
if 'Horas Trabalhadas' in df_calc.columns:
    df_calc['Horas_Dec'] = df_calc['Horas Trabalhadas'].apply(extrair_horas_decimais)
else:
    df_calc['Horas_Dec'] = 7.33

df_jornada = df_calc.groupby('Setor')['Horas_Dec'].mean().reset_index()
df_jornada.rename(columns={'Horas_Dec': 'Jornada Atual'}, inplace=True)
df_jornada['Jornada Atual'] = df_jornada['Jornada Atual'].round(2)

# Mostra o Estado Inicial da Operação no topo
with st.expander("📊 Ver Planilha do Estado Atual da Operação", expanded=False):
    st.dataframe(df_jornada.style.format({"Jornada Atual": "{:.2f}h"}), use_container_width=True)

# ==========================================
# 🧮 2. MOTOR DE TRANSFERÊNCIA AUTOMÁTICA
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
# 🛠️ 3. INTERFACE DE ABAS
# ==========================================
tab1, tab2 = st.tabs(["🛠️ Otimização Manual", "🤖 Simulação Automática"])

df_resultado_manual = None
df_resultado_auto = None

# --- ABA 1: MANUAL ---
with tab1:
    st.subheader("Painel de Otimização Manual")
    st.info("Escolha de qual setor tirar horas e para qual setor enviar.")
    
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

    # Base projetada inicial
    df_resultado_manual = df_jornada.copy()
    df_resultado_manual['Jornada Projetada'] = df_resultado_manual['Jornada Atual']

    if st.session_state["transferencias_manuais"]:
        st.markdown("**Movimentações Planejadas:**")
        df_trans_manual = pd.DataFrame(st.session_state["transferencias_manuais"])
        st.dataframe(df_trans_manual, use_container_width=True)
        
        if st.button("🗑️ Limpar Movimentações Manuais"):
            st.session_state["transferencias_manuais"] = []
            st.rerun()
            
        # Aplica os cálculos
        for t in st.session_state["transferencias_manuais"]:
            idx_doador = df_resultado_manual.index[df_resultado_manual['Setor'] == t['Doador (Origem)']].tolist()[0]
            idx_receptor = df_resultado_manual.index[df_resultado_manual['Setor'] == t['Receptor (Destino)']].tolist()[0]
            
            df_resultado_manual.at[idx_doador, 'Jornada Projetada'] -= t['Horas Transferidas']
            df_resultado_manual.at[idx_receptor, 'Jornada Projetada'] += t['Horas Transferidas']

    # Mostra a Planilha Final e o Gráfico na Aba Manual
    st.markdown("---")
    st.markdown("### 📊 Resultado do Impacto (Manual)")
    st.dataframe(df_resultado_manual.style.format({"Jornada Atual": "{:.2f}h", "Jornada Projetada": "{:.2f}h"}), use_container_width=True)
    st.caption("Gráfico Comparativo: A barra mais clara é como estava, a mais escura é a sua projeção.")
    st.bar_chart(df_resultado_manual.set_index('Setor')[['Jornada Atual', 'Jornada Projetada']], use_container_width=True)

# --- ABA 2: AUTOMÁTICA ---
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

    # Mostra a Planilha Final e o Gráfico na Aba Automática
    st.markdown("---")
    st.markdown("### 📊 Resultado do Impacto (Automático)")
    st.dataframe(df_resultado_auto.style.format({"Jornada Atual": "{:.2f}h", "Jornada Projetada": "{:.2f}h"}), use_container_width=True)
    st.caption("Gráfico Comparativo: A barra mais clara é como estava, a mais escura é a sugestão do robô.")
    st.bar_chart(df_resultado_auto.set_index('Setor')[['Jornada Atual', 'Jornada Projetada']], use_container_width=True)

# ==========================================
# 💾 4. PAINEL DE GESTÃO PARA O RELATÓRIO
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
