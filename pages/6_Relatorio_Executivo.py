import io
import os
import pandas as pd
import streamlit as st
import plotly.express as px
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from helpers import upload_and_filter_page
from kpis import compute_dashboard_data, format_horas_hhmmss, format_number_br

META_PADRAO = 7 + 20 / 60
LIMITE_HORAS_PADRAO = 9 + 20 / 60
FATOR_CO2_DIESEL = 2.64  

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="EPTitle", fontSize=18, leading=22, textColor=colors.HexColor("#123B6D")))
styles.add(ParagraphStyle(name="EPSub", fontSize=12, leading=15, textColor=colors.HexColor("#2E5C99")))
styles.add(ParagraphStyle(name="EPAlert", fontSize=10, leading=14, textColor=colors.darkred, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle(name="EPSuccess", fontSize=10, leading=14, textColor=colors.green, fontName="Helvetica-Bold"))

def ordenar_setores(df):
    ordem = pd.to_numeric(df["Setor"], errors="coerce").fillna(999999).astype(int)
    return df.assign(_ord=ordem).sort_values("_ord").drop(columns="_ord")

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
    return fig

def grafico_grupos(cenario, titulo, col_a, col_b, rotulo):
    plot_df = ordenar_setores(cenario[["Setor", col_a, col_b]].copy())
    plot_df["Setor"] = plot_df["Setor"].astype(str)
    long_df = plot_df.melt(id_vars="Setor", value_vars=[col_a, col_b], var_name="Série", value_name=rotulo)
    long_df["Série"] = long_df["Série"].replace({col_a: "Atual", col_b: "Simulado"})
    fig = px.bar(long_df, x="Setor", y=rotulo, color="Série", barmode="group", title=titulo)
    fig.update_xaxes(type="category")
    return fig

def build_pdf(cenario_df, origem, texto_alerta, texto_resumo, texto_praticas, dre_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=1.6*cm, rightMargin=1.6*cm, topMargin=1.6*cm, bottomMargin=1.6*cm)
    story = []
    
    logo_path = "logo-quebec-epico.png"
    if os.path.exists(logo_path):
        img = Image(logo_path, width=4*cm, height=1.5*cm, kind='proportional')
        img.hAlign = 'LEFT'
        story.append(img)
        story.append(Spacer(1, 10))
    
    story.append(Paragraph("Relatório Executivo de Engenharia e Operações - EPICO", styles["EPTitle"]))
    story.append(Spacer(1, 8))
    
    cabecalho = f"""
    <b>Cidade Analisada:</b> Trindade de Goiás - GO<br/>
    <b>Departamento:</b> Torre de Controle e Monitoramento Inteligente<br/>
    <b>Gerente e Engenheiro de Otimização:</b> Christian Rodrigues<br/>
    <b>Origem do cenário projetado:</b> {origem}
    """
    story.append(Paragraph(cabecalho, styles["EPSub"]))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("1. O Custo da Ineficiência Atual (Diagnóstico Base)", styles["Heading2"]))
    story.append(Paragraph(texto_alerta, styles["EPAlert"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("2. Resultados da Otimização (DRE & ROI)", styles["Heading2"]))
    story.append(Paragraph(texto_resumo, styles["EPSuccess"]))
    story.append(Spacer(1, 8))

    # --- NOVA TABELA FINANCEIRA DRE NO PDF ---
    t_dre = Table(dre_data, colWidths=[12*cm, 5*cm])
    t_dre.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123B6D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E2EFDA")), # Destaca a linha de Lucro
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_dre)
    story.append(Spacer(1, 15))

    story.append(Paragraph("3. Melhores Práticas Operacionais Implementadas na Simulação", styles["Heading2"]))
    story.append(Paragraph(texto_praticas, styles["BodyText"]))
    story.append(Spacer(1, 12))

    tabela = cenario_df.copy()
    if "Horas Atual (h)" in tabela.columns: tabela["Horas Atual"] = tabela["Horas Atual (h)"].apply(format_horas_hhmmss)
    if "Horas Simulada (h)" in tabela.columns: tabela["Horas Simulada"] = tabela["Horas Simulada (h)"].apply(format_horas_hhmmss)

    cols = [c for c in ["Setor", "Eficiência Sim.", "Capacidade (t)", "Ton Atual", "Toneladas Simulada", "Horas Atual", "Horas Simulada", "Viagens Atual", "Viagens Projetadas", "Km Atual", "Km Simulado", "Combustível Atual", "Combustível Simulado"] if c in tabela.columns]
    
    dados = [cols]
    for _, row in tabela[cols].iterrows():
        linha = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                if c in ["Km Atual", "Km Simulado"]: linha.append(f"{v:.2f}")
                elif "Ton" in c or "Combustível" in c: linha.append(f"{v:.4f}")
                else: linha.append(f"{v:.2f}")
            else:
                linha.append(str(v))
        dados.append(linha)

    t = Table(dados, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123B6D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))
    
    story.append(Paragraph("4. Detalhamento Técnico Pós-Simulação por Setor", styles["Heading2"]))
    story.append(t)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

jornada_meta, df_filtrado = upload_and_filter_page(
    "Relatório Executivo",
    "Apresentação C-Level: Diagnóstico de Vazamento de Caixa, DRE Projetado e Diretrizes Operacionais."
)

results = compute_dashboard_data(df_filtrado, jornada_meta=jornada_meta)
rotas = results["rotas"].copy()

logo_path = "logo-quebec-epico.png"
if os.path.exists(logo_path): st.image(logo_path, width=250)

st.title("Relatório Executivo - Aprovação C-Level")

st.markdown("""
**Cidade Analisada:** Trindade de Goiás - GO  
**Departamento:** Torre de Controle e Monitoramento Inteligente  
**Engenheiro de Otimização:** Christian Rodrigues  
""")
st.markdown("---")

# Puxa os dados da memória se existirem, senão usa os padrões
meta_op = st.session_state.get("meta_operacional", META_PADRAO)
preco_diesel = st.session_state.get("preco_diesel", 6.23)
preco_arla = st.session_state.get("preco_arla", 3.50)
custo_pneu = st.session_state.get("custo_pneu", 1500.0)
vida_pneu = st.session_state.get("vida_pneu", 40000)
custo_manut = st.session_state.get("custo_manut", 0.85)

qtd_coletores = st.session_state.get("qtd_coletores", 3)
qtd_equipe = 1 + qtd_coletores
pct_hora_extra = st.session_state.get("pct_hora_extra", 50.0)
mot_salario = st.session_state.get("mot_salario", 2741.61)
mot_insalub = st.session_state.get("mot_insalub", 1096.64)
mot_encargos = st.session_state.get("mot_encargos", 651.48)
mot_va = st.session_state.get("mot_va", 708.50)
col_salario = st.session_state.get("col_salario", 2053.20)
col_insalub = st.session_state.get("col_insalub", 821.28)
col_encargos = st.session_state.get("col_encargos", 602.04)
col_va = st.session_state.get("col_va", 708.50)

st.sidebar.subheader("⚙️ Parâmetros Financeiros Utilizados")
st.sidebar.info("Os valores abaixo foram puxados automaticamente da memória global do sistema.")
st.sidebar.write(f"**Diesel:** R$ {preco_diesel:.2f}/L")
st.sidebar.write(f"**Pneu:** R$ {custo_pneu:.2f}")
st.sidebar.write(f"**Adicional H.E.:** {pct_hora_extra}%")

total_motorista = mot_salario + mot_insalub + mot_encargos + mot_va
total_coletor = col_salario + col_insalub + col_encargos + col_va
custo_equipe_mensal = total_motorista + (total_coletor * qtd_coletores)

mot_hora_normal = mot_salario / 220.0
col_hora_normal = col_salario / 220.0
fator_he = 1 + (pct_hora_extra / 100.0)
custo_he_equipe = (mot_hora_normal * fator_he) + ((col_hora_normal * fator_he) * qtd_coletores)

cenario_salvo = st.session_state.get("epico_relatorio_cenario")
origem_salva = st.session_state.get("epico_relatorio_origem", "Sem origem definida")
flag_nova_rota = st.session_state.get("epico_nova_rota_criada", False)

if not isinstance(cenario_salvo, pd.DataFrame) or cenario_salvo.empty:
    st.warning("📊 Nenhum cenário salvo foi encontrado. Vá até os Simuladores e clique em 'Salvar Cenário'.")
    st.stop()

st.success(f"✅ Cenário ativo projetado a partir de: **{origem_salva}**")
cenario = cenario_salvo.copy()

# CÁLCULOS ANTES (Vazamento Atual)
if "L_por_km_real" not in cenario.columns: cenario["L_por_km_real"] = (cenario["Combustível Atual"] / cenario["Km Atual"].replace(0, 1)).fillna(0)
he_antes = (cenario["Horas Atual (h)"] - meta_op).clip(lower=0).sum()
litros_imp_antes = (cenario["Km Improdutivo"] * cenario["L_por_km_real"]).sum()
km_imp_antes = cenario["Km Improdutivo"].sum()

vazamento_mensal = (
    (he_antes * custo_he_equipe) +
    (litros_imp_antes * preco_diesel) +
    ((litros_imp_antes * 0.05) * preco_arla) +
    (km_imp_antes * (custo_pneu / max(vida_pneu, 1))) +
    (km_imp_antes * custo_manut)
) * 26

# CÁLCULOS DEPOIS (Otimização)
horas_antes = float(cenario["Horas Atual (h)"].sum())
horas_depois = float(cenario["Horas Simulada (h)"].sum())
km_antes = float(cenario["Km Atual"].sum())
km_depois = float(cenario["Km Simulado"].sum())
litros_antes = float(cenario["Combustível Atual"].sum())
litros_depois = float(cenario["Combustível Simulado"].sum())

delta_horas = max(0.0, horas_antes - horas_depois)
horas_homem = delta_horas * qtd_equipe 
delta_km = max(0.0, km_antes - km_depois)
delta_litros = max(0.0, litros_antes - litros_depois)

eco_diesel = delta_litros * preco_diesel
eco_arla = (delta_litros * 0.05) * preco_arla
eco_pneu = delta_km * (custo_pneu / max(vida_pneu, 1))
eco_manut = delta_km * custo_manut
eco_hora = delta_horas * custo_he_equipe

lucro_bruto_mensal = (eco_diesel + eco_arla + eco_pneu + eco_manut + eco_hora) * 26
custo_nova_rota = custo_equipe_mensal if flag_nova_rota else 0.0
lucro_liquido = lucro_bruto_mensal - custo_nova_rota

# MONTAGEM DA TABELA DRE PARA O PDF
dre_data = [
    ["Rubrica de Custo (OPEX)", "Economia Mensal Projetada"],
    ["Combustível (Diesel + ARLA 32)", f"R$ {format_number_br((eco_diesel + eco_arla) * 26, 2)}"],
    ["Desgaste de Frota (Pneus + Manutenção)", f"R$ {format_number_br((eco_pneu + eco_manut) * 26, 2)}"],
    ["Passivo Trabalhista (Horas Extras Poupadas)", f"R$ {format_number_br(eco_hora * 26, 2)}"],
    ["LUCRO BRUTO OPERACIONAL (MÊS)", f"R$ {format_number_br(lucro_bruto_mensal, 2)}"]
]
if flag_nova_rota:
    dre_data.append(["Custo da Nova Equipe (Contratação/Mês)", f"- R$ {format_number_br(custo_nova_rota, 2)}"])
    
dre_data.append(["LUCRO LÍQUIDO FINAL DE CAIXA (MÊS)", f"R$ {format_number_br(lucro_liquido, 2)}"])


# TEXTOS DO RELATÓRIO
texto_alerta = f"🚨 DIAGNÓSTICO: A operação em seu formato original apresenta um 'Custo Oculto' (vazamento de caixa) projetado em R$ {format_number_br(vazamento_mensal, 2)} ao mês, decorrente do pagamento de Horas Extras e manutenção de frotas rodando vazias (Km Improdutivo)."

if flag_nova_rota:
    texto_resumo = f"✅ ROI DA DECISÃO: A otimização exigiu a criação de uma NOVA ROTA para garantir a saúde da operação, preservando {format_horas_hhmmss(horas_homem)} HORAS-HOMEM mensais em passivo de fadiga. Mesmo abatendo o custo da folha da nova equipe contratada, a empresa garante um lucro final conforme detalhado abaixo:"
else:
    texto_resumo = f"✅ ROI DA DECISÃO: A equalização da frota ATUAL reduziu drasticamente a ociosidade e eliminou {format_horas_hhmmss(horas_homem)} HORAS-HOMEM mensais de passivo físico nas ruas. A estratégia entrega um corte direto de OPEX sem a necessidade de inflar a base com novas contratações, conforme detalhado abaixo:"

texto_praticas = """
Para manter este cenário de alta performance, propomos as seguintes Diretrizes Operacionais (implantadas no cérebro matemático desta plataforma):<br/>
<br/>
<b>1. Trava de Sobrecarga (Capacidade Nominal):</b> Veículos não devem ultrapassar 100% de sua capacidade técnica na viagem (ex: 9,5t para Toco). Exceder este limite eleva exponencialmente os custos com molas, pneus e consumo de diesel.<br/>
<b>2. Banda de Eficiência Mínima (70%):</b> Caminhões viajando ao aterro com menos de 70% da capacidade configuram subutilização ("bater lata"), aumentando o Custo por Tonelada (R$/ton). O lixo deve ser redistribuído para otimizar as caixas compactadoras.<br/>
<b>3. Minimização de Viagens (Física Geográfica):</b> O envio de lixo para setores distantes do aterro foi bloqueado se exigir uma viagem adicional.<br/>
<b>4. Gestão pelo Efeito Multiplicador (Horas-Homem):</b> Fica estabelecido que cada 1 hora de atraso da frota custa 4 horas de folha de pagamento à empresa. A otimização focará no resgate ágil dos veículos para preservar a margem de lucro projetada.
"""

st.subheader("1. O Custo da Ineficiência Atual (Baseline)")
st.error(texto_alerta)

st.subheader("2. Resultados da Otimização (DRE Projetado)")
st.success(texto_resumo)

# Monta o visual do DRE na tela também para espelhar o PDF
st.markdown("### Demonstrativo de Resultados do Exercício (DRE Mensal)")
df_dre_view = pd.DataFrame(dre_data[1:], columns=dre_data[0])
st.dataframe(df_dre_view, use_container_width=True, hide_index=True)

st.markdown("---")

st.subheader("3. Melhores Práticas e Recomendações Estratégicas")
st.markdown(texto_praticas, unsafe_allow_html=True)

st.markdown("---")

st.subheader("4. Comprovação do Cenário (Gráficos)")
st.plotly_chart(grafico_horas(cenario, meta_op, LIMITE_HORAS_PADRAO, "Impacto nas Horas por Setor"), use_container_width=True)

st.subheader("5. Anexo de Dados Pós-Simulação")
exibir = cenario.copy()
if "Horas Atual (h)" in exibir.columns: exibir["Horas Atual"] = exibir["Horas Atual (h)"].apply(format_horas_hhmmss)
if "Horas Simulada (h)" in exibir.columns: exibir["Horas Simulada"] = exibir["Horas Simulada (h)"].apply(format_horas_hhmmss)
cols = [c for c in ["Setor", "Tipo Caminhão", "Eficiência Sim.", "Ton Atual", "Toneladas Simulada", "Horas Atual", "Horas Simulada", "Viagens Atual", "Viagens Projetadas", "Km Atual", "Km Simulado", "Combustível Atual", "Combustível Simulado"] if c in exibir.columns]
st.dataframe(exibir[cols], use_container_width=True, hide_index=True)

st.markdown("### Exportação para Diretoria")
pdf_buffer = build_pdf(cenario, origem_salva, texto_alerta, texto_resumo, texto_praticas, dre_data)
st.download_button(label="📄 Baixar PDF do Relatório Executivo (Para Aprovação)", data=pdf_buffer, file_name="relatorio_diretoria_quebec.pdf", mime="application/pdf")