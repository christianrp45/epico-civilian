import math
import pandas as pd
import streamlit as st
import plotly.express as px
from helpers import upload_and_filter_page
from kpis import compute_dashboard_data, format_horas_hhmmss, format_number_br

LIMITE_HORAS_PADRAO = 9 + 20 / 60
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

# --- MAPEAMENTO OPERACIONAL (DNA DE TRINDADE) ---
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

def ceil_viagens(toneladas, capacidade):
    if pd.isna(toneladas) or pd.isna(capacidade) or capacidade <= 0: return 0
    toneladas = max(float(toneladas), 0.0)
    return int(math.ceil(toneladas / float(capacidade))) if toneladas > 0 else 0

def ordenar_setores(df):
    ordem = pd.to_numeric(df["Setor"], errors="coerce").fillna(999999).astype(int)
    return df.assign(_ord=ordem).sort_values("_ord").drop(columns="_ord")

def construir_mapa_capacidade(rotas, prefixo="auto"):
    st.sidebar.subheader("Configuração de Frota")
    tipo_map, cap_map = {}, {}
    for setor in rotas["Setor"].astype(str).tolist():
        tipo = st.sidebar.selectbox(f"Tipo caminhão - Setor {setor}", options=list(CAPACIDADES.keys()), index=0, key=f"{prefixo}_{setor}")
        tipo_map[setor] = tipo
        cap_map[setor] = CAPACIDADES[tipo]
    return tipo_map, cap_map

def preparar(rotas, tipo_map, cap_map):
    df = rotas.copy()
    df["Setor"] = df["Setor"].astype(str).str.zfill(4)
    nums = ["Toneladas", "Viagens", "Km Produtivo", "Km Improdutivo", "Km Total", "Combustível", "Horas Trabalhadas", "Produtividade (t/h)"]
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
    df["Km Improdutivo Simulado"] = df["Km Improdutivo"]
    df["Horas Simulada (h)"] = df["Horas Trabalhadas"]
    df["Toneladas Simulada"] = df["Toneladas"]
    df["Ton Recebida do Doador"] = 0.0
    df["Ton Doada"] = 0.0
    df["Produtividade Ref"] = df["Produtividade (t/h)"].fillna(0)
    media_prod = df["Produtividade Ref"].replace([float("inf"), -float("inf")], pd.NA).dropna().mean()
    if pd.isna(media_prod): media_prod = 0.0
    df.loc[df["Produtividade Ref"] <= 0, "Produtividade Ref"] = media_prod
    return ordenar_setores(df)

def recomputar_fisica(df):
    out = df.copy()
    out["Viagens Projetadas"] = out.apply(lambda x: ceil_viagens(x["Toneladas Simulada"], x["Capacidade (t)"]), axis=1)
    novo_km_imp, nova_hr_imp = [], []
    for _, row in out.iterrows():
        v_orig = max(1, int(row["Viagens Atual"]))
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

# --- NOVO ALGORITMO C-LEVEL: TETRIS DE CAÇAMBA E EFEITO ESPONJA ---
def equalizar_inteligente(df, alvo_horas=None, nome="Base"):
    sim = df.copy()
    plano_raw = []
    if not alvo_horas: alvo_horas = float(sim["Horas Simulada (h)"].sum()) / max(len(sim), 1)

    for passo in range(1500):
        sim = recomputar_fisica(sim)
        
        doadores = sim[sim["Horas Simulada (h)"] > alvo_horas + (1/60)].sort_values("Horas Simulada (h)", ascending=False)
        receptores = sim[sim["Horas Simulada (h)"] < alvo_horas - (1/60)].copy()
        
        if doadores.empty or receptores.empty: break
        
        # 1. Efeito Esponja: Ordena receptores priorizando caminhões Trucados (Gigantes primeiro)
        receptores["_is_trucado"] = receptores["Tipo Caminhão"] == "Trucado"
        receptores = receptores.sort_values(["_is_trucado", "Horas Simulada (h)"], ascending=[False, True])

        houve_movimento = False

        for idx_d in doadores.index:
            for idx_r in receptores.index:
                excesso_h = float(sim.loc[idx_d, "Horas Simulada (h)"] - alvo_horas)
                deficit_h = float(alvo_horas - sim.loc[idx_r, "Horas Simulada (h)"])
                
                prod_d = float(sim.loc[idx_d, "Produtividade Ref"]) if pd.notna(sim.loc[idx_d, "Produtividade Ref"]) else 1.0
                if prod_d <= 0: prod_d = 1.0
                
                # Tons base para equilibrar apenas o relógio
                tons_alvo = min(excesso_h, deficit_h) * 0.5 * prod_d 
                
                # Lógica Física das Caçambas
                D_tons = float(sim.loc[idx_d, "Toneladas Simulada"])
                D_cap = float(sim.loc[idx_d, "Capacidade (t)"])
                R_tons = float(sim.loc[idx_r, "Toneladas Simulada"])
                R_cap = float(sim.loc[idx_r, "Capacidade (t)"])
                
                # Descobre se o Doador tem uma viagem "quase vazia" (Resto)
                D_resto = D_tons % D_cap
                if D_resto < 0.01: D_resto = D_cap
                
                # Descobre quanto espaço vazio o Receptor tem nas viagens atuais dele
                R_viagens = math.ceil(R_tons / R_cap) if R_tons > 0 else 1
                R_espaco_livre = (R_viagens * R_cap) - R_tons
                if R_espaco_livre < 0.01: R_espaco_livre = R_cap # Se tá cheio, permite abrir nova viagem

                tons_permitidas = tons_alvo

                # 2. Tetris: Se o resto do doador for pequeno, empurra ele inteiro para matar 1 viagem!
                if 0 < D_resto <= (tons_alvo * 1.5):
                    tons_permitidas = D_resto

                # 3. Trava de Ociosidade: Tenta não estourar a caçamba atual do Receptor (exceto se for Trucado)
                is_trucado = (sim.loc[idx_r, "Tipo Caminhão"] == "Trucado")
                if tons_permitidas > R_espaco_livre and not is_trucado:
                    tons_permitidas = R_espaco_livre

                if tons_permitidas < 0.05: continue
                
                # Executa a transferência de forma cirúrgica
                horas_permitidas = tons_permitidas / prod_d

                sim.loc[idx_d, "Horas Produtivas Simuladas"] = max(0.0, float(sim.loc[idx_d, "Horas Produtivas Simuladas"]) - horas_permitidas)
                sim.loc[idx_r, "Horas Produtivas Simuladas"] += horas_permitidas
                
                vel_d = float(sim.loc[idx_d, "Km Produtivo"]) / float(sim.loc[idx_d, "Horas Produtivas"]) if float(sim.loc[idx_d, "Horas Produtivas"])>0 else 10.0
                vel_r = float(sim.loc[idx_r, "Km Produtivo"]) / float(sim.loc[idx_r, "Horas Produtivas"]) if float(sim.loc[idx_r, "Horas Produtivas"])>0 else 10.0
                
                sim.loc[idx_d, "Km Produtivo Simulado"] = max(0.0, float(sim.loc[idx_d, "Km Produtivo Simulado"]) - (horas_permitidas * vel_d))
                sim.loc[idx_r, "Km Produtivo Simulado"] += (horas_permitidas * vel_r)
                
                sim.loc[idx_d, "Toneladas Simulada"] = max(0.0, float(sim.loc[idx_d, "Toneladas Simulada"]) - tons_permitidas)
                sim.loc[idx_r, "Toneladas Simulada"] += tons_permitidas
                sim.loc[idx_d, "Ton Doada"] += tons_permitidas
                sim.loc[idx_r, "Ton Recebida do Doador"] += tons_permitidas

                plano_raw.append({"Cenário": nome, "Setor Doador": str(sim.loc[idx_d, "Setor"]), "Setor Receptor": str(sim.loc[idx_r, "Setor"]), "Horas_Raw": horas_permitidas, "Toneladas_Raw": tons_permitidas})
                houve_movimento = True
                break
            if houve_movimento: break
        if not houve_movimento: break

    sim = recomputar_fisica(sim)
    plano_df = pd.DataFrame(plano_raw)
    if not plano_df.empty:
        plano_df = plano_df.groupby(["Cenário", "Setor Doador", "Setor Receptor"], as_index=False).sum()
        plano_df = plano_df[(plano_df["Horas_Raw"] >= (1/60)) | (plano_df["Toneladas_Raw"] >= 0.01)]
        plano_df["Horas Transferidas"] = plano_df["Horas_Raw"].apply(format_horas_hhmmss)
        plano_df["Toneladas Transferidas"] = plano_df["Toneladas_Raw"].round(2)
        plano_df = plano_df.sort_values(by="Toneladas_Raw", ascending=False)
        plano_df = plano_df[["Cenário", "Setor Doador", "Setor Receptor", "Horas Transferidas", "Toneladas Transferidas"]]
    else:
        plano_df = pd.DataFrame(columns=["Cenário", "Setor Doador", "Setor Receptor", "Horas Transferidas", "Toneladas Transferidas"])
    return sim, plano_df

def criar_nova_rota(df, meta_horas):
    sim = df.copy()
    novo_setor = str(int(pd.to_numeric(sim["Setor"], errors="coerce").max()) + 1).zfill(4)
    prod_media = sim["Produtividade Ref"].replace(0, pd.NA).mean()
    hr_improd_media = sim["Horas Improdutivas"].replace(0, pd.NA).dropna().mean()
    km_improd_media = sim["Km Improdutivo"].replace(0, pd.NA).dropna().mean()
    if pd.isna(hr_improd_media): hr_improd_media = 1.5
    if pd.isna(km_improd_media): km_improd_media = 25.0
    linha = {
        "Setor": novo_setor, "Toneladas": 0.0, "Viagens": 0, "Km Produtivo": 0.0,
        "Km Improdutivo": km_improd_media, "Km Total": km_improd_media, "Combustível": 0.0,
        "Horas Trabalhadas": hr_improd_media, "Horas Produtivas": 0.0, "Horas Improdutivas": hr_improd_media,
        "Tipo Caminhão": "Toco", "Capacidade (t)": CAPACIDADES["Toco"], "Horas Atual (h)": 0.0,
        "Ton Atual": 0.0, "Viagens Atual": 0, "Km Atual": 0.0, "Combustível Atual": 0.0,
        "Horas Produtivas Simuladas": 0.0, "Horas Improdutivas Simuladas": hr_improd_media,
        "Km Produtivo Simulado": 0.0, "Km Improdutivo Simulado": km_improd_media,
        "Horas Simulada (h)": hr_improd_media, "Toneladas Simulada": 0.0,
        "Ton Recebida do Doador": 0.0, "Ton Doada": 0.0,
        "Produtividade Ref": 0.0 if pd.isna(prod_media) else prod_media,
        "L_por_km_real": sim["L_por_km_real"].mean()
    }
    sim = pd.concat([sim, pd.DataFrame([linha])], ignore_index=True)
    sim = ordenar_setores(sim)
    novo_target = max(meta_horas, float(sim["Horas Simulada (h)"].sum()) / max(len(sim), 1))
    sim, plano = equalizar_inteligente(sim, novo_target, "Com nova rota")
    return sim, plano, novo_setor

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
    ex["Eficiência Atual"] = ex.apply(lambda x: calcular_eficiencia(x["Ton Atual"], x["Viagens Atual"], x["Capacidade (t)"]), axis=1)
    ex["Eficiência Sim."] = ex.apply(lambda x: calcular_eficiencia(x["Toneladas Simulada"], x["Viagens Projetadas"], x["Capacidade (t)"]), axis=1)
    for col in ["Ton Atual", "Toneladas Simulada", "Combustível Atual", "Combustível Simulado"]:
        ex[col] = pd.to_numeric(ex[col], errors="coerce").round(2)
    for col in ["Km Atual", "Km Simulado"]:
        ex[col] = pd.to_numeric(ex[col], errors="coerce").round(2)
    return ex[["Setor", "Turno", "Frequência", "Tipo Caminhão", "Eficiência Atual", "Eficiência Sim.", "Ton Atual", "Toneladas Simulada", "Horas Atual", "Horas Simulada", "Viagens Atual", "Viagens Projetadas", "Km Atual", "Km Simulado"]]

def grafico_horas(cenario, meta_horas, limite_horas, titulo):
    plot_df = ordenar_setores(cenario[["Setor", "Horas Atual (h)", "Horas Simulada (h)"]].copy())
    plot_df["Setor"] = plot_df["Setor"].astype(str)
    atual_max = float(plot_df["Horas Atual (h)"].max())
    long_df = plot_df.melt(id_vars="Setor", value_vars=["Horas Atual (h)", "Horas Simulada (h)"], var_name="Série", value_name="Horas")
    long_df["Série"] = long_df["Série"].replace({"Horas Atual (h)": "Horas Atual", "Horas Simulada (h)": "Horas Simulada"})
    fig = px.bar(long_df, x="Setor", y="Horas", color="Série", barmode="group", title=titulo)
    fig.update_xaxes(type="category")
    fig.add_hline(y=meta_horas, line_dash="dash", line_color="green", annotation_text=f"Meta ideal {format_horas_hhmmss(meta_horas)}")
    fig.add_hline(y=limite_horas, line_dash="dash", line_color="yellow", annotation_text=f"Limite legal {format_horas_hhmmss(limite_horas)}")
    fig.add_hline(y=atual_max, line_dash="dot", line_color="red", annotation_text=f"Topo atual real {format_horas_hhmmss(atual_max)}")
    return fig

def ganhos_financeiros(c, p_diesel, p_arla, p_pneu, v_pneu, c_manut, custo_he_equipe, custo_equipe_mensal, qtd_equipe, nova_rota_criada=False):
    delta_horas = max(0.0, float(c["Horas Atual (h)"].sum()) - float(c["Horas Simulada (h)"].sum()))
    delta_km = max(0.0, float(c["Km Atual"].sum()) - float(c["Km Simulado"].sum()))
    delta_litros = max(0.0, float(c["Combustível Atual"].sum()) - float(c["Combustível Simulado"].sum()))
    
    eco_diesel = delta_litros * p_diesel
    eco_arla = (delta_litros * 0.05) * p_arla
    eco_pneu = delta_km * (p_pneu / max(v_pneu, 1))
    eco_manut = delta_km * c_manut
    eco_hora = delta_horas * custo_he_equipe
    horas_homem = delta_horas * qtd_equipe  
    
    total_diario = eco_diesel + eco_arla + eco_pneu + eco_manut + eco_hora
    total_mensal = total_diario * 26 
    
    custo_nova_rota = custo_equipe_mensal if nova_rota_criada else 0.0
    lucro_liquido = total_mensal - custo_nova_rota
    
    return {
        "horas": delta_horas, "horas_homem": horas_homem, "km": delta_km, "litros": delta_litros,
        "eco_diesel": eco_diesel, "eco_arla": eco_arla, "eco_pneu": eco_pneu,
        "eco_manut": eco_manut, "eco_hora": eco_hora, "total_diario": total_diario,
        "total_mensal": total_mensal, "custo_nova_rota": custo_nova_rota, "lucro_liquido": lucro_liquido
    }

jornada_meta, df_filtrado = upload_and_filter_page("Equalização Automática", "Motor Tetris: Otimização de Caçambas e Filtros de Turno/Frequência.")
results = compute_dashboard_data(df_filtrado, jornada_meta=jornada_meta)
rotas = results["rotas"].copy()
if rotas.empty:
    st.warning("Não há rotas disponíveis para análise.")
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
    st.warning("Tente alterar o filtro de Turno e Frequência.")
    st.stop()

st.sidebar.subheader("🎯 Metas Operacionais")
meta_equalizacao = st.sidebar.number_input("Meta ideal (horas)", min_value=1.0, max_value=24.0, value=float(st.session_state.get("meta_operacional", META_PADRAO)), step=0.01)
limite_operacional = st.sidebar.number_input("Limite legal (horas)", min_value=1.0, max_value=24.0, value=float(LIMITE_HORAS_PADRAO), step=0.01)

st.sidebar.subheader("⚙️ Parâmetros Operacionais (Frota)")
preco_diesel = st.sidebar.number_input("Preço Diesel (R$/L)", min_value=0.0, value=float(st.session_state.get("preco_diesel", 6.23)), step=0.10)
preco_arla = st.sidebar.number_input("Preço ARLA 32 (R$/L)", min_value=0.0, value=float(st.session_state.get("preco_arla", 3.50)), step=0.10)
custo_pneu = st.sidebar.number_input("Custo Jogo Pneus (R$)", min_value=0.0, value=float(st.session_state.get("custo_pneu", 1500.0)), step=100.0)
vida_pneu = st.sidebar.number_input("Vida Útil Pneu (Km)", min_value=1, value=int(st.session_state.get("vida_pneu", 40000)), step=1000)
custo_manut = st.sidebar.number_input("Custo Manutenção (R$/Km)", min_value=0.0, value=float(st.session_state.get("custo_manut", 0.85)), step=0.05)

with st.sidebar.expander("👷 Parâmetros de Mão de Obra (Mensal)", expanded=False):
    qtd_coletores = st.number_input("Qtd de Coletores por Caminhão", min_value=1, value=int(st.session_state.get("qtd_coletores", 3)), step=1)
    qtd_equipe = 1 + qtd_coletores 
    pct_hora_extra = st.number_input("Adicional de Hora Extra (%)", min_value=0.0, value=float(st.session_state.get("pct_hora_extra", 50.0)), step=5.0)

    mot_salario = st.number_input("Salário Base (Mot.)", value=float(st.session_state.get("mot_salario", 2741.61)))
    mot_insalub = st.number_input("Insalubridade (Mot.)", value=float(st.session_state.get("mot_insalub", 1096.64)))
    mot_encargos = st.number_input("Encargos Trabalhistas (Mot.)", value=float(st.session_state.get("mot_encargos", 651.48)))
    mot_va = st.number_input("Vale Alimentação (Mot.)", value=float(st.session_state.get("mot_va", 708.50)))

    col_salario = st.number_input("Salário Base (Col.)", value=float(st.session_state.get("col_salario", 2053.20)))
    col_insalub = st.number_input("Insalubridade (Col.)", value=float(st.session_state.get("col_insalub", 821.28)))
    col_encargos = st.number_input("Encargos Trabalhistas (Col.)", value=float(st.session_state.get("col_encargos", 602.04)))
    col_va = st.number_input("Vale Alimentação (Col.)", value=float(st.session_state.get("col_va", 708.50)))

total_motorista = mot_salario + mot_insalub + mot_encargos + mot_va
total_coletor = col_salario + col_insalub + col_encargos + col_va
custo_equipe_mensal = total_motorista + (total_coletor * qtd_coletores)

mot_hora_normal = mot_salario / 220.0
col_hora_normal = col_salario / 220.0
fator_he = 1 + (pct_hora_extra / 100.0)
custo_he_equipe = (mot_hora_normal * fator_he) + ((col_hora_normal * fator_he) * qtd_coletores)

st.sidebar.markdown("---")
gerar_nova_rota = st.sidebar.checkbox("Permitir criação de nova rota de alívio", value=False)

tipo_map, cap_map = construir_mapa_capacidade(rotas, "auto")
base = preparar(rotas, tipo_map, cap_map)

st.subheader(f"1. Base Atual da Operação ({filtro_turno} | {filtro_freq})")
ex = base.copy()
ex["Horas Atual"] = ex["Horas Atual (h)"].apply(format_horas_hhmmss)
ex["Eficiência Atual"] = ex.apply(lambda x: calcular_eficiencia(x["Ton Atual"], x["Viagens Atual"], x["Capacidade (t)"]), axis=1)
st.dataframe(ex[["Setor", "Turno", "Frequência", "Tipo Caminhão", "Eficiência Atual", "Ton Atual", "Horas Atual", "Viagens Atual", "Km Atual"]], use_container_width=True, hide_index=True)

ca, cb = st.columns(2)
if ca.button("Gerar proposta automática"):
    sim_base_pre = base.copy()
    sim_base_pre["Capacidade (t)"] = CAP_BASE_TOCO
    sim_base_pre = recomputar_fisica(sim_base_pre)
    sim_base, plano_base = equalizar_inteligente(sim_base_pre, None, "Base Original Equalizada")
    
    sim_frota_pre = base.copy()
    sim_frota_pre = recomputar_fisica(sim_frota_pre)
    sim_frota, plano_frota = equalizar_inteligente(sim_frota_pre, None, "Frota Manual Equalizada")
    
    if gerar_nova_rota and float(sim_frota["Horas Simulada (h)"].max()) > limite_operacional + 1e-9:
        sim_frota, plano_frota, novo = criar_nova_rota(sim_frota, meta_equalizacao)
        st.session_state["epico_nova_rota_criada"] = True
    else:
        st.session_state["epico_nova_rota_criada"] = False
        
    st.session_state["epico_auto_base"] = sim_base.copy()
    st.session_state["epico_auto_plano_base"] = plano_base.copy()
    st.session_state["epico_auto_frota"] = sim_frota.copy()
    st.session_state["epico_auto_plano_frota"] = plano_frota.copy()

if cb.button("Limpar Resultados da Equalização Automática"):
    for k in ["epico_auto_base", "epico_auto_plano_base", "epico_auto_frota", "epico_auto_plano_frota", "epico_nova_rota_criada"]: st.session_state.pop(k, None)
    st.rerun()

res_base = st.session_state.get("epico_auto_base")
res_frota = st.session_state.get("epico_auto_frota")
plano_frota = st.session_state.get("epico_auto_plano_frota")
flag_nova_rota = st.session_state.get("epico_nova_rota_criada", False)

if isinstance(res_frota, pd.DataFrame) and not res_frota.empty:
    st.subheader(f"2. Resultado da Simulação {'(Com Nova Rota)' if flag_nova_rota else '(Frota Otimizada)'}")
    if isinstance(plano_frota, pd.DataFrame) and not plano_frota.empty: st.dataframe(plano_frota, use_container_width=True, hide_index=True)
    st.dataframe(df_apresentacao(res_frota), use_container_width=True, hide_index=True)

    st.plotly_chart(grafico_horas(res_frota, meta_equalizacao, limite_operacional, "Horas por setor - Pós-Simulação"), use_container_width=True)

    st.subheader("3. Demonstrativo de Ganhos Econômicos (DRE Financeiro)")
    g = ganhos_financeiros(res_frota, preco_diesel, preco_arla, custo_pneu, vida_pneu, custo_manut, custo_he_equipe, custo_equipe_mensal, qtd_equipe, flag_nova_rota)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Economia Combustível (Diesel+ARLA)", f"R$ {format_number_br(g['eco_diesel'] + g['eco_arla'], 2)} /dia")
    col2.metric("Economia Desgaste (Pneus+Manut.)", f"R$ {format_number_br(g['eco_pneu'] + g['eco_manut'], 2)} /dia")
    col3.metric(f"Economia H.E. ({qtd_equipe} vidas/rota)", f"R$ {format_number_br(g['eco_hora'], 2)} /dia", f"{format_horas_hhmmss(g['horas_homem'])} Horas-Homem ganhas")
    
    st.markdown(f"### Lucro Bruto da Operação (Mensal): **R$ {format_number_br(g['total_mensal'], 2)}**")
    
    if flag_nova_rota:
        st.warning(f"⚠️ **Atenção:** Uma nova rota foi criada para aliviar a frota. Custo da nova equipe (com todos os encargos): **- R$ {format_number_br(g['custo_nova_rota'], 2)} /mês**")
        if g['lucro_liquido'] > 0:
            st.success(f"💰 **ROI POSITIVO:** Mesmo pagando a nova equipe, a empresa ainda lucra **R$ {format_number_br(g['lucro_liquido'], 2)}** por mês!")
        else:
            st.error(f"📉 **ROI NEGATIVO:** O custo da nova equipe superou a economia gerada. Prejuízo de **R$ {format_number_br(g['lucro_liquido'], 2)}** por mês.")
    else:
        st.success(f"💰 **LUCRO LÍQUIDO MENSAL PROJETADO:** **R$ {format_number_br(g['lucro_liquido'], 2)}**")

    s1, s2 = st.columns(2)
    if s1.button("Salvar Cenário Base para o Relatório"):
        st.session_state["epico_relatorio_cenario"] = res_base.copy()
        origem = f"Automática ({filtro_turno} | {filtro_freq})" if filtro_turno != "Todos" else "Automática (Geral)"
        st.session_state["epico_relatorio_origem"] = origem
        st.success("Cenário salvo!")
    if s2.button("Salvar Cenário Otimizado para o Relatório"):
        st.session_state["epico_relatorio_cenario"] = res_frota.copy()
        origem = f"Automática ({filtro_turno} | {filtro_freq})" if filtro_turno != "Todos" else "Automática (Geral)"
        st.session_state["epico_relatorio_origem"] = origem
        st.success("Cenário salvo!")
