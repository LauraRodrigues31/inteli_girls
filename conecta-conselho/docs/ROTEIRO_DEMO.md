# Roteiro da Demonstração — Conecta Conselho

**Duração total:** 7–8 minutos | **Formato:** live no Streamlit + nuvem IBM watsonx Orchestrate
**Dados:** 100 % simulados — avisar à banca no início

---

## 1. Abertura (30 s)

**Quem fala:** qualquer integrante

> *"Operadoras de telecomunicações precisam decidir onde expandir a rede — e essa decisão envolve muito mais do que lucro. Uma análise só financeira pode ignorar comunidades que mais precisam de conectividade. O Conecta Conselho reúne cinco perspectivas especializadas — mercado, impacto social, engenharia, orçamento e parcerias — para que **nenhuma decisão seja tomada só pelo lucro**."*

---

## 2. Regiões demonstradas

Três regiões foram escolhidas para contar histórias contrastantes com os números do `RESULTADOS_REGIOES.md`.

---

### Região 1 — Central (realizar_piloto)

**História:** ótima engenharia e orçamento, mas pouco impacto social. O sistema não aprova direto.

| # | O que clicar / fazer | O que aparece na tela | Quem fala | Fala sugerida |
|---|---|---|---|---|
| 1 | Selecionar "central" no dropdown | Abas Mercado / Social / Engenharia / Financeiro / Parcerias carregadas | — | — |
| 2 | Aba **Engenharia** | backbone 8 km, fibra 68 %, viabilidade 88 | **Laura (Engenharia)** | *"A Central tem a melhor infra da base: backbone perto, fibra já distribuída. Engenharia dá 86 de 100."* |
| 3 | Aba **Financeiro** | capex R$ 1,9 M, orçamento R$ 3 M, payback 31 meses, margem positiva | **Gabi (Orçamento)** | *"Orçamento cobre o CAPEX com folga e o payback é de 31 meses — score 76."* |
| 4 | Aba **Social** | vulnerabilidade 24, 29 % sem internet, pessoas beneficiadas 65 mil | **Thaly (Social)** | *"Impacto social é o ponto fraco: vulnerabilidade baixa, poucas pessoas sem acesso. Score social: 30."* |
| 5 | Aba **Parcerias** | 8 instituições âncora, maturidade alta, economia 18 % | **Mi (Pontes)** | *"Central tem boa rede de parceiros — universidade, shopping, prefeitura. Pontes dá 66."* |
| 6 | Clicar **Analisar** | Barras dos 5 agentes surgem | — | — |
| 7 | Ver resultado do Guardião | `realizar_piloto`, consolidado 60 | **Guardião** (qualquer) | *"O Guardião consolida: engenharia e orçamento fortes justificam um piloto, mas o impacto social abaixo de 50 impede investimento imediato. Recomendação: realizar piloto."* |
| 8 | Ver divergências | Nenhuma divergência formal registrada | — | *"Os agentes convergem aqui — não há tensão crítica entre perspectivas."* |

---

### Região 2 — Esperança (aguardar)

**História:** boa demanda de mercado, mas engenharia e orçamento fracos. Duas divergências.

| # | O que clicar / fazer | O que aparece na tela | Quem fala | Fala sugerida |
|---|---|---|---|---|
| 1 | Selecionar "esperanca" | Dados carregados | — | — |
| 2 | Aba **Mercado** | renda R$ 2.900, crescimento 3,2 %, 65 % sem internet, 1 concorrente | **Ana (Mercado)** | *"Boa demanda reprimida: dois terços dos domicílios sem internet e quase sem concorrência. Score mercado: 63."* |
| 3 | Aba **Engenharia** | backbone 62 km, fibra só 8 %, prazo 20 meses, viabilidade 38 | **Laura (Engenharia)** | *"Topografia montanhosa, backbone distante, fibra quase inexistente. Engenharia dá só 34."* |
| 4 | Aba **Financeiro** | capex R$ 8,7 M, orçamento R$ 5 M, déficit R$ 3,7 M, payback 107 meses | **Gabi (Orçamento)** | *"CAPEX quase o dobro do orçamento disponível e payback acima de 9 anos. Score orçamento: 20."* |
| 5 | Aba **Parcerias** | 4 instituições âncora, maturidade baixa, economia 28 % | **Mi (Pontes)** | *"Poucos parceiros e maturidade baixa — Pontes dá 43. Parcerias existem mas não estão consolidadas."* |
| 6 | Clicar **Analisar** | Barras surgem | — | — |
| 7 | Ver resultado do Guardião | `aguardar`, consolidado 44 | **Guardião** | *"Consolidado 44, abaixo de 50. O sistema recomenda aguardar."* |
| 8 | Ver divergências | **D1** social=66 vs. orçamento=20 (diff 46) + **D2** engenharia=34 < 40 com mercado=63 > 60 | **Guardião** | *"Duas divergências: bom impacto social mas viabilidade financeira fraca; e boa demanda de mercado mas engenharia inviável. O sistema não decide — precisa de mais análise de campo."* |

---

### Região 3 — Nova União (escalar) *(depende da regra em aprovação)*

**História:** impacto social altíssimo, mas financeiramente inviável. Escala para um humano.

| # | O que clicar / fazer | O que aparece na tela | Quem fala | Fala sugerida |
|---|---|---|---|---|
| 1 | Selecionar "nova_uniao" | Dados carregados | — | — |
| 2 | Aba **Social** | vulnerabilidade 86, 82 % sem internet, 78 % baixa renda, score 78 | **Thaly (Social)** | *"Nova União tem o maior impacto social da base: quase toda a população sem internet e altíssima vulnerabilidade."* |
| 3 | Aba **Financeiro** | capex R$ 12,5 M, orçamento R$ 3,5 M, receita < opex, payback nulo | **Gabi (Orçamento)** | *"A operação é deficitária: receita mensal não cobre nem o custo operacional. Score orçamento: 0."* |
| 4 | Aba **Engenharia** | backbone 98 km, fibra 0 %, prazo 28 meses, viabilidade 18 | **Laura (Engenharia)** | *"Sem fibra alguma, backbone a 98 km. Seria construir do zero. Score engenharia: 11."* |
| 5 | Aba **Parcerias** | 3 instituições âncora, maturidade baixa, sem infra compartilhável | **Mi (Pontes)** | *"Apenas 3 possíveis parceiros e sem infraestrutura compartilhável. Pontes dá 21 — o menor da base."* |
| 6 | Clicar **Analisar** | Barras surgem | — | — |
| 7 | Ver resultado do Guardião | `escalar` *(com regra extra)* ou `aguardar` *(sem ela)*, consolidado 30 | **Guardião** | *"Consolidado 30, orçamento 0 e engenharia 11 — ambos abaixo de 20. Pela regra em discussão no grupo, isso escala para análise humana: o caso é real, mas exige programa de universalização, não investimento privado direto."* |
| 8 | Ver divergências | **D1** social=78, orçamento=0, diff=78 | — | *"A maior divergência da base: o maior impacto social junto com a pior viabilidade financeira."* |

> **⚠️ Lembrete para a apresentação:** deixar claro que a recomendação `escalar` depende da aprovação da regra extra pelo grupo antes do dia da banca. Se não aprovada, o Guardião mostra `aguardar` — o comentário narrativo permanece o mesmo.

---

## 3. Fechamento (30 s)

**Quem fala:** qualquer integrante

1. Mostrar a **trilha de auditoria** (painel de rastreabilidade no Streamlit): cada decisão expõe os indicadores usados, as fontes e as limitações.
2. Clicar em **Exportar JSON**: fazer download do relatório da última região analisada.
3. Encerrar com limitações:

> *"O sistema apoia a triagem — não autoriza obras, não calcula CAPEX real, não substitui análise de campo. Os dados são simulados. O que entregamos é a lógica: cinco perspectivas, pesos transparentes, divergências explícitas e escalonamento humano quando o sistema não tem segurança."*

---

## 4. Checklist pré-demo

### Na véspera
- [ ] `develop` atualizada: `git pull origin develop`
- [ ] `python -m pytest -q` passando sem falhas
- [ ] `streamlit run conecta-conselho/app.py` abre sem erro
- [ ] Prints de backup das 3 regiões (central, esperanca, nova_uniao) tirados e salvos
- [ ] Ensaio cronometrado: deve caber em 7–8 min

### 15 minutos antes
- [ ] **Laura** roda `orchestrate env activate conecta-conselho --api-key "$WXO_API_KEY"` (o token expira em 2 h — ativar no máximo 1 h antes)
- [ ] Testar as 3 regiões na nuvem: central → realizar_piloto, esperanca → aguardar, nova_uniao → escalar/aguardar
- [ ] Confirmar conexão à internet estável
- [ ] Abas abertas: Streamlit, repo GitHub, este roteiro

> **Lembrete:** a instância Trial (jp-tok) expira por volta de **01/12/2026** (30 dias a partir da criação).
> Confirmar a data exata em: IBM Cloud → Resource list → instância watsonx Orchestrate → aba Plan.

---

## 5. Plano B

| Falha | Ação |
|---|---|
| Nuvem IBM Cloud fora do ar ou lenta | Rodar Streamlit em modo local: `CC_MODO=local streamlit run conecta-conselho/app.py` (usa os mesmos cálculos determinísticos, sem chamadas à nuvem) |
| Streamlit com erro de import | Usar os **prints de backup** das 3 regiões e as tabelas de `RESULTADOS_REGIOES.md` para narrar os resultados manualmente |
| Token expirado durante a demo | Laura reativa: `orchestrate env activate conecta-conselho --api-key "$WXO_API_KEY"` (30 s) |
| Score diferente do gabarito | Citar: *"Os scores são determinísticos — qualquer diferença é de versão do código. O gabarito está em RESULTADOS_REGIOES.md, gerado com o commit 4cd4e92"* |

---

## 6. Perguntas prováveis da banca

*(Respostas baseadas em CONTEXTO_PROJETO Seções 4 e 6)*

**P: Por que o LLM não calcula o score?**
> O score é calculado por funções Python determinísticas com fórmulas documentadas. Se o LLM calculasse, os resultados variariam entre execuções, não seriam auditáveis e poderiam contradizer os dados. O LLM só escreve a justificativa em português — o número vem do código.

**P: Como é calculada a confiança?**
> A confiança não é subjetiva: é determinada pela completude dos dados. Todos os campos obrigatórios presentes → `alta`. Menos de 6 campos ou campo crítico ausente → `baixa`. A regra está documentada na Seção 3.3 do PADRÃO e é a mesma para todos os agentes.

**P: Os dados são reais?**
> Não. Todos os dados são 100 % simulados e fictícios, criados exclusivamente para fins de demonstração. O aviso aparece em todas as telas do Streamlit e no topo de cada relatório JSON. Não há nenhum dado real de municípios brasileiros.

**P: E se os agentes discordarem?**
> O Guardião identifica e registra divergências explicitamente (campo `divergencias`). Quando a tensão é alta — por exemplo, impacto social muito alto mas orçamento zero — o Guardião a destaca na justificativa e, se a confiança for baixa ou o consolidado muito baixo, escala para análise humana. O desacordo é recurso, não bug.

**P: Quando o sistema chama um humano?**
> Quando o score consolidado indica `escalar` (abaixo de 30 pela regra em aprovação, ou abaixo de 30 pelas regras atuais), quando qualquer agente retorna erro ou confiança baixa, ou quando há divergências que nenhum peso consegue resolver. A decisão final sempre é humana — o sistema só apoia a triagem.

**P: Por que o Agente de Pontes não "garante" a demanda?**
> O Agente de Pontes identifica **possíveis** instituições âncora e modela cenários **hipotéticos** de articulação. Nenhum contrato real existe. A linguagem é sempre condicional: *"se a prefeitura se tornar âncora"*, não *"a prefeitura vai assinar"*. Isso está na Seção 6 do CONTEXTO e é regra obrigatória do PADRÃO (Seção 10).

**P: Isso substitui o analista?**
> Não. O sistema **apoia** a triagem de oportunidades. Não autoriza obras, não calcula CAPEX executivo, não faz geoprocessamento real, não negocia contratos. O usuário-alvo é um analista de planejamento que usa o sistema como primeira camada de análise antes de acionar campo e engenharia detalhada.

**P: Por que esses pesos?**
> Os pesos (engenharia 25 %, orçamento 25 %, mercado 20 %, social 20 %, pontes 10 %) refletem a premissa de que limitações técnicas ou financeiras são bloqueantes — por isso peso maior. Os demais são habilitadores. Estão explicitamente documentados como *"hipótese de MVP para fins de demonstração"* — não representam metodologia real de investimento.

---

*Documento gerado em: 2026-11-03 | Branch: `docs/roteiro-demo` | Commit base: `4cd4e92`*
*Scores de referência: `RESULTADOS_REGIOES.md` | Sistema: Conecta Conselho — MVP*
