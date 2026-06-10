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
    long_df = plot_df.melt(id_vars="Setor", value_vars=["Horas Atual (h)", "Horas Simulada (h)"], var_name="Série", value_name="Horas")
    long_df["Série"] = long_df["Série"].replace({"Horas Atual (h)": "Horas Atual", "Horas Simulada (h)": "Horas Simulada"})
    fig = px.bar(long_df, x="Setor", y="Horas", color="Série", barmode="group", title=titulo)
    fig.update_xaxes(type="category")
    fig.add_hline(y=meta_horas, line_dash="dash", line_color="green", annotation_text=f"Meta")
    fig.add_hline(y=limite_horas, line_dash="dash", line_color="red", annotation_text=f"Limite Legal")
    return fig

def build_pdf(cenario_df, origem, texto_alerta, texto_resumo, texto_praticas, dre_data, cidade_ativa):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []

    logo_path = "logo-quebec-epico.png"
    if os.path.exists(logo_path):
        try:
            story.append(Image(logo_path, width=5*cm, height=1.5*cm))
            story.append(Spacer(1, 10))
        except: pass

    story.append(Paragraph("RELATÓRIO LOGÍSTICO EXECUTIVO — PLATAFORMA ÉPICO", styles["EPTitle"]))
    story.append(Paragraph("Otimização Estratégica e Inteligência de Transportes", styles["EPSub"]))
    story.append(Spacer(1, 15))

    meta_texto = f"""
    <b>Cidade Analisada:</b> {cidade_ativa}<br/>
    <b>Departamento:</b> Torre de Controle e Monitoramento Inteligente<br/>
    <b>Engenheiro de Otimização:</b> Christian Rodrigues<br/>
    <b>Origem do Cenário:</b> {origem}<br/>
    """
    story.append(Paragraph(meta_texto, styles["BodyText"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("1. Diagnóstico de Gargalos (Baseline Operacional)", styles["Heading2"]))
    story.append(Paragraph(texto_alerta, styles["EPAlert"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("2. Demonstração Financeira da Otimização (DRE & ROI)", styles["Heading2"]))
    story.append(Paragraph(texto_resumo, styles["EPSuccess"]))
    story.append(Spacer(1, 8))

    t_dre = Table(dre_data, colWidths=[12*cm, 5*cm])
    t_dre.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123B6D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E2EFDA")), 
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

# CAPTURA DA CIDADE ATIVA SALVA EM MEMÓRIA
cidade_selecionada = st.session_state.get("global_cidade_ativa", "Trindade")

st.markdown(f"""
**Cidade Analisada:** {cidade_selecionada}  
**Departamento:** Torre de Controle e Monitoramento Inteligente  
**Engenheiro de Otimização:** Christian Rodrigues  
""")
st.markdown("---")

meta_op = st.session_state.get("meta_operacional", META_PADRAO)
preco_diesel = st.session_state.get("preco_diesel", 6.23)
preco_arla = st.session_state.get("preco_arla", 3.50)
custo_pneu = st.session_state.get("custo_pneu", 1500.0)
vida_pneu = st.session_state.get("vida_pneu", 40000)
custo_manut = st.session_state.get("custo_manut", 0.85)

qtd_coletores = st.session_state.get("qtd_coletores", 3)
qtd_equipe = 1 + qtd_coletores
pct_hora_extra = st.session_state.get("pct_hora_extra", 50.0)
custo_he = st.session_state.get("custo_he_h", 45.0)

cenario = st.session_state.get("epico_relatorio_cenario")
origem_salva = st.session_state.get("epico_relatorio_origem", "Nenhum cenário salvo")

if cenario is None or not isinstance(cenario, pd.DataFrame) or cenario.empty:
    st.warning("⚠️ **Nenhum cenário de simulação foi localizado na memória.** Por favor, vá até a página de 'Simulador Executivo' ou 'Equalização Automática', execute os cálculos e clique em 'Salvar Cenário' antes de extrair o relatório.")
    st.stop()

# --- EQUAÇÕES DE DRE COMPARATIVO ---
v_atual = cenario["Viagens Atual"].sum()
v_sim = cenario["Viagens Projetadas"].sum()
km_atual = cenario["Km Atual"].sum()
km_sim = cenario["Km Simulado"].sum()
diesel_atual = cenario["Combustível Atual"].sum()
diesel_sim = cenario["Combustível Simulado"].sum()

he_atual = (cenario["Horas Atual (h)"] - meta_op).clip(lower=0).sum()
he_sim = (cenario["Horas Simulada (h)"] - meta_op).clip(lower=0).sum()
horas_homem = (cenario["Horas Atual (h)"] - cenario["Horas Simulada (h)"]).clip(lower=0).sum() * qtd_equipe * 26

# Financeiro puro
custo_diesel_at = diesel_atual * preco_diesel
custo_diesel_sim = diesel_sim * preco_diesel
custo_he_at = he_atual * custo_he
custo_he_sim = he_sim * custo_he

custo_pneu_at = km_atual * (custo_pneu / vida_pneu)
custo_pneu_sim = km_sim * (custo_pneu / vida_pneu)
custo_manut_at = km_atual * custo_manut
custo_manut_sim = km_sim * custo_manut

opex_atual = custo_diesel_at + custo_he_at + custo_pneu_at + custo_manut_at
opex_simulado = custo_diesel_sim + custo_he_sim + custo_pneu_sim + custo_manut_sim

vazamento_mensal = opex_atual * 26
economia_diaria = opex_atual - opex_simulado
economia_mensal = economia_diaria * 26

flag_nova_rota = "Criar nova equipe" in origem_salva or cenario["Horas Simulada (h)"].max() > LIMITE_HORAS_PADRAO
custo_folha_nova_rota = 22000.0 if flag_nova_rota else 0.0
lucro_liquido = economia_mensal - custo_folha_nova_rota

dre_data = [
    ["INDICADORES DE RESULTADO OPERACIONAL", "VALORES PROJETADOS"],
    ["Total de Viagens/Dia (Cenário Histórico)", f"{v_atual:.0f} viagens"],
    ["Total de Viagens/Dia (Cenário Otimizado)", f"{v_sim:.0f} viagens"],
    ["Rodagem Mensal Estimada (Histórico)", f"{km_atual*26:,.1f} km"],
    ["Rodagem Mensal Estimada (Otimizado)", f"{km_sim*26:,.1f} km"],
    ["Custo Mensal de Diesel (Histórico)", f"R$ {format_number_br(custo_diesel_at*26, 2)}"],
    ["Custo Mensal de Diesel (Otimizado)", f"R$ {format_number_br(custo_diesel_sim*26, 2)}"],
    ["Custo Mensal de Horas Extras (Histórico)", f"R$ {format_number_br(custo_he_at*26, 2)}"],
    ["Custo Mensal de Horas Extras (Otimizado)", f"R$ {format_number_br(custo_he_sim*26, 2)}"],
    ["Despesa Operacional Total (Histórico)", f"R$ {format_number_br(opex_atual*26, 2)}"],
    ["Despesa Operacional Total (Otimizado)", f"R$ {format_number_br(opex_simulado*26, 2)}"],
    ["ECONOMIA BRUTA MENSAL DO PROJETO", f"R$ {format_number_br(economia_mensal, 2)}"],
    ["Custo de Expansão de Frota (Nova Rota)", f"R$ {format_number_br(custo_folha_nova_rota, 2)}"],
    ["LUCRO OPERACIONAL LÍQUIDO (MÊS)", f"R$ {format_number_br(lucro_liquido, 2)}"]
]

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
<b>3. Minimização de Viagens (Física Geográfica):</b> O envio de lixo para setores distantes do aterro foi violentamente bloqueado se exigir uma viagem adicional.<br/>
<b>4. Gestão pelo Efeito Multiplicador (Horas-Homem):</b> Fica estabelecido que cada 1 hora de atraso da frota custa 4 hours de folha de pagamento à empresa. A otimização focará no resgate ágil dos veículos para preservar a margem de lucro projetada.
"""

st.subheader("1. O Custo da Ineficiência Atual (Baseline)")
st.error(texto_alerta)

st.subheader("2. Resultados da Otimização (DRE Projetado)")
st.success(texto_resumo)

st.markdown("### Demonstrativo de Resultados do Exercício (DRE Mensal)")
df_dre_view = pd.DataFrame(dre_data[1:], columns=dre_data[0])
st.dataframe(df_dre_view, use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("3. Melhores Práticas e Recomendações Estratégicas")
st.markdown(texto_praticas, unsafe_allow_html=True)

# 🧠 --- INJEÇÃO DO PARECER DA IA NO RELATÓRIO EXECUTIVO ---
parecer_ia = st.session_state.get("epico_parecer_ia_salvo")
cidade_ia = st.session_state.get("epico_parecer_ia_cidade")

if parecer_ia and cidade_ia == cidade_selecionada:
    st.markdown("---")
    st.subheader("🧠 Parecer Consultivo Autônomo (Inteligência Artificial)")
    st.info("💡 Este trecho foi auditado e gerado pelo Co-Piloto Gemini com base nos dados reais de balança e rodagem desta unidade.")
    st.markdown(parecer_ia)

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
pdf_buffer = build_pdf(cenario, origem_salva, texto_alerta, texto_resumo, texto_praticas, dre_data, cidade_selecionada)
st.download_button(label="📄 Baixar PDF do Relatório Executivo (Para Aprovação)", data=pdf_buffer, file_name=f"relatorio_diretoria_{cidade_selecionada.lower()}.pdf", mime="application/pdf")