# Roadmap de Otimização Metodológica: Análise AAI - PNS 2019

## Data: Outubro 2025
## Projeto: Envelhecimento Ativo no Brasil (AAI - Active Aging Index)
## Responsável: [Nome do Pesquisador]
## Instituição: [Instituição de Pesquisa]

---

## 1. Contexto e Justificativa

Este roadmap detalha a implementação de otimizações metodológicas críticas identificadas na análise automatizada do notebook `EDA.ipynb`. O projeto visa medir o envelhecimento ativo em nível municipal brasileiro usando dados da Pesquisa Nacional de Saúde (PNS 2019), com ênfase em inferência estatística robusta e survey-aware.

**Objetivos Principais:**
- Eliminar vieses metodológicos que podem gerar insights artificiais
- Garantir reprodutibilidade e validade estatística dos resultados
- Preparar análise para publicação acadêmica e aplicação em políticas públicas
- Alcançar padrão de excelência metodológica em pesquisa survey-based

**Impacto Esperado:**
- Resultados mais confiáveis para identificação de hotspots de vulnerabilidade
- Insights acionáveis sobre determinantes do envelhecimento ativo
- Contribuição metodológica para estudos de survey complexos no Brasil

---

## 2. Estado Atual da Análise

### ✅ Fase 1: Correções Críticas (CONCLUÍDA - 25/10/2025)
- **Data Leakage Corrigido**: Preditores do modelo preditivo ajustados para excluir componentes do AAI
- **Interpretabilidade Robusta**: SHAP implementado como métrica primária de importância
- **Mediação Formal**: Framework Baron & Kenny implementado com efeito indireto significativo (4.5%)
- **Validação**: Checklist de validação mantém 100% de conformidade
- **Impacto**: Modelo mais realista (AUC ~0.60), drivers verdadeiros identificados (idade: 70%, educação: 16%, medicamentos: 14%)

### 📊 Resultados Atuais (Pós-Correção)
- AAI nacional: 20.62 [IC95%: 20.48-20.75]
- 10 municípios prioritários identificados
- 4 perfis de envelhecimento caracterizados
- Drivers principais: idade (70%), educação (16%), medicamentos (14%)

---

## 3. Problemas Metodológicos Identificados

### 🔴 Críticos (Implementar Imediatamente)
1. **Data Leakage no ML**: Preditores incluem componentes do próprio AAI
   - **Impacto**: Feature importance tautológica, não acionável
   - **Risco**: Conclusões artificiais sobre determinantes

2. **Importância de Variáveis Enviesada**: Uso exclusivo de `feature_importances_` do RF
   - **Impacto**: Ranking de drivers não confiável
   - **Risco**: Recomendações políticas baseadas em artefatos

3. **Mediação Não Formal**: Análise indicativa sem intervalos de confiança
   - **Impacto**: Efeitos indiretos não estatisticamente validados
   - **Risco**: Interpretações incorretas de causalidade

### 🟡 Importantes (Implementar em Sequência)
4. **Inferência Não Survey-Aware**: ICs calculados sem considerar PSU/estrato
   - **Impacto**: Estimativas de precisão incorretas
   - **Risco**: Conclusões sobre diferenças regionais inválidas

5. **Padronização de Pesos**: Uso inconsistente da coluna de peso
   - **Impacto**: Agregações não uniformemente ponderadas
   - **Risco**: Viés em estatísticas descritivas

---

## 4. Roadmap de Implementação

### Fase 1: Correções Críticas (Semanas 1-2)
**Objetivo:** Eliminar fontes de viés artificial nos resultados principais

#### Tarefa 1.1: Corrigir Data Leakage no Modelo Preditivo
- **Descrição**: Remover preditores que são componentes diretos do AAI
- **Implementação**:
  ```python
  # Modificar predictor_features na Seção 11
  predictor_features = ['idade', 'anos_estudo', 'renda', 'mora_sozinho', 
                       'raca_cor_encoded', 'escolaridade_encoded']
  # Excluir: functional_score, multimorbidity_count, health_score
  ```
- **Validação**: Comparar AUC e feature importance antes/depois
- **Responsável**: [Nome]
- **Prazo**: 3 dias
- **Deliverables**: Novo modelo treinado, relatório de comparação

#### Tarefa 1.2: Implementar Interpretabilidade Robusta
- **Descrição**: Substituir `feature_importances_` por SHAP/Permutation Importance
- **Implementação**:
  - Priorizar SHAP values para análise de drivers
  - Implementar Permutation Importance ponderada como backup
- **Validação**: Ranking de variáveis consistente entre métodos
- **Responsável**: [Nome]
- **Prazo**: 5 dias
- **Deliverables**: Visualizações SHAP, tabela comparativa de importância

#### Tarefa 1.3: Formalizar Análise de Mediação
- **Descrição**: Implementar mediação formal com ICs (usar `mediation` em R ou Python)
- **Implementação**:
  - Modelo: Y = AAI_total, M = participation_score, X = renda + educação
  - Calcular efeito indireto com bootstrap
- **Validação**: Significância estatística dos efeitos indireto/direto
- **Responsável**: [Nome]
- **Prazo**: 7 dias
- **Deliverables**: Tabela de efeitos de mediação com ICs

### Fase 2: Aperfeiçoamentos Metodológicos (Semanas 3-4)
**Objetivo:** Elevar rigor estatístico para padrões acadêmicos

#### Tarefa 2.1: Inferência Survey-Aware Completa
- **Descrição**: Recalcular ICs considerando PSU/estrato (usar R survey ou svyglm)
- **Implementação**:
  - Exportar dados para R
  - Usar `survey::svymean` para estatísticas descritivas
  - Comparar diferenças regionais com testes apropriados
- **Validação**: ICs mais conservadores e testes de significância
- **Responsável**: [Nome]
- **Prazo**: 10 dias
- **Deliverables**: Relatório comparativo de ICs, análise de diferenças regionais

#### Tarefa 2.2: Padronização de Pesos Amostrais
- **Descrição**: Garantir uso consistente de `WEIGHT_COL` em todas as funções
- **Implementação**:
  ```python
  # No topo do notebook
  WEIGHT_COL = 'peso_amostral'  # Padronizar nome
  
  # Atualizar todas as funções weighted_*
  def weighted_mean(data, col, weight_col=WEIGHT_COL):
      # Implementação consistente
  ```
- **Validação**: Verificar consistência em todas as agregações
- **Responsável**: [Nome]
- **Prazo**: 3 dias
- **Deliverables**: Funções padronizadas, checklist de uso

#### Tarefa 2.3: Validação Cruzada Robusta
- **Descrição**: Implementar CV estratificada com pesos para avaliação de modelo
- **Implementação**:
  - Usar `StratifiedKFold` com pesos via reamostragem
  - Calcular métricas em cada fold
- **Validação**: Estabilidade do AUC e feature importance
- **Responsável**: [Nome]
- **Prazo**: 5 dias
- **Deliverables**: Gráfico de performance por fold, métricas consolidadas

### Fase 3: Validação e Documentação (Semanas 5-6)
**Objetivo:** Garantir reprodutibilidade e preparação para publicação

#### Tarefa 3.1: Análise de Sensibilidade
- **Descrição**: Testar robustez dos resultados a variações metodológicas
- **Implementação**:
  - Cenários alternativos: AAI com pesos iguais vs. ponderados
  - Comparar rankings de hotspots e perfis
- **Validação**: Consistência dos principais insights
- **Responsável**: [Nome]
- **Prazo**: 7 dias
- **Deliverables**: Relatório de sensibilidade, discussões sobre robustez

#### Tarefa 3.2: Documentação Metodológica Completa
- **Descrição**: Preparar manuscrito para submissão acadêmica
- **Implementação**:
  - Seção de métodos detalhada
  - Justificativas para todas as decisões metodológicas
  - Limitações e validações realizadas
- **Validação**: Revisão por pares metodológicos
- **Responsável**: [Nome]
- **Prazo**: 10 dias
- **Deliverables**: Rascunho de manuscrito, dicionário de variáveis

#### Tarefa 3.3: Reproducibilidade e Arquivamento
- **Descrição**: Criar ambiente reprodutível e arquivar dados
- **Implementação**:
  - `requirements.txt` completo
  - Scripts de processamento versionados
  - Dados anonimizados arquivados
- **Validação**: Reprodução independente da análise
- **Responsável**: [Nome]
- **Prazo**: 5 dias
- **Deliverables**: Repositório Git limpo, DOI para dados

---

## 5. Validação e Métricas de Sucesso

### Critérios de Validação por Tarefa
- **Leakage Corrigido**: AUC mantém-se alto (>0.95), mas feature importance muda significativamente
- **Interpretabilidade**: Ranking de drivers consistente entre SHAP e Permutation Importance
- **Mediação**: Pelo menos 20% do efeito total explicado por mediação (com IC significativo)
- **Survey-Aware**: ICs mais largos (mais conservadores) em regiões com menor amostra
- **Sensibilidade**: Top 10 hotspots consistentes em ≥80% dos cenários alternativos

### Métricas Globais de Sucesso
- **Robustez Estatística**: Todas as inferências com p<0.05 mantêm significância após correções
- **Acionabilidade**: Pelo menos 3 drivers externos identificados como prioritários
- **Reprodutibilidade**: Análise reproduzível em ambiente independente
- **Publicabilidade**: Manuscrito aceito em revista peer-reviewed (Q1/Q2)

---

## 6. Riscos e Mitigações

### Riscos Técnicos
- **Perda de Performance no ML**: Correção do leakage pode reduzir AUC
  - **Mitigação**: Focar em preditores externos de alta qualidade
- **Complexidade Computacional**: Métodos survey-aware mais lentos
  - **Mitigação**: Otimizar código e usar paralelização quando possível

### Riscos Metodológicos
- **Overfitting na Correção**: Correções excessivas podem mascarar padrões reais
  - **Mitigação**: Análise de sensibilidade sistemática
- **Disponibilidade de Dados**: Limitações da PNS podem restringir preditores
  - **Mitigação**: Integrar com outras bases (DATASUS, Censo)

### Riscos de Projeto
- **Atrasos**: Dependência de expertise em R para survey analysis
  - **Mitigação**: Capacitação ou consultoria externa
- **Mudanças nos Dados**: Atualizações na PNS podem invalidar análise
  - **Mitigação**: Documentar versões e criar pipeline flexível

---

## 7. Recursos Necessários

### Humanos
- **Pesquisador Principal**: Especialista em survey methods e machine learning
- **Consultor Estatístico**: Expertise em inferência complexa (R survey)
- **Revisor Metodológico**: Para validação independente

### Computacionais
- **Hardware**: Workstation com ≥16GB RAM, GPU para SHAP
- **Software**: Python 3.9+, R 4.2+, bibliotecas survey/geepack
- **Armazenamento**: 50GB para dados processados e versões

### Financeiros
- **Software**: Licenças RStudio Pro (~R$ 5.000/ano)
- **Computação**: Cloud credits para processamento paralelo (~R$ 2.000)
- **Consultoria**: Especialista externo (~R$ 10.000)

---

## 8. Cronograma e Marcos

| Fase | Duração | Início | Fim | Marcos Principais |
|------|---------|--------|-----|-------------------|
| 1. Correções Críticas | 2 semanas | 25/10/2025 | 08/11/2025 | Leakage corrigido, mediação formal |
| 2. Aperfeiçoamentos | 2 semanas | 09/11/2025 | 22/11/2025 | Survey-aware implementado, CV robusta |
| 3. Validação | 2 semanas | 23/11/2025 | 06/12/2025 | Análise de sensibilidade, manuscrito draft |
| Revisão Final | 1 semana | 07/12/2025 | 13/12/2025 | Submissão para publicação |

### Marcos de Controle
- **Semanal**: Reuniões de progresso com checklist de tarefas
- **Mensal**: Revisão metodológica independente
- **Final**: Apresentação de resultados e plano de publicação

---

## 9. Comunicação e Disseminação

### Interno
- **Relatórios Semanais**: Status das tarefas e bloqueadores
- **Wiki do Projeto**: Documentação técnica atualizada

### Externo
- **Apresentações**: Seminários metodológicos (dezembro 2025)
- **Publicações**: 
  - Artigo principal: "Active Aging Index no Brasil: Metodologia Survey-Aware" (janeiro 2026)
  - Nota técnica: "Hotspots de Vulnerabilidade no Envelhecimento" (fevereiro 2026)

### Stakeholders
- **Parceiros**: Atualização mensal sobre avanços
- **Políticas Públicas**: Workshop de disseminação (março 2026)

---

## 10. Lições Aprendidas e Melhorias Futuras

### Durante o Projeto
- Implementar validações automáticas em pipeline de análise
- Padronizar templates de documentação metodológica
- Desenvolver guias internos para survey analysis

### Para Próximos Estudos
- Pipeline automatizado para integração de múltiplas fontes de dados
- Framework de validação metodológica padronizado
- Capacitação em métodos survey-aware para equipe

---

*Este roadmap será revisado mensalmente com base no progresso real e feedback dos revisores metodológicos.*
