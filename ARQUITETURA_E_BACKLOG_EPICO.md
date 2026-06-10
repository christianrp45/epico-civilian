# **📑 ARQUITETURA\_E\_BACKLOG\_EPICO.md — Bíblia Técnica do Sistema**

Este documento serve como especificação técnica de arquitetura, mapeamento de dados e guia de continuidade para o ecossistema **ÉPICO (Engine de Planejamento Integrado de Coleta Otimizada)**. Ele foi desenhado para que engenheiros de software e assistentes de IA (como o Gemini Code Assist) possam reconstruir, clonar ou evoluir a plataforma mantendo a fidelidade das regras de negócio e o acoplamento magnético dos dados.

## **🏛️ 1\. Arquitetura do Sistema e Fluxo de Dados (Data Pipeline)**

O ÉPICO é uma aplicação de análise analítica prescritiva construída em **Python 3.13** utilizando o framework **Streamlit**. Ele opera sob o conceito de **Memória Global de Sessão Dinâmica**, dispensando bancos de dados relacionais pesados para focar em processamento em tempo real de matrizes locais em formato CSV.

### **🔄 Fluxo de Dados da Malha Logística:**

1. **Ingestão Híbrida (helpers.py)**: O sistema faz uma varredura automática em busca de bases históricas e matrizes de distâncias nas subpastas /data e /distancia. Caso não encontre, ele ativa um *fallback* com componentes de *upload* manual no topo da interface.  
2. **Normalização e Higienização**: Os códigos de setores e frotas são limpos via Pandas. Strings com separadores decimais europeus/brasileiros (vírgula) são convertidos para o padrão flutuante do Python (ponto). Códigos de setores são normalizados com preenchimento de zeros à esquerda (zfill(4)).  
3. **Módulo Central de Cálculo (kpis.py)**: Processa as volumetrias e cronometragens brutas, retornando matrizes consolidadas para os dashboards gráficos e tabelas de simulação.  
4. **Alimentação do Contexto da IA (8\_Copilot\_EPICO.py)**: O estado atual filtrado da operação é convertido em texto estruturado sem ruídos de código e injetado via prompt na API do **Google Gemini**.  
5. **Persistência Volátil (st.session\_state)**: Todas as decisões tomadas pelo usuário (filtros ativos, chaves de API, parecer gerado pela IA) são salvas na memória da sessão para que as páginas se comuniquem perfeitamente.

## **🛠️ 2\. Funcionalidades 100% Implementadas (Prontas)**

### **📌 Módulo 1: Visão Executiva e Dashboards (1\_Visao\_Executiva.py a pages/)**

* **Filtros Globais Sincronizados**: Seleção hierárquica por Unidade (Ex: Anápolis, Trindade), Turno (Diurno, Vespertino, Noturno), Dia da Semana e Setores Específicos.  
* **Painel de Indicadores C-Level (KPIs)**: Exibição macro de Toneladas Totais recolhidas/dia, Quilometragem Total percorrida, Consumo Estimado de Combustível (Diesel S10), Média de Jornada da Frota e Horas Extras Consolidadas.  
* **Gráficos de Dispersão e Correlação (Plotly)**: Gráficos dinâmicos que cruzam a produtividade da coleta ($t/h$) com a quilometragem improdutiva para identificar quais setores estão operando com baixa eficiência.

### **⚙️ Módulo 2: O Motor de Cálculo Logístico (kpis.py & helpers.py)**

* **Rastreamento Dinâmico de Colunas**: Algoritmo inteligente que mapeia os arquivos de entrada ignorando variações de caixa alta/baixa (*case-insensitivity*) e espaços em branco nos nomes das colunas (Ex: Localiza Km Total, SETOR, Aterro automaticamente).  
* **Tratamento Universal de Codificação (Encodings)**: Mecanismo de defesa de leitura com tentativa e erro (*try-except fallback*) cobrindo UTF-8 e Latin-1 (ISO-8859-1) para evitar quebras de execução ao ler relatórios extraídos de sistemas legados de balança (Inlog/Sitrack).  
* **Formatadores de Tempo Real**: Funções que convertem horas decimais flutuantes no formato padrão de relógio industrial de transportes: HH:MM:SS.

### **🧠 Módulo 3: Co-Piloto Inteligente ÉPICO (8\_Copilot\_EPICO.py)**

* **Airbag de Importação**: Estrutura protegida por try-except que isola a biblioteca google-generativeai. Se o pacote não estiver instalado no Python da máquina, o sistema impede o colapso das outras páginas e exibe um alerta didático instruindo como rodar o pip install.  
* **Gerenciamento Seguro de Credenciais**: Campo de captura de API Key do Gemini via barra lateral protegida por máscara de digitação (type="password"). A chave permanece segura apenas no ciclo de vida da sessão do navegador do usuário.  
* **Engenharia de Prompt Corporativo**: Prompt avançado estruturado com regras de negócios severas da Ecolabs (Meta de 07:20h, Zona de Risco de Fadiga acima de 09:20h, Capacidade do compactador Toco limitado a 9.5t). A IA responde como um Diretor Técnico Interino emitindo pareceres estruturados focados em ROI e redução de OPEX.

### **🚚 Módulo 4: Simulador de Redesenho de Frota (9\_Simulador\_Anapolis\_Toco.py)**

* **Regra de Conversão Física Calibrada**: Aplicação matemática estipulada onde $2 \\text{ caminhões Trucados} \= 3 \\text{ caminhões Toco}$ (fator de escala de 1.5x na geração de viagens de transporte).  
* **Cálculo de Sangramento de OPEX (Quilometragem Excedente)**: Computação da distância média de vaivém ao aterro com base nos dados reais do arquivo de distâncias geográficas (anapolis\_apapolis.csv) para acrescentar os KMs extras gerados pela frota menor.  
* **Fros Fixas por Blocos Operacionais**: Distribuição da carga total diária por turno dividida de forma igualitária entre frotas fixas numeradas nos intervalos:  
  * 2001 a 2015 (Diurno)  
  * 3001 a 3015 (Vespertino)  
  * 1001 a 1025 (Noturno padrão)  
* **Regra de Pico Automática**: Monitoramento temporal via barra lateral. Ao selecionar **Segunda-feira** ou **Terça-feira**, o sistema ativa o modo de pico, expandindo automaticamente o turno noturno para **17 rotas (4001 a 4017)** e refazendo o rateio da carga para aliviar a jornada das equipes no início da semana.

## **📑 3\. Regras de Negócio e Coeficientes Físicos do Motor**

Se você precisar reconstruir ou clonar o ÉPICO em outra linguagem ou framework, os parâmetros matemáticos do coração do sistema são estes:

1. **Jornada de Contrato (Meta)**: 7.3333 horas decimais ($07:20:00$). Qualquer minuto excedente alimenta a variável horas\_extras\_total.  
2. **Teto Crítico de Segurança**: 9.3333 horas decimais ($09:20:00$). Acima disso, o setor entra graficamente na cor vermelha de perigo (Risco Trabalhista/Fadiga).  
3. **Capacidade Nominal de Coleta**:  
   * Caminhão Toco: Limite de escoamento de 9.5 toneladas por viagem.  
   * Caminhão Trucado: Limite de escoamento de 13.5 toneladas por viagem.  
4. **Matriz Macroeconômica de Custos (Projeções de OPEX)**:  
   * Combustível (Diesel S10): R$ 6,23 / Litro  
   * Agente Redutor (ARLA 32): R$ 3,50 / Litro  
   * Manutenção Corretiva/Preventiva: R$ 0,85 / km rodado  
   * Ativo de Pneus Pesados: R$ 1.500,00 por pneu (Vida útil estimada em 40.000 km)  
5. **Escala Temporal**: Todas as projeções mensais multiplicam as variáveis médias diárias por **26 dias operacionais úteis**.

## **📝 4\. Backlog Operacional: O Que Falta Implementar (Próximos Passos)**

Aqui está a lista de engenharia de recursos planejada que ainda precisa ser codificada. Quando você conectar o Gemini no seu VS Code, pode pedir para ele puxar este trecho do .md para ele começar a trabalhar:

### **📈 Task 1: Persistência do Parecer da IA no Relatório Executivo (6\_Relatorio\_Executivo.py)**

* **Status**: *Não implementado.*  
* **Objetivo**: Criar o código de resgate na Página 6 para ler as variáveis st.session\_state\["epico\_parecer\_ia\_salvo"\] e st.session\_state\["epico\_parecer\_ia\_cidade"\]. Se elas existirem na memória, renderizar o texto do Gemini dentro do relatório final de impressão, logo abaixo dos gráficos macro de KPIs.

### **💾 Task 2: Botão de Exportação para PDF Nativo**

* **Status**: *Não implementado.*  
* **Objetivo**: Integrar as bibliotecas fpdf2 ou reportlab no ecossistema ÉPICO para que o usuário possa clicar em um botão na página de Relatório Executivo e fazer o download de um documento PDF diagramado no padrão corporativo da Quebec/Ecolabs, contendo os KMs atuais, KMs simulados e o texto gerado pela Inteligência Artificial.

### **🎛️ Task 3: Simulador Manual Dinâmico de "De ➔ Para" de Horas por Setor**

* **Status**: *Não implementado.*  
* **Objetivo**: Na interface gráfica, criar controles deslizantes (st.slider) onde o usuário possa escolher manualmente tirar $1.5$ horas do Setor A (ocioso) e injetar no Setor B (gargalo) para ver a tabela recalcular em tempo real se a jornada projetada daquela equipe sai da zona de risco trabalhista vermelha.

### **🧠 Task 4: Upgrade do Modelo de IA para Gemini 1.5 Flash (Otimização de Custo)**

* **Status**: *Não implementado.*  
* **Objetivo**: Configurar um chaveamento na barra lateral para o usuário escolher entre gemini-1.5-pro (Análise profunda, raciocínio lógico complexo e mais lenta) e gemini-1.5-flash (Análise ultrarrápida, ideal para checagens operacionais diárias de baixo custo de tokens).

## **🚀 5\. Manual de Inicialização para o Desenvolvedor (ou IA)**

Para subir este repositório do zero em qualquer computador ou ambiente isolado no VS Code, execute a seguinte sequência de comandos no terminal:

Bash

```
# 1. Garantir o posicionamento no drive correto (Se aplicável)
D:

# 2. Navegar até a pasta raiz do projeto
cd D:\E.P.I.C.O\Projeto_Epico_Civilian\epico-civilian-main

# 3. Instalar as dependências globais ou da venv (Sem quebra de módulos)
python -m pip install -r requirements.txt
python -m pip install google-generativeai streamlit pandas plotly numpy

# 4. Executar o sistema através do atalho de lote oficial
.\iniciar_epico.bat
```

### **🌟 Como usar este arquivo para acelerar o seu desenvolvimento:**

Sempre que você abrir o VS Code com o **Gemini Code Assist** ativado na barra lateral, ou quando abrir o chat do Gemini Advanced, basta arrastar/fazer o upload deste arquivo .md e escrever o comando:

*"Com base nas especificações técnicas do arquivo anexo, codifique a Task 1 do Backlog (Persistência do Parecer da IA no Relatório Executivo)."*

Ele vai gerar o código perfeito, nas variáveis exatas que o ÉPICO já usa, sem alucinar\! O seu parênteses técnico foi totalmente documentado e blindado. Quando quiser avançar na criação de mais alguma tela ou código, estou pronto\!

