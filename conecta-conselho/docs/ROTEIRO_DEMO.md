# Roteiro da Demonstração — Conecta Conselho

**Duração total:** 7–8 minutos | **Formato:** live no site (front React) + nuvem IBM watsonx Orchestrate
**Dados:** 100 % simulados — avisar à banca no início

---

## 1. Abertura (30 s)

**Quem fala:** qualquer integrante

> *"Operadoras de telecomunicações precisam decidir onde expandir a rede — e essa decisão envolve muito mais do que lucro. Uma análise só financeira pode ignorar comunidades que mais precisam de conectividade. O Conecta Conselho reúne cinco perspectivas especializadas — mercado, impacto social, engenharia, orçamento e parcerias — para que **nenhuma decisão seja tomada só pelo lucro**."*

---

## 2. Regiões demonstradas

O app tem **3 páginas**: **📖 Como funciona**, **🔍 Análise de Região** e **🧪 Simulador de cenários**. O **mapa interativo** fica dentro das páginas Análise e Simulador — colorido pela recomendação do Guardião: 🟢 verde = realizar piloto, 🔵 azul = investir agora, 🟡 amarelo = aguardar, 🔴 borda vermelha = atenção prioritária. A pessoa escolhe a região **clicando no mapa**.

Três regiões foram escolhidas para contar histórias contrastantes com os números do `RESULTADOS_REGIOES.md`.

---

### Região 1 — Central (realizar piloto)

**História:** ótima engenharia e orçamento, mas pouco impacto social. O sistema não aprova direto.

| # | O que clicar / fazer | O que aparece na tela | Quem fala | Fala sugerida |
|---|---|---|---|---|
| 1 | Abrir **🔍 Análise de Região** → clicar em **Central** no mapa (cor verde) | "Região Central selecionada · Clique em outra região para mudar." | — | — |
| 2 | Clicar **▶ Executar Conselho** → aguardar as 5 chamadas | Painel de status ao vivo: `✅ Mercado — x s`, `✅ Impacto Social — x s`, etc. | — | — |
| 3 | Ver cartão do Guardião | `🔬 Realizar Piloto`, score consolidado 60 | **Guardião** (qualquer) | *"O Guardião consolida: engenharia e orçamento fortes justificam um piloto, mas o impacto social abaixo de 50 impede investimento imediato. Recomendação: realizar piloto."* |
| 4 | Ver radar dos 5 agentes | Gráfico radar com scores: Engenharia 86, Orçamento 76, Mercado 37, Social 30, Pontes 66 | **Laura (Engenharia)** | *"A Central tem a melhor infra da base: backbone perto, fibra já distribuída. Engenharia dá 86 de 100."* |
| 5 | Expandir **⚖️ Conflitos entre especialistas (1)** | D1 — cc_orcamento 76 alto × cc_impacto_social 30 baixo (\|76−30\|=46 > 30) | — | *"O sistema identificou uma divergência: orçamento forte mas impacto social fraco. Por isso piloto, e não investir agora."* |

---

### Região 2 — Nova União (aguardar com alerta de atenção prioritária)

**História:** impacto social altíssimo, mas financeiramente inviável e infraestrutura zerada. O Guardião recomenda aguardar e dispara o Alerta de Atenção Prioritária — essa região não pode ser esquecida.

| # | O que clicar / fazer | O que aparece na tela | Quem fala | Fala sugerida |
|---|---|---|---|---|
| 1 | Clicar em **Nova União** no mapa (borda vermelha) | "Região Nova União selecionada" — borda vermelha indica atenção prioritária antes mesmo de executar | **Thaly (Social)** | *"Nova União tem o maior impacto social da base: quase toda a população sem internet e altíssima vulnerabilidade."* |
| 2 | Clicar **▶ Executar Conselho** | Painel de status ao vivo com 5 chamadas | — | — |
| 3 | Ver cartão do Guardião | `⏳ Aguardar`, score consolidado 30, badge `⚠️ Atenção Prioritária` | **Guardião** | *"Consolidado 30. Orçamento 0 e Engenharia 11 — ambos abaixo de 20. O Guardião recomenda aguardar e dispara o Alerta de Atenção Prioritária: essa região não pode ser ignorada — ela exige programa de universalização, não investimento privado direto."* |
| 4 | Ver radar dos 5 agentes | Social 78, Pontes 21, Mercado 37, Engenharia 11, Orçamento 0 | **Gabi (Orçamento)** | *"A operação é deficitária: receita mensal não cobre nem o custo operacional. Score orçamento: 0."* |
| 5 | Expandir **🔍 Por que aguardar** e **🛤️ Caminhos para viabilizar** | Lista de motivos e caminhos | **Laura (Engenharia)** | *"Sem fibra alguma, backbone a 98 km. Seria construir do zero. Score engenharia: 11."* |
| 6 | Expandir **⚖️ Conflitos entre especialistas (1)** | D1 — cc_impacto_social 78 × cc_orcamento 0, \|diff\|=78 | — | *"A maior divergência da base: o maior impacto social junto com a pior viabilidade financeira. O alerta de atenção prioritária garante que a região não some do radar."* |

---

### Região 3 — Esperança (Simulador: aguardar → realizar piloto)

**História:** boa demanda de mercado, mas engenharia e orçamento fracos. Com parcerias, o Agente de Pontes muda o cenário.

| # | O que clicar / fazer | O que aparece na tela | Quem fala | Fala sugerida |
|---|---|---|---|---|
| 1 | Ir para **🧪 Simulador de cenários** → clicar em **Esperança** no mapa | Mapa no Simulador com Esperança selecionada | **Ana (Mercado)** | *"Boa demanda reprimida: dois terços dos domicílios sem internet e quase sem concorrência. Score mercado: 63."* |
| 2 | Clicar em **▶️ História do one-pager: Esperança com parcerias** | Parcerias ativadas automaticamente; cenário base e simulado calculados | — | — |
| 3 | Ver cartão base vs. simulado | Base: `⏳ Aguardar` score 44 → Simulado: `🔬 Realizar Piloto` score 50 | **Mi (Pontes)** | *"O Agente de Pontes ativa as parcerias: CAPEX reduzido em 28 % via compartilhamento de infraestrutura, o orçamento é recalculado e o score sobe para 50 — o piloto se torna viável."* |
| 4 | Ver premissa exibida | "Parcerias ativadas: CAPEX reduzido em 28 % via compartilhamento de infraestrutura — orçamento recalculado." | **Guardião** | *"Não é uma decisão automática — é uma hipótese para o analista investigar em campo."* |

---

## 3. Fechamento (30 s)

**Quem fala:** qualquer integrante

1. Mostrar as **divergências e limitações** do Guardião (expanders na tela de resultado): cada decisão expõe os indicadores usados, os riscos e as limitações.
2. Clicar em **⬇️ Baixar relatório JSON (trilha de auditoria)**: fazer download do relatório da última região analisada.
3. Encerrar com limitações:

> *"O sistema apoia a triagem — não autoriza obras, não calcula CAPEX real, não substitui análise de campo. Os dados são simulados. O que entregamos é a lógica: cinco perspectivas, pesos transparentes, divergências explícitas e o Alerta de Atenção Prioritária para que regiões críticas não sejam ignoradas."*

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
- [ ] Testar as 3 regiões na nuvem: central → realizar_piloto, esperanca → aguardar (base), nova_uniao → aguardar com alerta
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
> A confiança não é opinião do LLM: cada agente a calcula por regra no código. Na maioria dos agentes ela depende da completude dos dados — campos faltando reduzem a confiança. O Agente de Orçamento também reduz a confiança para `baixa` quando a operação é financeiramente inviável (receita menor que o custo operacional), como na Nova União. Não é uma probabilidade estatística.

**P: Os dados são reais?**
> Não. Todos os dados são 100 % simulados e fictícios, criados exclusivamente para fins de demonstração. O aviso aparece em todas as telas do site e no topo de cada relatório JSON. Não há nenhum dado real de municípios brasileiros.

**P: E se os agentes discordarem?**
> O Guardião identifica e registra divergências explicitamente (campo `divergencias`). Quando a tensão é alta — por exemplo, impacto social muito alto mas orçamento zero — o Guardião destaca na justificativa. Se alguma dimensão atingir patamar crítico (orçamento ou engenharia abaixo de 20), o sistema emite o **Alerta de Atenção Prioritária** sinalizando que a revisão humana é essencial. O desacordo é recurso, não bug.

**P: Quando o sistema dispara o Alerta de Atenção Prioritária?**
> Quando orçamento < 20, OU engenharia < 20, OU qualquer agente retorna confiança `baixa` ou erro — o sistema exibe o alerta `⚠️ Atenção Prioritária` junto com a recomendação (**Investir agora**, **Realizar piloto** ou **Aguardar**). A decisão final sempre é humana — o sistema só apoia a triagem.

**P: Por que nenhuma região recebe `investir_agora`?**
> O critério exige consolidado ≥ 70 **E** orçamento ≥ 60 **E** engenharia ≥ 60 simultaneamente. Com engenharia e orçamento pesando 50 % do consolidado, o sistema é deliberadamente conservador — nenhuma região da base atual justifica investimento imediato sem um piloto que valide campo e custos reais.

**P: Por que o Agente de Pontes não "garante" a demanda?**
> O Agente de Pontes identifica **possíveis** instituições âncora e modela cenários **hipotéticos** de articulação. Nenhum contrato real existe. A linguagem é sempre condicional: *"se a prefeitura se tornar âncora"*, não *"a prefeitura vai assinar"*. Isso está na Seção 6 do CONTEXTO e é regra obrigatória do PADRÃO (Seção 10).

**P: Isso substitui o analista?**
> Não. O sistema **apoia** a triagem de oportunidades. Não autoriza obras, não calcula CAPEX executivo, não faz geoprocessamento real, não negocia contratos. O usuário-alvo é um analista de planejamento que usa o sistema como primeira camada de análise antes de acionar campo e engenharia detalhada.

**P: Por que esses pesos?**
> Os pesos (engenharia 25 %, orçamento 25 %, mercado 20 %, social 20 %, pontes 10 %) refletem a premissa de que limitações técnicas ou financeiras são bloqueantes — por isso peso maior. Os demais são habilitadores. Estão explicitamente documentados como *"hipótese de MVP para fins de demonstração"* — não representam metodologia real de investimento.

---

*Documento atualizado em: 2026-11-06 | Branch: `docs/documentacao-final` | Alinhado com: `ROTEIRO_VIDEO.md`, `CONTEXTO_PROJETO.md`, `RESULTADOS_REGIOES.md`*
*3 páginas · mapa interativo na Análise e no Simulador · Nova União = aguardar com Alerta de Atenção Prioritária*
