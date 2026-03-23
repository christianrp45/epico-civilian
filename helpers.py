import streamlit as st
from kpis import apply_filters, get_filter_options

def upload_and_filter_page(title, caption):
    st.title(title)
    st.caption(caption)

    if "epico_df" not in st.session_state:
        st.warning("Nenhuma base foi carregada. Vá para a página inicial e envie o arquivo.")
        st.stop()

    df = st.session_state["epico_df"]

    # Carrega as opções completas iniciais
    unidades, turnos, dias, setores = get_filter_options(df)

    if "jornada_meta" not in st.session_state:
        st.session_state["jornada_meta"] = 7.33

    if "filtro_unidades" not in st.session_state:
        st.session_state["filtro_unidades"] = unidades

    if "filtro_turnos" not in st.session_state:
        st.session_state["filtro_turnos"] = turnos

    if "filtro_dias" not in st.session_state:
        st.session_state["filtro_dias"] = dias

    if "filtro_setores" not in st.session_state:
        st.session_state["filtro_setores"] = setores

    st.sidebar.subheader("Configuração Global")
    st.session_state["jornada_meta"] = st.sidebar.number_input(
        "Jornada contratual/meta (horas)",
        min_value=1.0,
        max_value=24.0,
        value=float(st.session_state["jornada_meta"]),
        step=0.01,
        key=f"global_jornada_meta_{title}"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"**Base ativa:** \n{st.session_state.get('epico_nome_arquivo', 'arquivo carregado')}"
    )

    st.subheader("Filtros Globais da Plataforma")
    
    # Validação para evitar erros de seleções anteriores que não existem mais
    selected_unidades = [u for u in st.session_state["filtro_unidades"] if u in unidades]

    col1, col2, col3, col4 = st.columns(4)

    # 1. Filtro de Unidade (Base de tudo)
    st.session_state["filtro_unidades"] = col1.multiselect(
        "🏢 Unidade",
        unidades,
        default=selected_unidades,
        key=f"global_unidades_{title}"
    )

    # Filtra o df temporariamente com as unidades escolhidas para saber quais turnos existem
    df_temp1 = df[df["Unidade"].isin(st.session_state["filtro_unidades"])] if st.session_state["filtro_unidades"] else df
    opcoes_turnos = sorted(list(df_temp1["Turno"].dropna().unique()))
    selected_turnos = [t for t in st.session_state["filtro_turnos"] if t in opcoes_turnos]

    # 2. Filtro de Turno (Depende de Unidade)
    st.session_state["filtro_turnos"] = col2.multiselect(
        "⏱️ Turno",
        opcoes_turnos,
        default=selected_turnos,
        key=f"global_turnos_{title}"
    )

    # Filtra novamente para saber quais dias existem nas unidades e turnos escolhidos
    df_temp2 = df_temp1[df_temp1["Turno"].isin(st.session_state["filtro_turnos"])] if st.session_state["filtro_turnos"] else df_temp1
    opcoes_dias = sorted(list(df_temp2["Dia da Semana"].dropna().unique()))
    selected_dias = [d for d in st.session_state["filtro_dias"] if d in opcoes_dias]

    # 3. Filtro de Dia (Depende de Unidade e Turno)
    st.session_state["filtro_dias"] = col3.multiselect(
        "📅 Dia da Semana",
        opcoes_dias,
        default=selected_dias,
        key=f"global_dias_{title}"
    )

    # Filtra para saber quais setores sobraram
    df_temp3 = df_temp2[df_temp2["Dia da Semana"].isin(st.session_state["filtro_dias"])] if st.session_state["filtro_dias"] else df_temp2
    # Assegura que Setor seja tratado como string para ordenação correta
    opcoes_setores = sorted(list(df_temp3["Setor"].dropna().astype(str).unique()))
    selected_setores = [s for s in st.session_state["filtro_setores"] if str(s) in opcoes_setores]

    # 4. Filtro de Setor (Depende de tudo)
    st.session_state["filtro_setores"] = col4.multiselect(
        "📍 Setor",
        opcoes_setores,
        default=selected_setores,
        key=f"global_setores_{title}"
    )

    # Aplica o filtro final (usando sua função original)
    df_filtrado = apply_filters(
        df,
        st.session_state["filtro_unidades"],
        st.session_state["filtro_turnos"],
        st.session_state["filtro_dias"],
        st.session_state["filtro_setores"],
    )

    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
        st.stop()

    return st.session_state["jornada_meta"], df_filtrado