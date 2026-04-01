import pandas as pd
import streamlit as st
import plotly.express as px

from helpers import upload_and_filter_page
from kpis import compute_dashboard_data, format_horas_hhmmss, format_number_br

# --- CONFIGURAÇÕES PADRÃO ---
META_PADRAO = 7 + 20 / 60

# --- CÉREBRO FINANCEIRO (OPEX) ---
def calcular_custo_oculto(df, meta_horas, p_diesel, p_arla, p_pneu, v_pneu, c_manut, custo_he):
    df_calc = df.copy()
    
    # Calcula L/Km para descobrir quanto o Km Improdutivo queima de Diesel
    df_calc["L_por_km_real"] = (df_calc["Combustível"] / df_calc["Km Total"].replace(0, 1)).replace([float("inf"), -float("inf")], 0).fillna(0)
    
    # 1. Custo do Tempo Perdido (Horas Trabalhadas acima da Meta)
    df_calc["Horas_Excesso"] = (df_calc["Horas Trabalhadas"] - meta_horas).clip(lower=0)
    total_horas_excesso = df_calc["Horas_Excesso"].sum()
    custo_total_he = total_horas_excesso * custo_he
    
    # 2. Custo do Deslocamento Improdutivo (Km Improdutivo)
    total_km_improdutivo = df_calc["Km Improdutivo"].sum()
    litros_desperdiciados = (df_calc["Km Improdutivo"] * df_calc["L_por_km_real"]).sum()
    
    custo_diesel_imp = litros_desperdiciados * p_diesel
    custo_arla_imp = (litros_desperdiciados * 0.05) * p_arla
    custo_pneu_imp = total_km_improdutivo * (p_pneu / max(v_pneu, 1))
    custo_manut_imp = total_km_improdutivo * c_manut
    
    custo_frota_improdutiva = custo_diesel_imp + custo_arla_imp + custo_pneu_imp + custo_manut_imp
    
    custo_total_diario = custo_total_he + custo_frota_improdutiva
    custo_total_mensal = custo_total_diario * 26 # 26 dias úteis
    
    return {
        "horas_perdidas": total_horas_excesso,
        "km_perdidos": total_km_improdutivo,
        "litros_perdidos": litros_desperdiciados,
        "custo_he_diario": custo_total_he,
        "custo_frota_diario": custo_frota_improdutiva,
        "custo_total_mensal": custo_total_mensal
    }

# --- INÍCIO DA PÁGINA ---
jornada_meta, df_filtrado = upload_and_filter_page(
    "Visão Executiva",
    "Diagnóstico financeiro e operacional da situação atual (Custo Oculto da Ineficiência)."
)

results = compute_dashboard_data(df_filtrado, jornada_meta=jornada_meta)
rotas = results["rotas"].copy()

if rotas.empty:
    st.warning("Nenhum dado disponível após os filtros.")
    st.stop()

# Garantir conversões numéricas
nums = ["Toneladas", "Viagens", "Km Produtivo", "Km Improdutivo", "Km Total", "Combustível", "Horas Trabalhadas", "Produtividade (t/h)"]
for c in nums:
    if c in rotas.columns:
        rotas[c] = pd.to_numeric(rotas[c], errors="coerce").fillna(0)

# --- MENU LATERAL DE OPEX (COM SINCRONIZAÇÃO DE MEMÓRIA) ---
st.sidebar.subheader("🎯 Metas Operacionais")
meta_operacional = st.sidebar.number_input("Meta ideal de jornada (h)", min_value=1.0, max_value=24.0, value=float(st.session_state.get("meta_operacional", META_PADRAO)), step=0.01)

st.sidebar.subheader("⚙️ Parâmetros Operacionais (Frota)")
preco_diesel = st.sidebar.number_input("Preço Diesel (R$/L)", min_value=0.0, value=float(st.session_state.get("preco_diesel", 6.23)), step=0.10)
preco_arla = st.sidebar.number_input("Preço ARLA 32 (R$/L)", min_value=0.0, value=float(st.session_state.get("preco_arla", 3.50)), step=0.10)
custo_pneu = st.sidebar.number_input("Custo Jogo Pneus (R$)", min_value=0.0, value=float(st.session_state.get("custo_pneu", 1500.0)), step=100.0)
vida_pneu = st.sidebar.number_input("Vida Útil Pneu (Km)", min_value=1, value=int(st.session_state.get("vida_pneu", 40000)), step=1000)
custo_manut = st.sidebar.number_input("Custo Manutenção (R$/Km)", min_value=0.0, value=float(st.session_state.get("custo_manut", 0.85)), step=0.05)

with st.sidebar.expander("👷 Parâmetros de Mão de Obra (Mensal)", expanded=False):
    st.markdown("**Composição da Equipe**")
    qtd_coletores = st.number_input("Qtd Coletores por Caminhão", min_value=1, value=int(st.session_state.get("qtd_coletores", 3)), step=1)
    pct_hora_extra = st.number_input("Adicional de H.E. (%)", min_value=0.0, value=float(st.session_state.get("pct_hora_extra", 50.0)), step=5.0)

    st.markdown("**Custos Motorista (R$)**")
    mot_salario = st.number_input("Salário Base (Mot.)", value=float(st.session_state.get("mot_salario", 2741.61)))
    mot_insalub = st.number_input("Insalubridade (Mot.)", value=float(st.session_state.get("mot_insalub", 1096.64)))
    mot_encargos = st.number_input("Encargos Trabalhistas (Mot.)", value=float(st.session_state.get("mot_encargos", 651.48)))
    mot_va = st.number_input("Vale Alimentação (Mot.)", value=float(st.session_state.get("mot_va", 708.50)))

    st.markdown("**Custos Coletor (R$)**")
    col_salario = st.number_input("Salário Base (Col.)", value=float(st.session_state.get("col_salario", 2053.20)))
    col_insalub = st.number_input("Insalubridade (Col.)", value=float(st.session_state.get("col_insalub", 821.28)))
    col_encargos = st.number_input("Encargos Trabalhistas (Col.)", value=float(st.session_state.get("col_encargos", 602.04)))
    col_va = st.number_input("Vale Alimentação (Col.)", value=float(st.session_state.get("col_va", 708.50)))

# Salva os valores na memória para que a Página Automática consiga ler os mesmos dados
st.session_state.update({
    "meta_operacional": meta_operacional, "preco_diesel": preco_diesel, "preco_arla": preco_arla,
    "custo_pneu": custo_pneu, "vida_pneu": vida_pneu, "custo_manut": custo_manut,
    "qtd_coletores": qtd_coletores, "pct_hora_extra": pct_hora_extra,
    "mot_salario": mot_salario, "mot_insalub": mot_insalub, "mot_encargos": mot_encargos, "mot_va": mot_va,
    "col_salario": col_salario, "col_insalub": col_insalub, "col_encargos": col_encargos, "col_va": col_va
})

# Calcula o custo da Hora Extra Real (Apenas Salário Base / 220)
mot_hora_normal = mot_salario / 220.0
col_hora_normal = col_salario / 220.0
fator_he = 1 + (pct_hora_extra / 100.0)
custo_he_equipe = (mot_hora_normal * fator_he) + ((col_hora_normal * fator_he) * qtd_coletores)

# --- CORPO DA PÁGINA ---
st.subheader("1. Indicadores Globais de Produção")

total_toneladas_calc = rotas["Toneladas"].sum()
total_viagens_calc = int(rotas["Viagens"].sum())
total_km_calc = rotas["Km Total"].sum()
total_combustivel_calc = rotas["Combustível"].sum()

ton_viagem_media = total_toneladas_calc / max(total_viagens_calc, 1)
km_improdutivo_pct = rotas["Km Improdutivo"].sum() / max(total_km_calc, 1)
km_por_litro = total_km_calc / max(total_combustivel_calc, 1)
horas_extras_totais = rotas["Horas Trabalhadas"].apply(lambda x: max(0, x - meta_operacional)).sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Toneladas", format_number_br(total_toneladas_calc, 2))
c2.metric("Total Viagens", total_viagens_calc)
c3.metric("Km Total Percorrido", format_number_br(total_km_calc, 2))
c4.metric("Consumo Diesel (L)", format_number_br(total_combustivel_calc, 2))

c5, c6, c7, c8 = st.columns(4)
c5.metric("Ton / Viagem Média", format_number_br(ton_viagem_media, 2))
c6.metric("Horas Extras (Total/Dia)", format_horas_hhmmss(horas_extras_totais))
c7.metric("% Km Improdutivo", f"{km_improdutivo_pct:.1%}")
c8.metric("Média Km/L", format_number_br(km_por_litro, 2))

st.markdown("---")

# --- PAINEL DE ALERTA FINANCEIRO (O CHOQUE PARA O CFO) ---
st.subheader("🚨 Termômetro Financeiro: O Custo da Ineficiência Atual")
st.markdown("Cálculo estimado do vazamento de caixa gerado por **Horas Extras** (acima da meta ideal) e **Km Improdutivo** (viagens de deslocamento sem coleta).")

sangramento = calcular_custo_oculto(rotas, meta_operacional, preco_diesel, preco_arla, custo_pneu, vida_pneu, custo_manut, custo_he_equipe)

f1, f2, f3 = st.columns(3)
f1.metric("Passivo Trab. (Horas Extras/Dia)", f"R$ {format_number_br(sangramento['custo_he_diario'], 2)}", f"-{format_horas_hhmmss(sangramento['horas_perdidas'])} horas estouradas", delta_color="inverse")
f2.metric("Desperdício de Frota (Km Imp./Dia)", f"R$ {format_number_br(sangramento['custo_frota_diario'], 2)}", f"-{format_number_br(sangramento['km_perdidos'], 1)} km vazios", delta_color="inverse")
f3.metric("Custo Oculto Total (Mensalizado)", f"R$ {format_number_br(sangramento['custo_total_mensal'], 2)}", "DRE Mensal Estimado", delta_color="inverse")

if sangramento['custo_total_mensal'] > 0:
    st.error(f"**Atenção Diretoria:** A operação atual possui um 'Custo Oculto' de aproximadamente **R$ {format_number_br(sangramento['custo_total_mensal'], 2)} por mês**. Utilize os Simuladores de Equalização para encontrar o Ponto de Equilíbrio e recuperar esse capital.")
else:
    st.success("Operação extremamente enxuta. Sem custos de ociosidade detectados.")

st.markdown("---")

# --- GRÁFICOS DE DIAGNÓSTICO ---
st.subheader("2. Raio-X por Setor (Onde estão os gargalos?)")

rotas_grafico = rotas.copy()
rotas_grafico["Setor"] = rotas_grafico["Setor"].astype(str)

g1, g2 = st.columns(2)
with g1:
    fig_prod = px.bar(
        rotas_grafico.sort_values("Produtividade (t/h)", ascending=False), 
        x="Setor", y="Produtividade (t/h)", 
        title="Produtividade Efetiva (t/h)",
        color="Produtividade (t/h)", color_continuous_scale="Viridis"
    )
    media_produtividade_calc = rotas_grafico["Produtividade (t/h)"].replace([float("inf"), -float("inf")], pd.NA).dropna().mean()
    if pd.isna(media_produtividade_calc): media_produtividade_calc = 0
    fig_prod.add_hline(y=media_produtividade_calc, line_dash="dash", line_color="red", annotation_text="Média Global")
    fig_prod.update_xaxes(type="category")
    st.plotly_chart(fig_prod, use_container_width=True)

with g2:
    fig_km = px.bar(
        rotas_grafico.sort_values("Km Improdutivo", ascending=False), 
        x="Setor", y="Km Improdutivo", 
        title="Desperdício: Km Improdutivo por Setor",
        color="Km Improdutivo", color_continuous_scale="Reds"
    )
    fig_km.update_xaxes(type="category")
    st.plotly_chart(fig_km, use_container_width=True)

st.subheader("3. Detalhamento Técnico")
tabela_view = rotas.copy()
tabela_view["Horas Trabalhadas"] = tabela_view["Horas Trabalhadas"].apply(format_horas_hhmmss)
for col in ["Toneladas", "Km Total", "Km Produtivo", "Km Improdutivo", "Combustível", "Produtividade (t/h)"]:
    tabela_view[col] = tabela_view[col].apply(lambda x: format_number_br(x, 2))

cols = ["Setor", "Toneladas", "Viagens", "Horas Trabalhadas", "Km Total", "Km Improdutivo", "Combustível", "Produtividade (t/h)"]
st.dataframe(tabela_view[cols], use_container_width=True, hide_index=True)
