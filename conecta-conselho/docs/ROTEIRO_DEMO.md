# Roteiro da Demonstração — Conecta Conselho

**Duração total:** 7–8 minutos | **Formato:** live no site (front React) + nuvem IBM watsonx Orchestrate
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
| 6 | Clicar **▶ Executar Conselho** | Cards dos 5 agentes surgem com scores e confiança | — | — |
| 7 | Ver resultado do Guardião | `🔬 Realizar Piloto`, consolidado 60 | **Guardião** (qualquer) | *"O Guardião consolida: engenharia e orçamento fortes justificam um piloto, mas o impacto social abaixo de 50 impede investimento imediato. Recomendação: realizar piloto."* |
| 8 | Expandir **⚡ Divergências identificadas (1)** | D1 — orçamento 76 alto x impacto social 30 baixo (\|76−30\|=46 > 30) | — | *"O sistema identificou uma divergência: orçamento forte mas impacto social fraco. É exatamente por isso que não aprova direto — o lucro sozinho não justifica o investimento sem retorno social. Por isso piloto, e não investir agora."* |

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
| 6 | Clicar **▶ Executar Conselho** | Cards dos 5 agentes surgem | — | — |
| 7 | Ver resultado do Guardião | `aguardar`, consolidado 44 | **Guardião** | *"Consolidado 44, abaixo de 50. O sistema recomenda aguardar."* |
| 8 | Ver divergências | **D1** social=66 vs. orçamento=20 (diff 46) + **D2** engenharia=34 < 40 com mercado=63 > 60 | **Guardião** | *"Duas divergências: bom impacto social mas viabilidade financeira fraca; e boa demanda de mercado mas engenharia inviável. O sistema não decide — precisa de mais análise de campo."* |

---

### Região 3 — Nova União (escalar)

**História:** impacto social altíssimo, mas financeiramente inviável. Escala para um humano.

| # | O que clicar / fazer | O que aparece na tela | Quem fala | Fala sugerida |
|---|---|---|---|---|
| 1 | Selecionar "nova_uniao" | Dados carregados | — | — |
| 2 | Aba **Social** | vulnerabilidade 86, 82 % sem internet, 78 % baixa renda, score 78 | **Thaly (Social)** | *"Nova União tem o maior impacto social da base: quase toda a população sem internet e altíssima vulnerabilidade."* |
| 3 | Aba **Financeiro** | capex R$ 12,5 M, orçamento R$ 3,5 M, receita < opex, payback nulo | **Gabi (Orçamento)** | *"A operação é deficitária: receita mensal não cobre nem o custo operacional. Score orçamento: 0 — confiança **baixa** porque a margem é negativa."* |
| 4 | Aba **Engenharia** | backbone 98 km, fibra 0 %, prazo 28 meses, viabilidade 18 | **Laura (Engenharia)** | *"Sem fibra alguma, backbone a 98 km. Seria construir do zero. Score engenharia: 11."* |
| 5 | Aba **Parcerias** | 3 instituições âncora, maturidade baixa, sem infra compartilhável | **Mi (Pontes)** | *"Apenas 3 possíveis parceiros e sem infraestrutura compartilhável. Pontes dá 21 — o menor da base."* |
| 6 | Clicar **▶ Executar Conselho** | Cards dos 5 agentes surgem | — | — |
| 7 | Ver resultado do Guardião | `👤 Escalar a Humano`, consolidado 30 | **Guardião** | *"Consolidado 30, orçamento 0 e engenharia 11 — ambos abaixo de 20 — e confiança do Orçamento é baixa. A regra adotada pelo grupo força escalonamento: esse caso exige programa de universalização, não investimento privado direto."* |
| 8 | Expandir **⚡ Divergências identificadas (1)** | **D1** social=78, orçamento=0, \|diff\|=78 | — | *"A maior divergência da base: o maior impacto social junto com a pior viabilidade financeira. O sistema não decide — escala para análise humana."* |

---

## 3. Fechamento (30 s)

**Quem fala:** qualquer integrante

1. Mostrar as **divergências e limitações** do Guardião (expanders na tela de resultado): cada decisão expõe os indicadores usados, os riscos e as limitações.
2. Clicar em **⬇️ Baixar relatório JSON (trilha de auditoria)**: fazer download do relatório da última região analisada.
3. Encerrar com limitações:

> *"O sistema apoia a triagem — não autoriza obras, não calcula CAPEX real, não substitui análise de campo. Os dados são simulados. O que entregamos é a lógica: cinco perspectivas, pesos transparentes, divergências explícitas e escalonamento humano quando o sistema não tem segurança."*

---

## 4. Checklist pré-demo

### Na véspera
- [ ] `develop` atualizada: `git pull origin develop`
- [ ] `python -m pytest -q` passando sem falhas
- [ ] Backend (`uvicorn api.main:app --port 8000`) e front (`cd frontend; npm run dev`) sobem sem erro e http://localhost:5173 abre
- [ ] Prints de backup das 3 regiões (central, esperanca, nova_uniao) tirados e salvos
- [ ] Ensaio cronometrado: deve caber em 7–8 min

### 15 minutos antes
- [ ] **Laura** roda `orchestrate env activate conecta-conselho` (o token expira em 2 h — ativar no máximo 1 h antes)
- [ ] Testar as 3 regiões na nuvem: central → realizar_piloto, esperanca → aguardar, nova_uniao → escalar
- [ ] Confirmar conexão à internet estável
- [ ] Abas abertas: site (localhost:5173), repo GitHub, este roteiro

> **Lembrete:** a instância Trial (jp-tok) expira por volta de **01/12/2026** (30 dias a partir da criação).
> Confirmar a data exata em: IBM Cloud → Resource list → instância watsonx Orchestrate → aba Plan.

---

## 5. Plano B

| Falha | Ação |
|---|---|
| Nuvem IBM Cloud fora do ar ou lenta | Na tela *Análise de Região*, escolher a fonte **Local (determinístico)** (usa os mesmos cálculos, sem chamadas à nuvem) |
| Site ou backend com erro ao subir | Usar os **prints de backup** das 3 regiões e as tabelas de `RESULTADOS_REGIOES.md` para narrar os resultados manualmente |
| Token expirado durante a demo | Laura reativa: `orchestrate env activate conecta-conselho` (30 s) |
| Score diferente do gabarito | Citar: *"Os scores são determinísticos — qualquer diferença é de versão do código. O gabarito está em RESULTADOS_REGIOES.md, gerado com o commit 1010f96"* |

---

## 6. Perguntas prováveis da banca

*(Respostas baseadas em CONTEXTO_PROJETO Seções 4 e 6)*

**P: Por que o LLM não calcula o score?**
> O score é calculado por funções Python determinísticas com fórmulas documentadas. Se o LLM calculasse, os resultados variariam entre execuções, não seriam auditáveis e poderiam contradizer os dados. O LLM só escreve a justificativa em português — o número vem do código.

**P: Como é calculada a confiança?**
> A confiança não é opinião do LLM: cada agente a calcula por regra no código. Na maioria dos agentes ela depende da completude dos dados — campos faltando reduzem a confiança. O Agente de Orçamento também reduz a confiança para `baixa` quando a operação é financeiramente inviável (receita menor que o custo operacional), como na Nova União. Não é uma probabilidade estatística. Confiança baixa em qualquer agente leva o Guardião a escalar para um humano.

**P: Os dados são reais?**
> Não. Todos os dados são 100 % simulados e fictícios, criados exclusivamente para fins de demonstração. O aviso aparece em todas as telas do site e no topo de cada relatório JSON. Não há nenhum dado real de municípios brasileiros.

**P: E se os agentes discordarem?**
> O Guardião identifica e registra divergências explicitamente (campo `divergencias`). Quando a tensão é alta — por exemplo, impacto social muito alto mas orçamento zero — o Guardião a destaca na justificativa e, se a confiança for baixa ou o consolidado muito baixo, escala para análise humana. O desacordo é recurso, não bug.

**P: Quando o sistema chama um humano?**
> Quando a regra adotada pelo grupo dispara `escalar`: consolidado < 30, OU engenharia < 20, OU orçamento < 20, OU qualquer agente retorna confiança `baixa` ou erro. A decisão final sempre é humana — o sistema só apoia a triagem.

**P: Por que nenhuma região recebe `investir_agora`?**
> O critério exige consolidado ≥ 70 **E** orçamento ≥ 60 **E** engenharia ≥ 60 simultaneamente. Com engenharia e orçamento pesando 50 % do consolidado, o sistema é deliberadamente conservador — nenhuma região da base atual justifica investimento imediato sem um piloto que valide campo e custos reais.

**P: Por que o Agente de Pontes não "garante" a demanda?**
> O Agente de Pontes identifica **possíveis** instituições âncora e modela cenários **hipotéticos** de articulação. Nenhum contrato real existe. A linguagem é sempre condicional: *"se a prefeitura se tornar âncora"*, não *"a prefeitura vai assinar"*. Isso está na Seção 6 do CONTEXTO e é regra obrigatória do PADRÃO (Seção 10).

**P: Isso substitui o analista?**
> Não. O sistema **apoia** a triagem de oportunidades. Não autoriza obras, não calcula CAPEX executivo, não faz geoprocessamento real, não negocia contratos. O usuário-alvo é um analista de planejamento que usa o sistema como primeira camada de análise antes de acionar campo e engenharia detalhada.

**P: Por que esses pesos?**
> Os pesos (engenharia 25 %, orçamento 25 %, mercado 20 %, social 20 %, pontes 10 %) refletem a premissa de que limitações técnicas ou financeiras são bloqueantes — por isso peso maior. Os demais são habilitadores. Estão explicitamente documentados como *"hipótese de MVP para fins de demonstração"* — não representam metodologia real de investimento.

---

*Documento gerado em: 2026-11-03 | Branch: `docs/roteiro-demo` | Commit base: `1010f96`*
*Scores de referência: `RESULTADOS_REGIOES.md` | Sistema: Conecta Conselho — MVP*
