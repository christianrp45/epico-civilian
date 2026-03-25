import os
import streamlit as st
from limpador_inlog import processar_inlog
from kpis import load_dataset, get_filter_options

st.set_page_config(page_title="EPICO Platform", page_icon="🚛", layout="wide")

# ==========================================
# ⚙️ BARRA LATERAL: ADMINISTRAÇÃO (GOD MODE)
# ==========================================
with st.sidebar:
    st.header("⚙️ Administração (ETL)")
    st.caption("Carregue o relatório bruto do Inlog. O sistema fará a limpeza, removerá anomalias e criará o Padrão Ouro.")
    
    # 1. MUDANÇA: Agora aceita csv, xls e xlsx
    ficheiro_inlog = st.file_uploader("1. Carregar Inlog Bruto (CSV, XLS, XLSX)", type=['csv', 'xls', 'xlsx'], key="upload_inlog_bruto")

    if ficheiro_inlog is not None:
        if st.button("🚀 Processar Dados Brutos", use_container_width=True):
            with st.spinner("A aplicar algoritmos de limpeza e inteligência..."):
                try:
                    # 2. MUDANÇA: Descobre a extensão do arquivo enviado para salvar corretamente
                    extensao = ficheiro_inlog.name.split('.')[-1].lower()
                    arquivo_temp = f"temp_inlog.{extensao}"
                    
                    with open(arquivo_temp, "wb") as f:
                        f.write(ficheiro_inlog.getbuffer())
                    
                    # 3. MUDANÇA: Envia o arquivo com a extensão certa para o robô
                    processar_inlog(arquivo_temp, "dados_coleta.xlsx")
                    
                    os.remove(arquivo_temp)
                    
                    st.success("✅ Padrão Ouro gerado com sucesso!")
                    
                    with open("dados_coleta.xlsx", "rb") as file:
                        btn = st.download_button(
                            label="📥 Baixar Padrão Ouro (Excel)",
                            data=file,
                            file_name="dados_coleta.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    st.info("👉 Baixe o arquivo acima e jogue na tela central da plataforma.")
                    
                except Exception as e:
                    st.error(f"Ups! Ocorreu um erro ao processar: {e}")
                    
    st.markdown("---")
    st.markdown("### Navegação")
    st.markdown("- **Visão Executiva**")
    st.markdown("- **Análise Analítica**")
    st.markdown("- **Equalização**")
    st.markdown("- **Simulador Executivo**")

# ==========================================
# 📊 ECRÃ PRINCIPAL: PLATAFORMA EPICO
# ==========================================
st.title("EPICO Platform")
st.caption("Plataforma de análise, equalização e simulação executiva da coleta domiciliar.")

st.subheader("Base principal da análise")

uploaded = st.file_uploader(
    "2. Envie a base da operação limpa (.xlsx, .xls ou .csv)",
    type=["xlsx", "xls", "csv"],
    key="base_principal_upload"
)

if uploaded is not None:
    try:
        df = load_dataset(uploaded)

        st.session_state["epico_df"] = df
        st.session_state["epico_nome_arquivo"] = uploaded.name

        unidades, turnos, dias, setores = get_filter_options(df)

        st.session_state["filtro_unidades"] = unidades
        st.session_state["filtro_turnos"] = turnos
        st.session_state["filtro_dias"] = dias
        st.session_state["filtro_setores"] = setores

        if "jornada_meta" not in st.session_state:
            st.session_state["jornada_meta"] = 7.33

        if "perfis_filtros" not in st.session_state:
            st.session_state["perfis_filtros"] = {}

        # --- RAIO X PERFEITAMENTE ALINHADO ---
        st.success(f"Base carregada com sucesso: {uploaded.name}")
        
        st.warning("🕵️‍♂️ Colunas que o Streamlit está enxergando agora:")
        st.write(df.columns.tolist())
        # --------------------------------------

    except Exception as exc:
        st.error(f"Não foi possível carregar o arquivo: {exc}")

def lista_bonita(lista):
    if not lista:
        return "Nenhum selecionado"
    return ", ".join(str(x) for x in lista)

if "epico_df" in st.session_state:
    st.info(f"Base ativa: {st.session_state.get('epico_nome_arquivo', 'arquivo carregado')}")

    if "perfis_filtros" not in st.session_state:
        st.session_state["perfis_filtros"] = {}

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Filtros globais atuais")
        st.markdown(f"**Unidades:** {lista_bonita(st.session_state.get('filtro_unidades', []))}")
        st.markdown(f"**Turnos:** {lista_bonita(st.session_state.get('filtro_turnos', []))}")
        st.markdown(f"**Dias:** {lista_bonita(st.session_state.get('filtro_dias', []))}")
        st.markdown(f"**Setores:** {lista_bonita(st.session_state.get('filtro_setores', []))}")

    with c2:
        if st.button("Resetar filtros globais"):
            unidades, turnos, dias, setores = get_filter_options(st.session_state["epico_df"])
            st.session_state["filtro_unidades"] = unidades
            st.session_state["filtro_turnos"] = turnos
            st.session_state["filtro_dias"] = dias
            st.session_state["filtro_setores"] = setores
            st.rerun()

        if st.button("Remover base atual"):
            for chave in [
                "epico_df",
                "epico_nome_arquivo",
                "filtro_unidades",
                "filtro_turnos",
                "filtro_dias",
                "filtro_setores",
                "jornada_meta",
                "perfis_filtros",
            ]:
                st.session_state.pop(chave, None)
            st.rerun()

    st.markdown("---")
    st.subheader("Perfis de filtros")

    p1, p2 = st.columns([1, 1])

    with p1:
        nome_perfil = st.text_input("Nome do perfil", placeholder="Ex.: Diurno Seg/Qua/Sex")

        if st.button("Salvar perfil atual"):
            if not nome_perfil.strip():
                st.warning("Informe um nome para o perfil.")
            else:
                st.session_state["perfis_filtros"][nome_perfil.strip()] = {
                    "filtro_unidades": st.session_state.get("filtro_unidades", []),
                    "filtro_turnos": st.session_state.get("filtro_turnos", []),
                    "filtro_dias": st.session_state.get("filtro_dias", []),
                    "filtro_setores": st.session_state.get("filtro_setores", []),
                    "jornada_meta": st.session_state.get("jornada_meta", 7.33),
                }
                st.success(f"Perfil '{nome_perfil.strip()}' salvo com sucesso.")

    with p2:
        perfis_existentes = list(st.session_state["perfis_filtros"].keys())

        perfil_escolhido = st.selectbox(
            "Perfis salvos",
            options=[""] + perfis_existentes
        )

        c21, c22 = st.columns(2)

        with c21:
            if st.button("Carregar perfil"):
                if perfil_escolhido:
                    perfil = st.session_state["perfis_filtros"][perfil_escolhido]
                    st.session_state["filtro_unidades"] = perfil["filtro_unidades"]
                    st.session_state["filtro_turnos"] = perfil["filtro_turnos"]
                    st.session_state["filtro_dias"] = perfil["filtro_dias"]
                    st.session_state["filtro_setores"] = perfil["filtro_setores"]
                    st.session_state["jornada_meta"] = perfil["jornada_meta"]
                    st.success(f"Perfil '{perfil_escolhido}' carregado.")
                    st.rerun()

        with c22:
            if st.button("Excluir perfil"):
                if perfil_escolhido:
                    st.session_state["perfis_filtros"].pop(perfil_escolhido, None)
                    st.success(f"Perfil '{perfil_escolhido}' excluído.")
                    st.rerun()

    if st.session_state["perfis_filtros"]:
        st.markdown("### Perfis disponíveis")
        for nome, perfil in st.session_state["perfis_filtros"].items():
            st.markdown(
                f"""
**{nome}** - Turnos: {perfil['filtro_turnos']}  
- Dias: {perfil['filtro_dias']}  
- Setores: {perfil['filtro_setores']}
"""
            )

else:
    st.warning("Nenhuma base carregada ainda. Faça o upload acima para usar todas as páginas.")

st.markdown(
    """
### Como funciona agora

- a base é carregada uma vez
- os filtros ficam salvos globalmente
- você pode salvar perfis de uso recorrente
- todas as páginas usam a mesma base e os mesmos filtros
"""
)
