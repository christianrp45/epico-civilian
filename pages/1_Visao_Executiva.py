import streamlit as st
import pandas as pd
import os

# 🛡️ AIRBAG DE IMPORTAÇÃO: Impede que a falta do pacote quebre as outras páginas do ÉPICO
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

from helpers import upload_and_filter_page
from kpis import compute_dashboard_data, format_horas_hhmmss, format_number_br

# Força o layout em tela larga (Padrão Quebec/Ecolabs)
st.set_page_config(page_title="ÉPICO - Co-Piloto IA", layout="wide")

st.title("🤖 Co-Piloto Inteligente ÉPICO")
st.caption("Consultoria analítica prescritiva em tempo real alimentada pelo Google Gemini. Transforme dados brutos em decisões C-Level.")

# --- VALIDAÇÃO DO AMBIENTE VIRTUAL ---
if not HAS_GENAI:
    st.error("⚠️ **O módulo 'google-generativeai' não foi encontrado no seu ambiente Python (.venv)!**")
    st.markdown("""
    Para corrigir isso e ativar o Co-Piloto de IA sem erros, feche o sistema e execute o comando abaixo no terminal do seu VS Code:
    ```bash
    .\\.venv\\Scripts\\pip install google-generativeai
    ```
    *Após a barra de instalação verde concluir com sucesso, execute o seu `iniciar_epico.bat` novamente.*
    """)
    st.stop()

# 1. Inicializa os filtros e os dados da cidade ativa (Híbrido)
jornada_meta, df_filtrado = upload_and_filter_page(
    "Análise Prescritiva de IA", 
    "O cérebro de Inteligência Artificial examinando os gargalos invisíveis da sua frota."
)

results = compute_dashboard_data(df_filtrado, jornada_meta=jornada_meta)
rotas = results["rotas"].copy()

if rotas.empty:
    st.warning("⚠️ Nenhum dado operacional disponível com os filtros selecionados.")
    st.stop()

# 2. Configuração e Autenticação da API Key do Gemini via Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("🔑 Autenticação do Ecossistema")
api_key_input = st.sidebar.text_input(
    "Insira sua Gemini API Key:", 
    type="password", 
    value=st.session_state.get("gemini_api_key", ""),
    help="Sua chave fica segura apenas na sessão atual do seu navegador."
)

if api_key_input.strip():
    st.session_state["gemini_api_key"] = api_key_input.strip()
    genai.configure(api_key=api_key_input.strip())
else:
    st.warning("⚠️ Por favor, insira a sua Gemini API Key na barra lateral para ativar os recursos de Inteligência Artificial.")
    st.stop()

# 3. Engenharia de Dados: Sumarização de Alta Performance para o Prompt
cidade_atual = st.session_state.get("global_cidade_ativa", "Trindade")
kpis_globais = results["kpis"]
medias_globais = results["medias"]

# Isola os top setores mais críticos em estouro de relógio e km vazio
top_horas = rotas.sort_values(by="Horas Trabalhadas", ascending=False).head(4)
top_desperdicio = rotas.sort_values(by="Km Improdutivo", ascending=False).head(4)

# Monta o raio-x de dados em texto estruturado para a IA ler sem ruídos
resumo_operacional_ia = f"""
--- BASELINE GLOBAL DA OPERAÇÃO EM {cidade_atual.upper()} ---
- Total de Toneladas Geradas: {kpis_globais['toneladas_total']:.2f} t/dia
- Quilometragem Total Percorrida: {kpis_globais['km_total']:.1f} km/dia
- Consumo Total de Combustível: {kpis_globais['combustivel_total']:.1f} Litros/dia
- Média de Jornada da Frota: {format_horas_hhmmss(medias_globais['media_horas'])} por equipe/dia
- Total de Horas Extras Pagas/Dia: {format_horas_hhmmss(kpis_globais['horas_extras_total'])}
- Percentual de Rodagem Vazia (Km Improdutivo): {kpis_globais['km_improdutivo_pct_total']:.1%}

--- MAIORES ESTOUROS DE JORNADA TRABALHISTA (ZONA DE RISCO) ---
"""
for _, row in top_horas.iterrows():
    resumo_operacional_ia += f"- Setor {row['Setor']}: Jornada de {format_horas_hhmmss(row['Horas Trabalhadas'])}, Peso Coletado: {row['Toneladas']:.2f}t, Viagens: {row['Viagens']:.1f}\n"

resumo_operacional_ia += "\n--- MAIORES DESPERDÍCIOS DE QUILOMETRAGEM (SANGRAMENTO DE OPEX) ---\n"
for _, row in top_desperdicio.iterrows():
    resumo_operacional_ia += f"- Setor {row['Setor']}: Desperdício de {row['Km Improdutivo']:.1f} km vazios, Produtividade Efetiva: {row['Produtividade (t/h)']:.2f} t/h\n"

# 4. Painel de Comando e Disparo da IA
st.markdown("### 📋 Solicitar Auditoria da Inteligência Artificial")
st.info("O cérebro analítico do Gemini vai cruzar a sua volumetria de balança com a rodagem dos caminhões para prescrever a melhor estratégia C-Level.")

if st.button("🚀 Executar Consultoria Logística Avançada", type="primary", use_container_width=True):
    with st.spinner(f"O Gemini está auditando a física operacional de {cidade_atual}... Aguarde."):
        try:
            # Aciona o modelo estável do Gemini Pro
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            prompt_corporativo = f"""
            Você é o Diretor Técnico Interino de Otimização e Logística da Ecolabs. Sua responsabilidade é analisar o relatório de telemetria e balança enviado pela equipe de engenharia e emitir um parecer estratégico para a Quebec Asset e a Diretoria Executiva.

            Dados Reais Extraídos do Sistema para a Cidade de {cidade_atual}:
            {resumo_operacional_ia}

            Regras de Negócio e Premissas da Ecolabs:
            1. A jornada padrão em contrato é de 07:20:00 (7.33h decimais). Qualquer minuto acima é passivo de Hora Extra.
            2. O limite de tolerância de segurança é 09:20:00 (9.33h decimais). Acima disso configura risco grave de fadiga e passivos trabalhistas.
            3. A capacidade limite de escoamento de um caminhão compactador Toco é de 9.5 toneladas por viagem.

            Por favor, redija o seu parecer técnico estruturado rigorosamente nas seguintes seções:
            1. **DIAGNÓSTICO CRÍTICO DA OPERAÇÃO**: Analise o baseline global da cidade. Aponte quais setores estão "sangrando o caixa" com horas extras abusivas ou rodando quilometragem vazia desnecessária (bater lata).
            2. **PLANO DE REMANEJAMENTO CIRÚRGICO**: Olhando os dados dos setores, prescreva ações de "De -> Para" exatas para equilibrar a jornada dos motoristas e coletores usando os simuladores manuais (indique quais setores devem doar tempo/carga e quais devem receber).
            3. **PARECER E DIRETRIZ FINANCEIRA**: Emita a decisão final. A frota atual consegue absorver o volume se for equalizada, ou a diretoria deve aprovar imediatamente o orçamento para o botão de 'Nova Rota de Alívio' por saturação da capacidade física?

            Mantenha um tom altamente profissional, corporativo, focado em retorno sobre o investimento (ROI) e redução de despesas operacionais (OPEX). Não cite variáveis de código, fale como um diretor de operações.
            """
            
            response = model.generate_content(prompt_corporativo)
            
            # Armazena o texto na sessão para que o relatório (Página 6) consiga resgatar
            st.session_state["epico_parecer_ia_salvo"] = response.text
            st.session_state["epico_parecer_ia_cidade"] = cidade_atual
            
            st.markdown("---")
            st.subheader("💡 Parecer Técnico e Diretrizes Prescritivas da IA")
            st.markdown(response.text)
            
            st.success("✅ **Integração Concluída:** O parecer da Inteligência Artificial foi sincronizado com sucesso na memória global do sistema e está disponível para inclusão no Relatório Executivo!")
            
        except Exception as e:
            st.error(f"Falha na comunicação com a API do Gemini: {e}")
            st.info("Verifique se a sua chave de API está ativa e possui créditos de uso.")