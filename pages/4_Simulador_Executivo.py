import math
import pandas as pd
import streamlit as st
import plotly.express as px
from helpers import upload_and_filter_page
from kpis import compute_dashboard_data, format_horas_hhmmss, format_number_br

LIMITE_HORAS = 9 + 20 / 60
META_PADRAO = 7 + 20 / 60
CAP_BASE_TOCO = 9.5
CAPACIDADES = {"Toco": 9.5, "Trucado": 13.5}

DISTANCIAS_ATERRO = {
    "2000": 2.43, "2001": 4.90, "2002": 5.02, "2003": 11.13, "2004": 12.30,
    "3000": 4.14, "3001": 2.10, "3002": 9.00, "3003": 15.39, "3004": 13.70,
    "3005": 4.78, "4001": 2.81, "4002": 3.56, "4003": 12.15, "4004": 14.58,
    "5001": 3.40, "5002": 5.24, "5003": 14.76, "5004": 13.96, "5005": 7.38
}
VELOCIDADE_MEDIA_ATERRO = 40.0

# --- NOVO: MAPEAMENTO OPERACIONAL ---
MAPA_TURNOS = {
    "2000": "Matutino", "2001": "Matutino", "2002": "Matutino", "2003": "Matutino", "2004": "Matutino",
    "3000": "Matutino", "3001": "Vespertino", "3002": "Vespertino", "3003": "Vespertino", "3004": "Vespertino", "3005": "Vespertino",
    "4001": "Matutino", "4002": "Matutino", "4003": "Matutino", "4004": "Matutino",
    "5001": "Vespertino", "5002": "Vespertino", "5003": "Vespertino", "5004": "Vespertino", "5005": "Vespertino"
}
MAPA_FREQUENCIA = {
    "2000": "Diária", "3000": "Diária",
    "2001": "Seg/Qua/Sex", "2002": "Seg/Qua/Sex", "2003": "Seg/Qua/Sex", "2004": "Seg/Qua/Sex",
    "3001": "Seg/Qua/Sex", "3002": "Seg/Qua/Sex", "3003": "Seg/Qua/Sex", "3004": "Seg/Qua/Sex", "3005": "Seg/Qua/Sex",
    "4001": "Ter/Qui/Sab", "4002": "Ter/Qui/Sab", "4003": "Ter/Qui/Sab", "4004": "Ter/Qui/Sab",
    "5001": "Ter/Qui/Sab", "5002": "Ter/Qui/Sab", "5003": "Ter/Qui/Sab", "5004": "Ter/Qui/Sab", "5005": "Ter/Qui/Sab"
}

def ceil_viagens(t, c):
    if pd.isna(t) or pd.isna(c) or c <= 0: return 0
    t = max(float(t), 0.0)
    return int(math.ceil(t / float(c))) if t > 0 else 0

def ordenar_setores(df):
    ordem = pd.to_numeric(df["Setor"], errors="coerce").fillna(999999).astype(int)
    return df.assign(_ord=ordem).sort_values("_ord").drop(columns="_ord")

def construir_mapa_capacidade(rotas, prefixo):
    st.sidebar.subheader("Configuração de Frota")
    tipo_map, cap_map = {}, {}
    for setor in rotas["Setor"].astype(str).tolist():
        tipo = st.sidebar.selectbox(f"Tipo caminhão - Setor {setor}", list(CAPACIDADES.keys()), index=0, key=f"{prefixo}_{setor}")
        tipo_map[setor] = tipo
        cap_map[setor] = CAPACIDADES[tipo]
    return tipo_map, cap_map

def preparar(rotas, tipo_map, cap_map):
    df = rotas.copy()
    df["Setor"] = df["Setor"].astype(str).str.zfill(4)
    nums = ["Toneladas","Viagens","Km Produtivo","Km Improdutivo","Km Total","Combustível","Horas Trabalhadas","Produtividade (t/h)"]
    for c in nums:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
            
    df["L_por_km_real"] = (df["Combustível"] / df["Km Total"].replace(0, 1)).replace([float("inf"), -float("inf")], 0).fillna(0)
    if "Horas Produtivas" not in df.columns or df["Horas Produtivas"].isna().all(): df["Horas Produtivas"] = df["Horas Trabalhadas"] * 0.75
    if "Horas Improdutivas" not in df.columns or df["Horas Improdutivas"].isna().all(): df["Horas Improdutivas"] = (df["Horas Trabalhadas"] - df["Horas Produtivas"]).clip(lower=0)
        
    df["Tipo Caminhão"] = df["Setor"].map(tipo_map).fillna("Toco")
    df["Capacidade (t)"] = df["Setor"].map(cap_map).fillna(CAPACIDADES["Toco"])
    df["Horas Atual (h)"] = df["Horas Trabalhadas"]
    df["Ton Atual"] = df["Toneladas"]
    df["Viagens Atual"] = df["Viagens"].fillna(0).round().astype(int)
    df["Km Atual"] = df["Km Total"]
    df["Combustível Atual"] = df["Combustível"]
    df["Horas Produtivas Simuladas"] = df["Horas Produtivas"]
    df["Horas Improdutivas Simuladas"] = df["Horas Improdutivas"]
    df["Km Produtivo Simulado"] = df["Km Produtivo"]
    df["Km Produtivo Simulado"] = df["Km Improdutivo"]
    df["Horas Simulada (h)"] = df["Horas Trabalhadas"]
    df["Toneladas Simulada"] = df["Toneladas"]
    df["Ton Recebida do Doador"] = 0.0
    df["Ton Doada"] = 0.0
    df["Produtividade Ref"] = df["Produtividade (t/h)"].fillna(0)
    media = df["Produtividade Ref"].replace([float("inf"), -float("inf")], pd.NA).dropna().mean()
    if pd.isna(media): media = 0.0
    df.loc[df["Produtividade Ref"] <= 0, "Produtividade Ref"] = media
    return ordenar_setores(df)

def recomputar(df):
    out = df.copy()
    out["Viagens Projetadas"] = out.apply(lambda x: ceil_viagens(x["Toneladas Simulada"], x["Capacidade (t)"]), axis=1)
    novo_km_imp, nova_hr_imp = [], []
    for _, row in out.iterrows():
        v_orig_teorica = ceil_viagens(row["Ton Atual"], CAP_BASE_TOCO)
        v_orig = max(1, int(v_orig_teorica))
        v_proj = max(1, int(row["Viagens Projetadas"]))
        delta_v = v_proj - v_orig
        dist_ida = DISTANCIAS_ATERRO.get(str(row["Setor"]), 7.5)
        km_extra_aterro = delta_v * (dist_ida * 2)
        km_imp = max(0.0, float(row["Km Improdutivo"]) + km_extra_aterro)
        hr_extra = 0.0
        if delta_v > 0: hr_extra = (km_extra_aterro / VELOCIDADE_MEDIA_ATERRO) + (delta_v * 0.5)
        elif delta_v < 0: hr_extra = -((abs(km_extra_aterro) / VELOCIDADE_MEDIA_ATERRO) + (abs(delta_v) * 0.5))
        hr_imp = max(0.0, float(row["Horas Improdutivas"]) + hr_extra)
        novo_km_imp.append(km_imp)
        nova_hr_imp.append(hr_imp)
    out["Km Improdutivo Simulado"] = novo_km_imp
    out["Horas Improdutivas Simuladas"] = nova_hr_imp
    out["Horas Simulada (h)"] = out["Horas Produtivas Simuladas"].fillna(0) + out["Horas Improdutivas Simuladas"].fillna(0)
    out["Km Simulado"] = out["Km Produtivo Simulado"] + out["Km Improdutivo Simulado"]
    out["Combustível Simulado"] = out["Km Simulado"] * out["L_por_km_real"]
    return ordenar_setores(out)

def transferir_proporcional(df, idx_d, idx_r, horas, tons):
    ton_before = max(float(df.loc[idx_d, "Toneladas Simulada"]), 0.0)
    hr_prod_before = max(float(df.loc[idx_d, "Horas Produtivas Simuladas"]), 0.0)
    if ton_before > 0 and tons > 0: frac = min(tons / ton_before, 1.0)
    elif hr_prod_before > 0 and horas > 0: frac = min(horas / hr_prod_before, 1.0)
    else: frac = 0.0
    for c in ["Horas Produtivas Simuladas", "Km Produtivo Simulado"]:
        mover = float(df.loc[idx_d, c]) * frac
        df.loc[idx_d, c] = max(float(df.loc[idx_d, c]) - mover, 0.0)
        df.loc[idx_r, c] = float(df.loc[idx_r, c]) + mover
    df.loc[idx_d, "Toneladas Simulada"] = max(float(df.loc[idx_d, "Toneladas Simulada"]) - tons, 0.0)
    df.loc[idx_r, "Toneladas Simulada"] = float(df.loc[idx_r, "Toneladas Simulada"]) + tons
    df.loc[idx_d, "Ton Doada"] += tons
    df.loc[idx_r, "Ton Recebida do Doador"] += tons
    return df

def calcular_eficiencia(tons, viagens, cap):
    if viagens == 0 or cap == 0: return "⚪ N/A"
    pct = (tons / (viagens * cap)) * 100
    if pct > 100: return f"🔴 {pct:.1f}%"
    elif pct < 70: return f"🟡 {pct:.1f}%"
    else: return f"🟢 {pct:.1f}%"

def df_apresentacao(c):
    ex = c.copy()
    ex["Horas Atual"] = ex["Horas Atual (h)"].apply(format_horas_hhmmss)
    ex["Horas Simulada"] = ex["Horas Simulada (h)"].apply(format_horas_hhmmss)
    ex["Eficiência Sim."] = ex.apply(lambda x: calcular_eficiencia(x["Toneladas Simulada"], x["Viagens Projetadas"], x["Capacidade (t)"]), axis=1)
    for col in ["Ton Atual","Toneladas Simulada","Ton Recebida do Doador","Ton Doada","Combustível Atual","Combustível Simulado"]:
        ex[col] = pd.to_numeric(ex[col], errors="coerce").round(4)
    for col in ["Km Atual","Km Simulado"]:
        ex[col] = pd.to_numeric(ex[col], errors="coerce").round(2)
    return ex[["Setor","Turno","Frequência","Tipo Caminhão","Eficiência Sim.","Capacidade (t)","Ton Atual","Toneladas Simulada","Ton Recebida do Doador","Ton Doada","Horas Atual","Horas Simulada","Viagens Atual","Viagens Projetadas","Km Atual","Km Simulado"]]

def grafico_horas(cenario, meta_horas, limite_horas, titulo):
    plot_df = ordenar_setores(cenario[["Setor","Horas Atual (h)","Horas Simulada (h)"]].copy())
    plot_df["Setor"] = plot_df["Setor"].astype(str)
    atual_max = float(plot_df["Horas Atual (h)"].max())
    long_df = plot_df.melt(id_vars="Setor", value_vars=["Horas Atual (h)","Horas Simulada (h)"], var_name="Série", value_name="Horas")
    long_df["Série"] = long_df["Série"].replace({"Horas Atual (h)":"Horas Atual","Horas Simulada (h)":"Horas Simulada"})
    fig = px.bar(long_df, x="Setor", y="Horas", color="Série", barmode="group", title=titulo)
    fig.update_xaxes(type="category")
    fig.add_hline(y=meta_horas, line_dash="dash", line_color="green", annotation_text=f"Meta ideal {format_horas_hhmmss(meta_horas)}")
    fig.add_hline(y=limite_horas, line_dash="dash", line_color="yellow", annotation_text=f"Limite legal {format_horas_hhmmss(limite_horas)}")
    fig.add_hline(y=atual_max, line_dash="dot", line_color="red", annotation_text=f"Topo atual real {format_horas_hhmmss(atual_max)}")
    return fig

def grafico_grupos(cenario, titulo, coluna_atual, coluna_simulada, rotulo):
    plot_df = ordenar_setores(cenario[["Setor", coluna_atual, coluna_simulada]].copy())
    plot_df["Setor"] = plot_df["Setor"].astype(str)
    long_df = plot_df.melt(id_vars="Setor", value_vars=[coluna_atual, coluna_simulada], var_name="Série", value_name=rotulo)
    long_df["Série"] = long_df["Série"].replace({coluna_atual:"Atual", coluna_simulada:"Simulado"})
    fig = px.bar(long_df, x="Setor", y=rotulo, color="Série", barmode="group", title=titulo)
    fig.update_xaxes(type="category")
    return fig

def ganhos_financeiros(c, p_diesel, p_arla, p_pneu, v_pneu, c_manut, custo_he_equipe):
    delta_horas = max(0.0, float(c["Horas Atual (h)"].sum()) - float(c["Horas Simulada (h)"].sum()))
    delta_km = max(0.0, float(c["Km Atual"].sum()) - float(c["Km Simulado"].sum()))
    delta_litros = max(0.0, float(c["Combustível Atual"].sum()) - float(c["Combustível Simulado"].sum()))
    
    eco_diesel = delta_litros * p_diesel
    eco_arla = (delta_litros * 0.05) * p_arla
    eco_pneu = delta_km * (p_pneu / max(v_pneu, 1))
    eco_manut = delta_km * c_manut
    eco_hora = delta_horas * custo_he_equipe
    
    total_diario = eco_diesel + eco_arla + eco_pneu + eco_manut + eco_hora
    total_mensal = total_diario * 26 
    
    return {
        "horas": delta_horas, "km": delta_km, "litros": delta_litros,
        "eco_diesel": eco_diesel, "eco_arla": eco_arla, "eco_pneu": eco_pneu,
        "eco_manut": eco_manut, "eco_hora": eco_hora, "total_diario": total_diario,
        "total_mensal": total_mensal, "lucro_liquido": total_mensal
    }

jornada_meta, df_filtrado = upload_and_filter_page("Simulador Executivo","Transferência manual entre setores com Filtros Operacionais.")
results = compute_dashboard_data(df_filtrado, jornada_meta=jornada_meta)
rotas = results["rotas"].copy()
medias = results["medias"]
if rotas.empty:
    st.warning("Não há rotas disponíveis para simulação.")
    st.stop()

# --- APLICANDO OS FILTROS OPERACIONAIS ---
rotas["Setor"] = rotas["Setor"].astype(str).str.zfill(4)
rotas["Turno"] = rotas["Setor"].map(MAPA_TURNOS).fillna("Desconhecido")
rotas["Frequência"] = rotas["Setor"].map(MAPA_FREQUENCIA).fillna("Desconhecida")

st.sidebar.subheader("🔎 Filtros da Operação")
filtro_turno = st.sidebar.selectbox("Filtrar por Turno", ["Todos", "Matutino", "Vespertino"])
filtro_freq = st.sidebar.selectbox("Filtrar por Frequência", ["Todas", "Diária", "Seg/Qua/Sex", "Ter/Qui/Sab"])

if filtro_turno != "Todos":
    rotas = rotas[rotas["Turno"] == filtro_turno]
if filtro_freq != "Todas":
    rotas = rotas[rotas["Frequência"] == filtro_freq]

if rotas.empty:
    st.sidebar.error("Nenhuma rota atende a esses filtros.")
    st.warning("Nenhuma rota atende aos filtros de Turno e Frequência selecionados. Tente mudar o filtro.")
    st.stop()

# --- MENU LATERAL OPEX ---
st.sidebar.subheader("🎯 Metas Operacionais")
meta_equalizacao = st.sidebar.number_input("Meta ideal (horas)", min_value=1.0, max_value=24.0, value=float(st.session_state.get("meta_operacional", META_PADRAO)), step=0.01)
limite_operacional = st.sidebar.number_input("Limite legal (horas)", min_value=1.0, max_value=24.0, value=float(LIMITE_HORAS), step=0.01)

st.sidebar.subheader("⚙️ Parâmetros Operacionais (Frota)")
preco_diesel = st.sidebar.number_input("Preço Diesel (R$/L)", min_value=0.0, value=float(st.session_state.get("preco_diesel", 6.23)), step=0.10)
preco_arla = st.sidebar.number_input("Preço ARLA 32 (R$/L)", min_value=0.0, value=float(st.session_state.get("preco_arla", 3.50)), step=0.10)
custo_pneu = st.sidebar.number_input("Custo Jogo Pneus (R$)", min_value=0.0, value=float(st.session_state.get("custo_pneu", 1500.0)), step=100.0)
vida_pneu = st.sidebar.number_input("Vida Útil Pneu (Km)", min_value=1, value=int(st.session_state.get("vida_pneu", 40000)), step=1000)
custo_manut = st.sidebar.number_input("Custo Manutenção (R$/Km)", min_value=0.0, value=float(st.session_state.get("custo_manut", 0.85)), step=0.05)

with st.sidebar.expander("👷 Parâmetros de Mão de Obra (Mensal)", expanded=False):
    qtd_coletores = st.number_input("Qtd de Coletores por Caminhão", min_value=1, value=int(st.session_state.get("qtd_coletores", 3)), step=1)
    pct_hora_extra = st.number_input("Adicional de Hora Extra (%)", min_value=0.0, value=float(st.session_state.get("pct_hora_extra", 50.0)), step=5.0)
    mot_salario = st.number_input("Salário Base (Mot.)", value=float(st.session_state.get("mot_salario", 2741.61)))
    col_salario = st.number_input("Salário Base (Col.)", value=float(st.session_state.get("col_salario", 2053.20)))

mot_hora_normal = mot_salario / 220.0
col_hora_normal = col_salario / 220.0
fator_he = 1 + (pct_hora_extra / 100.0)
custo_he_equipe = (mot_hora_normal * fator_he) + ((col_hora_normal * fator_he) * qtd_coletores)

tipo_map, cap_map = construir_mapa_capacidade(rotas, "manual")
base = preparar(rotas, tipo_map, cap_map)
base = recomputar(base)

st.subheader(f"1. Situação Atual do Grupo ({filtro_turno} | {filtro_freq})")
c1,c2,c3,c4 = st.columns(4)
c1.metric("Média de horas", format_horas_hhmmss(medias["media_horas"]))
c2.metric("Meta ideal", format_horas_hhmmss(meta_equalizacao))
c3.metric("Limite legal", format_horas_hhmmss(limite_operacional))
c4.metric("Amplitude atual", format_horas_hhmmss(base["Horas Atual (h)"].max() - base["Horas Atual (h)"].min()))

st.markdown("##### Painel de Doadores e Receptores (Desvio da Média Possível)")
df_atual = base.copy()
alvo_equalizacao = max(meta_equalizacao, float(df_atual["Horas Simulada (h)"].sum()) / max(len(df_atual), 1))
df_atual["Desvio (h)"] = df_atual["Horas Simulada (h)"] - alvo_equalizacao
df_atual["Perfil"] = df_atual["Desvio (h)"].apply(lambda x: "🔴 Doador" if x > 1e-4 else ("🟢 Receptor" if x < -1e-4 else "⚪ Na Meta"))

def format_desvio(h):
    if abs(h) < 1e-4: return "00:00:00"
    sign = "+" if h > 0 else "-"
    return f"{sign}{format_horas_hhmmss(abs(h))}"

df_atual["Desvio ao Alvo"] = df_atual["Desvio (h)"].apply(format_desvio)
df_atual["Horas Simulada"] = df_atual["Horas Simulada (h)"].apply(format_horas_hhmmss)
df_atual["Toneladas Simulada"] = pd.to_numeric(df_atual["Toneladas Simulada"], errors="coerce").round(2)
df_atual["Km Simulado"] = pd.to_numeric(df_atual["Km Simulado"], errors="coerce").round(2)

cols_atual = ["Setor", "Perfil", "Desvio ao Alvo", "Horas Simulada", "Tipo Caminhão", "Toneladas Simulada", "Viagens Projetadas", "Km Simulado"]
df_atual_view = df_atual.sort_values(by="Desvio (h)", ascending=False)
st.dataframe(df_atual_view[cols_atual], use_container_width=True, hide_index=True)

st.subheader("2. Equalização Manual de Rotas")
df_doadores = df_atual_view[df_atual_view["Desvio (h)"] > 1e-4]
df_receptores = df_atual_view[df_atual_view["Desvio (h)"] < -1e-4].sort_values(by="Desvio (h)", ascending=True)

lista_doadores = df_doadores["Setor"].astype(str).tolist()
lista_receptores = df_receptores["Setor"].astype(str).tolist()

transferencias = []
for i in range(8):
    a,b,c = st.columns(3)
    doador = a.selectbox(f"Setor doador {i+1} (Acima da média)", [""] + lista_doadores, key=f"doador_{i}")
    receptor = b.selectbox(f"Setor receptor {i+1} (Abaixo da média)", [""] + lista_receptores, key=f"receptor_{i}")
    horas = c.number_input(f"Horas a transferir {i+1}", min_value=0.0, max_value=8.0, value=0.0, step=0.1, key=f"horas_{i}")
    if doador and receptor and horas > 0:
        transferencias.append((doador, receptor, float(horas)))

c_apply, c_clear = st.columns(2)
if c_apply.button("Aplicar Equalização Manual"):
    sim = base.copy()
    plano = []
    inconsist = []
    
    for doador, receptor, horas in transferencias:
        if doador == receptor:
            inconsist.append(f"{doador}: doador e receptor não podem ser iguais.")
            continue
        idx_d = sim[sim["Setor"] == doador].index
        idx_r = sim[sim["Setor"] == receptor].index
        if len(idx_d)==0 or len(idx_r)==0: continue
        
        idx_d, idx_r = idx_d[0], idx_r[0]
        if horas >= float(sim.loc[idx_d, "Horas Simulada (h)"]):
            inconsist.append(f"{doador}: horas maiores que a rota.")
            continue
            
        prod = float(sim.loc[idx_d, "Produtividade Ref"]) if pd.notna(sim.loc[idx_d, "Produtividade Ref"]) else 0.0
        tons = max(horas * prod, 0.0)
        sim = transferir_proporcional(sim, idx_d, idx_r, horas, tons)
        sim = recomputar(sim) 
        plano.append({"Setor Doador": doador, "Setor Receptor": receptor, "Horas Transferidas": format_horas_hhmmss(horas), "Toneladas Transferidas": round(tons, 2)})
        
    st.session_state["epico_manual_resultado"] = sim.copy()
    st.session_state["epico_manual_plano"] = pd.DataFrame(plano)
    st.session_state["epico_manual_incons"] = inconsist
    st.session_state["epico_relatorio_cenario"] = sim.copy()
    origem = f"Manual ({filtro_turno} | {filtro_freq})" if filtro_turno != "Todos" else "Manual (Geral)"
    st.session_state["epico_relatorio_origem"] = origem
    
    base_para_auto = rotas.copy()
    base_para_auto["Setor"] = base_para_auto["Setor"].astype(str).str.zfill(4)
    base_para_auto["Toneladas"] = base_para_auto["Setor"].map(dict(zip(sim["Setor"], sim["Toneladas Simulada"]))).fillna(base_para_auto["Toneladas"])
    base_para_auto["Horas Trabalhadas"] = base_para_auto["Setor"].map(dict(zip(sim["Setor"], sim["Horas Simulada (h)"]))).fillna(base_para_auto["Horas Trabalhadas"])
    base_para_auto["Viagens"] = base_para_auto["Setor"].map(dict(zip(sim["Setor"], sim["Viagens Projetadas"]))).fillna(base_para_auto["Viagens"])
    base_para_auto["Km Total"] = base_para_auto["Setor"].map(dict(zip(sim["Setor"], sim["Km Simulado"]))).fillna(base_para_auto["Km Total"])
    base_para_auto["Km Improdutivo"] = base_para_auto["Setor"].map(dict(zip(sim["Setor"], sim["Km Improdutivo Simulado"]))).fillna(base_para_auto["Km Improdutivo"])
    base_para_auto["Combustível"] = base_para_auto["Setor"].map(dict(zip(sim["Setor"], sim["Combustível Simulado"]))).fillna(base_para_auto["Combustível"])
    st.session_state["epico_rotas_manual_simulada"] = base_para_auto.copy()
    st.session_state["epico_nova_rota_criada"] = False

if c_clear.button("Limpar Resultados do Simulador"):
    for k in ["epico_rotas_manual_simulada","epico_manual_resultado","epico_manual_plano","epico_manual_incons","epico_relatorio_cenario","epico_relatorio_origem","epico_nova_rota_criada"]:
        st.session_state.pop(k, None)
    st.rerun()

res = st.session_state.get("epico_manual_resultado")
plano = st.session_state.get("epico_manual_plano")
incs = st.session_state.get("epico_manual_incons", [])

if incs:
    st.warning("Algumas transferências não puderam ser aplicadas:")
    for m in incs: st.markdown(f"- {m}")

if isinstance(res, pd.DataFrame) and not res.empty:
    st.subheader("3. Resultado da Simulação")
    if isinstance(plano, pd.DataFrame) and not plano.empty:
        st.dataframe(plano, use_container_width=True, hide_index=True)
    st.dataframe(df_apresentacao(res), use_container_width=True, hide_index=True)
    
    st.plotly_chart(grafico_horas(res, meta_equalizacao, limite_operacional, "Horas por setor - Atual x Simulado"), use_container_width=True)
    
    x,y = st.columns(2)
    with x: st.plotly_chart(grafico_grupos(res, "Toneladas por setor", "Ton Atual", "Toneladas Simulada", "Toneladas"), use_container_width=True)
    with y: st.plotly_chart(grafico_grupos(res, "Viagens por setor", "Viagens Atual", "Viagens Projetadas", "Viagens"), use_container_width=True)
        
    st.subheader("4. Demonstrativo de Ganhos Econômicos (DRE Financeiro)")
    g = ganhos_financeiros(res, preco_diesel, preco_arla, custo_pneu, vida_pneu, custo_manut, custo_he_equipe)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Economia Combustível (Diesel+ARLA)", f"R$ {format_number_br(g['eco_diesel'] + g['eco_arla'], 2)} /dia")
    col2.metric("Economia Desgaste (Pneus+Manut.)", f"R$ {format_number_br(g['eco_pneu'] + g['eco_manut'], 2)} /dia")
    col3.metric(f"Economia H.E. (Equipe)", f"R$ {format_number_br(g['eco_hora'], 2)} /dia")
    
    st.success(f"💰 **LUCRO LÍQUIDO MENSAL PROJETADO:** **R$ {format_number_br(g['lucro_liquido'], 2)}**")