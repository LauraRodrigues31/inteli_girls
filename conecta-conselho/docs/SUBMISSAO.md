# Conecta Conselho — Textos de Submissão
## IBM AI Experiential Learning Lab · Trilha 3 · Telecomunicações Inteligentes

> ⚠️ **AVISO: todos os dados utilizados na demonstração são SIMULADOS e FICTÍCIOS.**
> Não representam indicadores reais de nenhuma região, operadora ou instituição brasileira.
> Não há dados pessoais no sistema.

---

## TEXTO 1 — Problem and Solution Statement
*(máximo 500 palavras — contagem real da versão em inglês: **414 palavras**)*

### Versão em inglês

Telecom operators must decide where to expand connectivity. Current planning processes tend to prioritize financially attractive areas, leaving underserved regions — including those with schools, health clinics, and public institutions — without access. A standard return-on-investment analysis silences the social perspective and misses opportunities to anchor demand through public partnerships.

**Conecta Conselho** is a multi-agent AI decision-support system that helps expansion planning analysts evaluate connectivity opportunities by bringing five competing perspectives into the same analysis. The system runs on IBM watsonx Orchestrate and is designed for a primary user who is a planning analyst or expansion manager at a telecom operator. Secondary users include social impact teams, engineering departments, and investment managers.

The analyst opens the dashboard, selects a region, and immediately sees five independent expert opinions — one per agent — covering market return, social impact, engineering feasibility, budget viability, and anchor partnerships. A deterministic Guardian consolidates these opinions into a single score and one of three recommendations: **Invest now**, **Start with a pilot**, or **Wait**. When any dimension scores critically low, the system raises a **Priority Alert** to flag that human review is essential before any decision is made.

The interaction is straightforward: the analyst chooses a region, reads the five views, examines the Guardian's reasoning, explores the **What-if Simulator** (e.g., "what if a partnership reduced CAPEX by 28%?"), and views the **Illustrative Map** showing all regions sized by population and colored by recommendation. Every screen carries a "simulated data" disclaimer. The analyst can export a structured JSON report with all scores, indicators, divergences, and audit trail.

What makes Conecta Conselho creative is the design choice to give agents **opposing mandates on purpose**: the Market Agent defends financial return while the Social Impact Agent defends schools and clinics, so no recommendation can be purely profit-driven. The Bridges Agent actively searches for anchor clients (schools, health units, city halls) that could make an unviable region viable — and the Simulator proves it: the Esperança region goes from "Wait" (score 44) to "Start pilot" (score 50) when partnerships are factored in.

Decisions are **deterministic and auditable**: no LLM invents numbers. All calculations use documented Python formulas applied to structured data. The Priority Alert replaces a black-box escalation rule with a transparent flag. The system is ready to scale: replacing simulated data with real sources (IBGE, Anatel, INEP, CNES) and adding new regions requires no architectural changes.

The demonstration uses entirely **simulated, fictional data**. No personal data is collected or processed.

---

### Versão em português

Operadoras de telecomunicações precisam decidir onde expandir a conectividade. Os processos atuais de planejamento tendem a priorizar regiões financeiramente atrativas, deixando áreas desassistidas — incluindo aquelas com escolas, postos de saúde e instituições públicas — sem acesso. Uma análise padrão de retorno sobre investimento silencia a perspectiva social e ignora oportunidades de ancorar a demanda por meio de parcerias com o setor público.

O **Conecta Conselho** é um sistema multiagente de apoio à decisão que ajuda analistas de planejamento de expansão de operadoras a avaliar oportunidades de conectividade reunindo cinco perspectivas concorrentes na mesma análise. O sistema roda no IBM watsonx Orchestrate e é destinado a um usuário principal que é analista ou gerente de planejamento de expansão. Usuários secundários incluem equipes de impacto social, áreas de engenharia e gestores de investimento.

O analista abre o dashboard, seleciona uma região e vê imediatamente cinco pareceres especializados e independentes — um por agente — cobrindo retorno de mercado, impacto social, viabilidade de engenharia, viabilidade orçamentária e parcerias âncora. Um Guardião determinístico consolida esses pareceres em um score único e uma de três recomendações: **Investir agora**, **Realizar piloto** ou **Aguardar**. Quando qualquer dimensão atinge um patamar crítico, o sistema emite um **Alerta de Atenção Prioritária** sinalizando que a revisão humana é essencial antes de qualquer decisão.

A interação é direta: o analista escolhe uma região, lê os cinco pareceres, examina o raciocínio do Guardião, explora o **Simulador de Cenários** (ex.: "e se uma parceria reduzisse o CAPEX em 28%?") e visualiza o **Mapa Ilustrativo** mostrando todas as regiões dimensionadas por população e coloridas pela recomendação. Toda tela exibe o aviso "dados simulados". O analista pode exportar um relatório JSON estruturado com todos os scores, indicadores, divergências e trilha de auditoria.

O que torna o Conecta Conselho criativo é a escolha de design de dar aos agentes **mandatos opostos de propósito**: o Agente de Mercado defende o retorno financeiro enquanto o Agente de Impacto Social defende escolas e postos de saúde, para que nenhuma recomendação seja puramente orientada ao lucro. O Agente de Pontes busca ativamente clientes âncora (escolas, unidades de saúde, prefeituras) que possam tornar uma região inviável em viável — e o Simulador prova isso: a região Esperança passa de "Aguardar" (score 44) para "Realizar piloto" (score 50) quando as parcerias são consideradas.

As decisões são **determinísticas e auditáveis**: nenhum LLM inventa números. Todos os cálculos usam fórmulas Python documentadas aplicadas a dados estruturados. O Alerta de Atenção Prioritária substitui uma regra de escalonamento de caixa-preta por um sinalizador transparente. O sistema está pronto para escalar: substituir dados simulados por fontes reais (IBGE, Anatel, INEP, CNES) e adicionar novas regiões não requer mudanças arquiteturais.

A demonstração usa **dados inteiramente simulados e fictícios**. Nenhum dado pessoal é coletado ou processado.

---

## TEXTO 2 — Technology Statement
*(objetivo e específico)*

### Versão em inglês

**IBM Bob**

IBM Bob was central to every development phase of Conecta Conselho. We used the `wxo-builder` skill throughout to configure the ADK environment, implement Python tools, author agent YAML files, write tests, and publish to watsonx Orchestrate. Key uses included:

- **Environment and ADK setup:** Bob guided the initial configuration of the `ibm-watsonx-orchestrate` ADK (version 2.19.1) in a Python 3.12 virtual environment on Windows, resolving path and encoding issues specific to PowerShell.
- **Agent tool implementation:** Bob authored and refined the five Python tool files (`tool_mercado.py`, `tool_social.py`, `tool_engenharia.py`, `tool_orcamento.py`, `tool_pontes.py`) and the Guardian (`tool_guardiao.py`), each implementing deterministic scoring formulas documented in the development standard.
- **Diagnostics:** Bob diagnosed three critical issues: (1) the YAML files initially used Llama models (`watsonx/meta-llama/llama-3-3-70b-instruct`, `llama-3-1-70b-instruct`, `llama-3-2-90b-vision-instruct`) that did not exist on the instance; Bob ran `orchestrate models list`, identified the available models, and we switched to `groq/openai/gpt-oss-120b`; (2) a `@tool` decorator was registered under a wrong function name, causing the agent to call a non-existent tool; (3) `orchestrate chat ask` hangs on Windows due to an interactive EOF loop — Bob identified this and recommended the REST API as an alternative.
- **Self-contained tool generator:** Bob designed and implemented `scripts/gerar_ferramenta_nuvem.py`, which embeds `regioes.json` as a Python dictionary inside the tool file, eliminating `ModuleNotFoundError` in the cloud runtime's isolated execution environment.
- **Publication and test scripts:** Bob created `scripts/publicar_agente.ps1` (PowerShell) and `scripts/testar_agente_nuvem.py`, which discover the agent ID dynamically via `orchestrate agents list -v` and test any agent against the IBM runtime API without hardcoding UUIDs or credentials.
- **Streamlit integration:** Bob implemented the multi-source integration layer (`integracao.py`, `cliente_nuvem.py`) that calls the five agents in parallel using a `ThreadPoolExecutor` (5 concurrent calls), consolidates results locally, and presents two modes the user explicitly chooses between: **IBM watsonx Orchestrate** and **Local** (the demo's plan B).
- **Test coverage:** Bob authored and maintained the automated test suite, which currently counts **883 passing tests** covering all agent tools, the Guardian, integration mocks, and the Streamlit interface.

**IBM watsonx Orchestrate**

- **ADK version:** `ibm-watsonx-orchestrate` 2.19.1
- **Agents:** 5 native agents — `cc_mercado`, `cc_impacto_social`, `cc_engenharia`, `cc_orcamento`, `cc_pontes` — each with one Python tool and strict YAML instructions enforcing deterministic JSON output.
- **LLM model:** all five agents use `groq/openai/gpt-oss-120b`. We also evaluated IBM Granite: the only instruction-tuned Granite model available in our instance was `watsonx/ibm/granite-4-h-small` (Granite 4.0, 30B). We switched the Engineering agent to it and ran our cloud test suite; in all three calls the agent did not invoke its analysis tool and returned an error. We reverted to the original model, the tests passed again (about 8 s per call), and kept `gpt-oss-120b` for all five agents. IBM Bob ran the swap, the test, and the rollback in a controlled way.
- **Publication:** via `orchestrate tools import -k python` and `orchestrate agents import -f agents/agente_<name>.yaml`.
- **Runtime API:** Streamlit calls agents in parallel via `POST <WXO_URL>/v1/orchestrate/<agent_id>/chat/completions` with IBM IAM authentication. The Guardian consolidation runs locally in Python — not in the cloud.
- **Architectural decision:** We tested a Guardian agent with collaborators in watsonx Orchestrate. The agent received the five specialist opinions but did not reliably call the consolidation tool — it returned incomplete or reformatted results. We moved the consolidation to a deterministic Python function (`consolidar_pareceres` in `tools/tool_guardiao.py`), which is consistent, testable, and auditable.

**Other technologies**

- Python 3.12, Streamlit (multi-page with `st.navigation`), Plotly (radar chart, bar chart, map), pytest (883 tests), GitHub (branch-per-feature, PR to `develop`, Laura merges and releases to `main`).

---

### Versão em português

**IBM Bob**

O IBM Bob foi central em todas as fases de desenvolvimento do Conecta Conselho. Utilizamos a skill `wxo-builder` ao longo de todo o projeto para configurar o ambiente ADK, implementar ferramentas Python, criar os arquivos YAML dos agentes, escrever testes e publicar no watsonx Orchestrate. Os principais usos incluíram:

- **Configuração do ambiente e ADK:** o Bob orientou a configuração inicial do ADK `ibm-watsonx-orchestrate` (versão 2.19.1) em um ambiente virtual Python 3.12 no Windows, resolvendo problemas de caminho e codificação específicos do PowerShell.
- **Implementação das ferramentas dos agentes:** o Bob escreveu e refinou os cinco arquivos de ferramentas Python (`tool_mercado.py`, `tool_social.py`, `tool_engenharia.py`, `tool_orcamento.py`, `tool_pontes.py`) e o Guardião (`tool_guardiao.py`), cada um implementando fórmulas de score determinísticas documentadas no padrão de desenvolvimento.
- **Diagnósticos:** o Bob diagnosticou três problemas críticos: (1) os arquivos YAML usavam inicialmente modelos Llama (`watsonx/meta-llama/llama-3-3-70b-instruct`, `llama-3-1-70b-instruct`, `llama-3-2-90b-vision-instruct`) que não existiam na instância; o Bob rodou `orchestrate models list`, identificou os modelos disponíveis e trocamos para `groq/openai/gpt-oss-120b`; (2) um decorator `@tool` foi registrado com o nome errado da função, fazendo o agente chamar uma ferramenta inexistente; (3) `orchestrate chat ask` trava no Windows por um loop EOF interativo — o Bob identificou o problema e recomendou a API REST como alternativa.
- **Gerador de ferramentas autocontidas:** o Bob projetou e implementou `scripts/gerar_ferramenta_nuvem.py`, que embute `regioes.json` como dicionário Python dentro do arquivo da ferramenta, eliminando o `ModuleNotFoundError` no ambiente de execução isolado do runtime em nuvem.
- **Scripts de publicação e teste:** o Bob criou `scripts/publicar_agente.ps1` (PowerShell) e `scripts/testar_agente_nuvem.py`, que descobrem o ID do agente dinamicamente via `orchestrate agents list -v` e testam qualquer agente contra a API de runtime da IBM sem hardcode de UUIDs ou credenciais.
- **Integração com o Streamlit:** o Bob implementou a camada de integração multi-fonte (`integracao.py`, `cliente_nuvem.py`) que chama os cinco agentes em paralelo usando um `ThreadPoolExecutor` (5 chamadas simultâneas), consolida os resultados localmente e apresenta dois modos que o usuário escolhe explicitamente: **IBM watsonx Orchestrate** e **Local** (plano B da demo).
- **Cobertura de testes:** o Bob escreveu e manteve a suíte de testes automatizados, que atualmente conta com **883 testes passando**, cobrindo todas as ferramentas dos agentes, o Guardião, mocks de integração e a interface Streamlit.

**IBM watsonx Orchestrate**

- **Versão do ADK:** `ibm-watsonx-orchestrate` 2.19.1
- **Agentes:** 5 agentes nativos — `cc_mercado`, `cc_impacto_social`, `cc_engenharia`, `cc_orcamento`, `cc_pontes` — cada um com uma ferramenta Python e instruções YAML rígidas que garantem saída JSON determinística.
- **Modelo de LLM:** os cinco agentes usam `groq/openai/gpt-oss-120b`. Também avaliamos o IBM Granite: o único Granite de instrução disponível na nossa instância era o `watsonx/ibm/granite-4-h-small` (Granite 4.0, 30B). Trocamos o agente de Engenharia para ele e rodamos nossa suíte de testes na nuvem; nas três chamadas o agente não acionou a ferramenta de análise e respondeu com erro. Voltamos ao modelo original, os testes passaram de novo (cerca de 8 s por chamada) e mantivemos o `gpt-oss-120b` nos cinco agentes. O IBM Bob conduziu a troca, o teste e a volta ao original de forma controlada.
- **Publicação:** via `orchestrate tools import -k python` e `orchestrate agents import -f agents/agente_<nome>.yaml`.
- **API de runtime:** o Streamlit chama os agentes em paralelo via `POST <WXO_URL>/v1/orchestrate/<agent_id>/chat/completions` com autenticação IBM IAM. A consolidação do Guardião roda localmente em Python — não na nuvem.
- **Decisão de arquitetura:** testamos um agente Guardião com colaboradores no watsonx Orchestrate. O agente recebia os cinco pareceres mas não chamava a ferramenta de consolidação de forma confiável — devolvia resultados incompletos ou reformatados. Movemos a consolidação para uma função Python determinística (`consolidar_pareceres` em `tools/tool_guardiao.py`), que é consistente, testável e auditável.

**Outras tecnologias**

Python 3.12, Streamlit (multi-página com `st.navigation`), Plotly (gráfico radar, barras, mapa), pytest (883 testes), GitHub (branch por funcionalidade, PR para `develop`, Laura faz merges e release para `main`).

---

*Versão 2 — 05/11/2026. Atualizado com resultado do teste Granite (L1) e revisões do PR #19. Versão final após merges das páginas.*
