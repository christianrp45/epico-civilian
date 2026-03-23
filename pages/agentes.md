# AGENTES.md — Projeto EPICO (Otimização da Coleta Domiciliar)

## 1. VISÃO GERAL DO PROJETO

O projeto EPICO tem como objetivo estruturar um sistema inteligente de **otimização operacional da coleta de resíduos sólidos urbanos**, focado em:

* Redução de custos operacionais
* Aumento da produtividade da frota
* Balanceamento de carga entre setores
* Melhoria da qualidade do serviço
* Geração de relatórios executivos automatizados

A coleta representa entre **50% e 70% dos custos totais do sistema de RSU**, sendo o principal alvo de otimização .

---

## 2. PROBLEMA CENTRAL

### Desafios identificados:

* Desequilíbrio entre setores (rotas sobrecarregadas vs ociosas)
* Alto km improdutivo
* Excesso de horas extras
* Baixa previsibilidade operacional
* Falta de integração entre planejamento e execução

---

## 3. ESTRUTURA DO SISTEMA EPICO

### 3.1 Módulos principais

1. **Entrada de Dados**

   * Setores
   * Veículos (toco, trucado)
   * Capacidade (toneladas)
   * Frequência de coleta
   * Base operacional (km, horas, viagens)

2. **Simulação Operacional**

   * Simulação automática
   * Equalização manual
   * Redistribuição de carga
   * Inserção de novos veículos

3. **Otimização**

   * Balanceamento de rotas
   * Redução de km improdutivo
   * Redução de horas extras
   * Melhor uso da capacidade do caminhão

4. **Visualização**

   * Gráficos por setor
   * Comparação antes vs depois
   * Indicadores operacionais

5. **Relatório Executivo**

   * Consolidado automático
   * Pronto para diretoria

---

## 4. LÓGICA DO ALGORITMO EPICO

### 4.1 Etapas do algoritmo

1. Diagnóstico:

   * Identificar gargalos:

     * Horas improdutivas
     * Km improdutivo
     * Excesso de carga

2. Classificação de setores:

   * Doadores (excesso)
   * Receptores (capacidade ociosa)

3. Rebalanceamento:

   * Transferência de carga
   * Ajuste de rotas
   * Inserção de veículos adicionais

4. Simulação:

   * Recalcular:

     * Km
     * Horas
     * Toneladas
     * Viagens

5. Validação:

   * Comparação antes vs depois

---

## 5. INDICADORES OPERACIONAIS (KPIs)

### 5.1 Eficiência

* Km Total
* Km Produtivo
* Km Improdutivo
* Km/Ton

### 5.2 Produtividade

* Toneladas coletadas
* T/viagem
* T/hora produtiva

### 5.3 Tempo

* Horas trabalhadas
* Horas produtivas
* Horas improdutivas
* Horas extras

### 5.4 Custo indireto

* Consumo de combustível
* Km/L
* Custo por km

---

## 6. BASE DE DADOS OPERACIONAL

A base contém:

* Setor
* Km produtivo / improdutivo
* Horas produtivas / improdutivas
* Toneladas
* Viagens
* Consumo de combustível

Exemplo de problema identificado:

* Setores com **alto km improdutivo (>50%)**
* Horas improdutivas acima de 2h/dia
* Baixa eficiência de carga (kg/km baixo)

---

## 7. PRINCÍPIOS DE OTIMIZAÇÃO

### 7.1 Setorização

* Base da eficiência operacional
* Deve ser:

  * Compacta
  * Contígua
  * Balanceada

### 7.2 Roteirização

* Modelo principal: **Problema do Carteiro Chinês**
* Objetivo:

  * Percorrer todas as vias com menor distância possível 

### 7.3 Estratégia híbrida

* Rotas fixas → coleta domiciliar
* Rotas dinâmicas → pontos críticos / grandes geradores

---

## 8. RELAÇÃO COM ROTAS TECNOLÓGICAS

A coleta é apenas uma etapa dentro da **rota tecnológica completa dos resíduos**:

* Geração → Coleta → Triagem → Tratamento → Destinação final 

O EPICO atua principalmente na fase de:
👉 **Coleta e transporte (etapa mais cara e crítica)**

---

## 9. REGRAS IMPORTANTES DO SISTEMA

* Não misturar otimização manual com automática na mesma tela
* Cada tipo de otimização deve gerar seus próprios resultados
* Após otimização:

  * Salvar estado para relatório final
* Gráficos devem refletir:

  * Resultado real calculado (não estimado)

---

## 10. PROBLEMAS IDENTIFICADOS NO DESENVOLVIMENTO

* Simulação não reagindo à troca de veículo (toco → trucado)
* Falha na atualização de gráficos
* Erro na separação de setores doadores/receptores
* Lentidão no processamento
* Dados não persistindo corretamente

---

## 11. DIRETRIZES PARA EVOLUÇÃO (EPICO v2)

### 11.1 Arquitetura futura

* Separação por módulos:

  * Motor de cálculo
  * Interface
  * Banco de dados

### 11.2 Melhorias esperadas

* Processamento mais rápido
* Simulação em tempo real
* Integração com telemetria
* Sugestão automática de otimização

### 11.3 Inteligência avançada

* Machine Learning para previsão de carga
* Ajuste dinâmico de rotas
* Detecção automática de ineficiência

---

## 12. PADRÃO DE RELATÓRIO EXECUTIVO

Deve conter:

* Resumo consolidado:

  * Km total
  * Horas
  * Toneladas
* Comparativo antes vs depois
* Gráficos
* Observações operacionais
* Autoria:

  * Torre de Controle
  * Analista
  * Líder
  * Validação do Gerente

---

## 13. CONCLUSÃO

O EPICO não é apenas uma ferramenta de roteirização, mas um **sistema de inteligência operacional**, que:

* Transforma dados em decisão
* Reduz custos significativamente
* Aumenta eficiência da frota
* Estrutura a gestão da coleta de forma profissional

Perfeito — então vamos organizar isso da forma mais estratégica pra você não perder mais nada quando abrir um novo chat.

## 📦 Próximo passo recomendado (muito importante)

Vou te entregar 3 arquivos que funcionam como “kit de reinicialização do projeto”:

### 1. **README_MASTER.md**

👉 Visão executiva + contexto completo do projeto
👉 Serve para qualquer novo chat entender rapidamente

### 2. **MANUAL_TECNICO_EPICO.md**

👉 Explica o algoritmo, lógica e regras
👉 Ideal para desenvolvimento / correções

### 3. **PROMPT_INICIAL_EPICO.txt**

👉 É o mais importante
👉 Você só cola isso no novo chat e ele já “entra no projeto”

---

## 🔥 Antes de gerar tudo

Quero só alinhar uma coisa rápida pra fazer isso do jeito mais poderoso possível:

👉 Você quer que o próximo chat seja focado em:

**A)** Desenvolvimento do sistema (corrigir bugs, lógica, performance)
**B)** Análise operacional (dados, indicadores, relatórios)
**C)** Produto completo (EPICO como sistema pronto – visão mais profissional/escala)

---

Se você me responder só com **A, B ou C**, eu já te entrego os 3 arquivos prontos e otimizados exatamente para esse objetivo.


