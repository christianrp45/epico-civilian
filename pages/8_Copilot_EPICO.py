import streamlit as st
import pandas as pd
import google.generativeai as genai
from helpers import upload_and_filter_page
from kpis import compute_dashboard_data, format_horas_hhmmss, format_number_br

st.set_page_config(page_title="ÉPICO - Co-Piloto IA", layout="wide")

st.title("🤖 Co-Piloto Inteligente ÉPICO")
st.caption("Consultoria analítica em tempo real alimentada pelo Google Gemini. Obtenha diagnósticos e sugestões de otimização automáticas.")

# 1. Recupera os dados filtrados da cidade ativa
jornada_meta, df_filtrado = upload_and_filter_page(
    "Análise Prescritiva de IA", 
    "O cérebro da inteligência artificial examinando a sua frota."
)

results = compute_dashboard_data(df_filtrado, jornada_meta=jornada_meta)
rotas = results["rotas"].copy()

# 2. Configuração da Chave de API do Gemini
# Para testar, você pode colar sua chave direto aqui ou usar o st.text_input
st.sidebar.subheader("🔑 Autenticação da IA")
api_key = st.sidebar.text_input("Insira sua Gemini API Key:", type="password", value=st.session_state.get("gemini_api_key", ""))

if api_key:
    st.session_state["gemini_api_key"] = api_key
    genai.configure(api_key=api_key)
else:
    st.warning("⚠️ Insira a sua Gemini API Key na barra lateral para ativar o Co-Piloto de IA.")
    st.stop()

# 3. Preparação do Contexto Operacional em formato de texto para a IA ler
cidade_atual = st.session_state.get("global_cidade_ativa", "Trindade")

# Monta um resumo dos top 5 setores mais críticos em horas extras
top_estourados = rotas.sort_values(by="Horas Trabalhadas", ascending=False).head(5)
resumo_setores_texto = ""
for _, row in top_estourados.iterrows():
    resumo_setores_texto += f"- Setor {row['Setor']}: Jornada de {format_horas_hhmmss(row['Horas Trabalhadas'])}, Peso Coletado: {row['Toneladas']:.2f}t, Km Improdutivo: {row['Km Improdutivo']:.1f}km.\n"

# 4. Interface e Disparo do Prompt
st.markdown("### 📋 Solicitar Diagnóstico Prescritivo")
st.markdown("O robô vai analisar a jornada de trabalho, o peso das caçambas e o desperdício de quilometragem para sugerir as melhores transferências manuais de horas.")

if st.button("🚀 Disparar Análise da Inteligência Artificial", type="primary", use_container_width=True):
    with st.spinner("O Gemini está examinando a física logística da sua frota... Aguarde."):
        try:
            # Seleciona o modelo correto e atualizado do Gemini
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            # Engenharia de Prompt focada em Logística Reversa de Resíduos
            prompt = f"""
            Você é o Engenheiro Chefe de Otimização Logística da Ecolabs. Sua missão é analisar os dados reais da frota de coleta de lixo da cidade de {cidade_atual} e propor melhorias drásticas baseadas nas regras do negócio.
            
            Regras Físicas do Sistema:
            - A jornada ideal (Meta) é de 7 horas e 20 minutos (7.33h decimais).
            - O limite crítico aceitável é de 9 horas e 20 minutos (9.33h decimais). Qualquer setor acima disso gera risco de acidentes e passivo trabalhista.
            - A capacidade técnica nominal de um caminhão Toco é de 9.5 toneladas.

            Aqui estão os dados operacionais dos setores mais críticos em horas extras atualmente:
            {resumo_setores_texto}
            
            Por favor, gere um relatório executivo dividido estritamente em 3 partes:
            1. **DIAGNÓSTICO CRÍTICO**: Aponte quais setores estão em zona de perigo trabalhista ou batendo lata (baixa eficiência de peso/viagem).
            2. **SUGESTÃO DE REMANEJAMENTO**: Proponha ações exatas de "De -> Para" (ex: 'Transfira X horas do setor A para o setor B para equilibrar o relógio').
            3. **PARECER DA DIRETORIA**: Diga se a frota atual dá conta do recado apenas com equalização ou se o gestor deve ativar o botão de 'Nova Rota de Alívio' devido ao estouro sistêmico.

            Seja direto, técnico, focado em redução de OPEX e use termos corporativos (C-Level).
            """
            
            response = model.generate_content(prompt)
            
            st.markdown("---")
            st.subheader("💡 Relatório Prescritivo da IA")
            st.markdown(response.text)
            
        except Exception as e:
            st.error(f"Erro ao conectar ou processar a API do Gemini: {e}")