# Roteiro do Vídeo — Conecta Conselho

**Duração máxima:** 3 minutos (180 s)  
**Destino:** Banca do IBM AI Experiential Learning Lab  
**Idioma da narração:** escolher entre Português (Seção A) ou Inglês (Seção B)  
**Dados:** 100 % simulados — avisar na narração

---

## Estrutura de Tempo

| Bloco | Tempo | Duração | Conteúdo |
|---|---|---|---|
| 1 — Problema | 0:00–0:25 | 25 s | Problema real, sem solução atual |
| 2 — Solução | 0:25–0:45 | 20 s | O que é o Conecta Conselho |
| 3 — Demo | 0:45–2:15 | 90 s | Produto funcionando na tela |
| 4 — IBM Bob | 2:15–2:45 | 30 s | Como o IBM Bob foi usado |
| 5 — Impacto | 2:45–3:00 | 15 s | Escala e próximos passos |

**Total: 3:00 | Demonstração: 90 s ✅**

---

## Seção A — Narração em Português

### Bloco 1 — Problema (0:00–0:25)

**O que aparece na tela:** mapa ou imagem estática de regiões rurais sem conectividade; pode ser print do IBGE ou imagem genérica de escola sem sinal. Fundo escuro preferível para contraste.

> *"Quando uma operadora decide onde expandir a internet, o critério costuma ser um só: lucro. Resultado: escolas sem conexão, postos de saúde sem telemedicina e comunidades inteiras fora da rede — exatamente as que mais precisam. O problema não é falta de dados. É falta de um processo que traga outras perspectivas para a mesa."*

---

### Bloco 2 — Solução (0:25–0:45)

**O que aparece na tela:** diagrama conceitual dos 5 agentes e do Guardião (pode ser o fluxo do CONTEXTO_PROJETO.md ou a aba "⚙️ Como funciona" do Streamlit). Mostrar os nomes dos agentes em destaque.

> *"O Conecta Conselho coloca cinco agentes de IA no IBM watsonx Orchestrate — cada um defende um ponto de vista: Mercado, Impacto Social, Engenharia, Orçamento e Pontes. O Guardião consolida com regras auditáveis e transparentes. Todos os dados são simulados. Uma pessoa decide — o sistema explica o porquê."*

---

### Bloco 3 — Demonstração (0:45–2:15) — 90 segundos na tela

> *"Veja funcionando."*

O app tem 3 páginas: **⚙️ Como funciona**, **🗺️ Análise de Região** e **🧪 Simulador de cenários**. O mapa fica dentro das páginas Análise e Simulador — colorido pela recomendação do Guardião: 🟢 verde = realizar piloto, 🔵 azul = investir agora, 🟡 amarelo = aguardar, 🔴 borda vermelha = atenção prioritária.

#### 3a — Página 'Como funciona' (0:45–0:50, 5 s)

**O que aparece na tela:** aba "⚙️ Como funciona" do Streamlit aberta, mostrando o fluxo dos 5 agentes. Zoom 125 %, tela cheia no navegador.

> *(silêncio ou música de fundo leve — sem narração)*

---

#### 3b — Nova União no IBM watsonx Orchestrate — chamadas ao vivo (0:50–1:25, 35 s)

**O que aparece na tela:** abrir a página **🗺️ Análise de Região**. No mapa colorido, clicar na região `nova_uniao` (borda vermelha de atenção prioritária). Clicar em **▶ Executar Conselho**. Mostrar o `st.status` com as 5 chamadas ao vivo surgindo: `✅ Mercado — x s`, `✅ Impacto Social — x s`, etc. Exibir o cartão colorido amarelo **⏳ Aguardar** com score 30. Mostrar o gráfico radar dos 5 agentes. Mostrar o alerta `⚠️ Atenção Prioritária` (borda vermelha). Expandir **🔍 Por que aguardar** (motivos) e **🛤️ Caminhos para viabilizar**. Expandir **⚖️ Conflitos entre especialistas (1)** — mostrar D1: cc_impacto_social = 78 vs. cc_orcamento = 0, diferença de 78.

> *"Nova União: impacto social altíssimo — 82 % dos domicílios sem internet. Mas o backbone está a 98 km e o orçamento não fecha. O Guardião recomenda aguardar, e dispara um alerta de atenção prioritária: essa região não pode ser esquecida. Ele explica por que aguardar e o que tornaria a região viável."*

---

#### 3c — Central — piloto com divergência (1:25–1:45, 20 s)

**O que aparece na tela:** clicar na região `central` no mapa (cor verde). Executar Conselho. Mostrar o cartão verde **🔬 Começar com piloto**, score 60. Expandir **⚖️ Conflitos entre especialistas (1)** — cc_orcamento = 76 vs. cc_impacto_social = 30.

> *"Central: ótima infraestrutura, orçamento folgado — mas impacto social baixo. O sistema não aprova direto. Identifica a divergência e recomenda piloto. O lucro sozinho não justifica o investimento sem retorno social."*

---

#### 3d — Simulador: Esperança com parcerias (1:45–2:05, 20 s)

**O que aparece na tela:** ir para a página **🧪 Simulador de cenários**. No mapa, clicar na região `esperanca`. Clicar no botão de atalho **▶️ História do one-pager: Esperança com parcerias** — isso ativa as parcerias do Agente Pontes automaticamente. Mostrar o cartão base **⏳ Aguardar** (score 44) e o cartão simulado **🔬 Realizar Piloto** (score 50). Mostrar a premissa: "Parcerias ativadas: CAPEX reduzido em 28 % via compartilhamento de infraestrutura — orçamento recalculado."

> *"Esperança: recomendação inicial — aguardar, score 44. O Simulador mostra: ao ativar as parcerias do Agente Pontes, o custo de implantação cai 28 % por compartilhamento de infraestrutura, o orçamento é recalculado e o score sobe para 50 — o piloto se torna viável. Não é uma decisão automática — é uma hipótese para o analista investigar em campo."*

---

#### 3e — Mapa na Análise e no Simulador (2:05–2:15, 10 s)

**O que aparece na tela (dois momentos):**
1. Na página **🗺️ Análise de Região**: mostrar o mapa colorido com todas as regiões — verde (piloto), azul (investir), amarelo (aguardar), borda vermelha (atenção prioritária em Nova União). Clicar na Nova União para destacar a borda vermelha.
2. Na página **🧪 Simulador de cenários**: mover o slider **📡 Nova distância do backbone (km)** e mostrar a região Esperança mudando de cor no mapa conforme a recomendação muda.

*(Opcional, se couber nos 90 s: mostrar 3–5 s da seção **⚖️ Comparar Regiões** — Central × Nova União — dentro da página de Análise.)*

> *"O mapa consolida todas as análises — cada cor é uma recomendação explicável. E no Simulador, ao mover o slider de distância do backbone, o mapa atualiza em tempo real."*

---

### Bloco 4 — Como construímos com o IBM Bob (2:15–2:45)

**O que aparece na tela (sequência de trechos de tela — ver lista completa na Seção de Gravação):**

1. **Bob criando a ferramenta do agente** — tela do IDE com o IBM Bob gerando o código de `tool_engenharia.py` ou `scripts/gerar_ferramenta_nuvem.py` a partir de um prompt.
2. **Bob publicando no Orchestrate** — Bob executando `orchestrate tools import` e `orchestrate agents import` no terminal integrado.
3. **Bob diagnosticando modelo indisponível** — janela do Bob mostrando diagnóstico: os YAMLs referenciavam modelos Llama inexistentes na instância; o Bob rodou `orchestrate models list` e trocou para `groq/openai/gpt-oss-120b`.
4. **Bob criando o gerador de ferramentas** — Bob escrevendo `scripts/gerar_ferramenta_nuvem.py` a partir da descrição do problema de `ModuleNotFoundError` em nuvem (erro de importação — gerador de ferramentas autocontidas).
5. **Tela do watsonx Orchestrate** — Agent Builder com os 5 agentes `cc_engenharia`, `cc_mercado`, `cc_impacto_social`, `cc_orcamento`, `cc_pontes` listados.

> *"Todo o pipeline foi construído com o IBM Bob. O Bob criou as ferramentas dos agentes e publicou cada agente no IBM watsonx Orchestrate. Quando os YAMLs referenciavam modelos Llama inexistentes, o Bob rodou 'orchestrate models list' e trocou para os modelos disponíveis — sem sair do IDE. Em outro diagnóstico, um erro de importação em nuvem levou o Bob a gerar o gerador automático de versões self-contained."*

---

### Bloco 5 — Impacto e escala (2:45–3:00)

**O que aparece na tela:** tela do Streamlit com dados das análises — mapa com todas as regiões coloridas, ou botão de download do relatório JSON. Mencionar "dados simulados" explicitamente.

> *"Com dados públicos reais — IBGE, Anatel, INEP, CNES — essa lógica escala para qualquer região do Brasil. Aqui os dados são simulados; a arquitetura é real. Decisões explicáveis. Auditáveis. Com voz de quem mais precisa de conexão."*

---

---

## Seção B — Narração em Inglês

### Block 1 — Problem (0:00–0:25)

> *"When a telecom operator decides where to expand internet access, the criterion is usually just one: profit. The result: schools without connectivity, health clinics without telemedicine, and entire communities left offline — exactly the ones who need it most. The problem isn't a lack of data. It's a lack of a process that brings other perspectives to the table."*

---

### Block 2 — Solution (0:25–0:45)

> *"Conecta Conselho puts five AI agents in IBM watsonx Orchestrate — each one defends a different point of view: Market, Social Impact, Engineering, Budget, and Bridges. The Guardian consolidates with auditable, transparent rules. All data is simulated. A human decides — the system explains why."*

---

### Block 3 — Demo (0:45–2:15)

> *"Watch it work."*

The app has 3 pages: **⚙️ How it works**, **🗺️ Region Analysis**, and **🧪 Scenario Simulator**. The map lives inside the Analysis and Simulator pages — colored by the Guardian's recommendation: 🟢 green = pilot, 🔵 blue = invest now, 🟡 yellow = wait, 🔴 red border = priority alert.

#### 3a — 'How it works' page (0:45–0:50)

> *(silence or background music)*

#### 3b — Nova União on IBM watsonx Orchestrate — live calls (0:50–1:25)

**On screen:** open **🗺️ Region Analysis**. On the colored map, click `nova_uniao` (red border). Click **▶ Run Council**. Show the live `st.status` with all 5 agent calls appearing: `✅ Market — x s`, `✅ Social Impact — x s`, etc. Show the yellow card **⏳ Wait**, score 30. Show the radar chart. Show the **⚠️ Priority Alert** (red border). Expand **🔍 Why wait** (reasons) and **🛤️ Paths to viability**. Expand **⚖️ Expert conflicts (1)** — cc_impacto_social = 78 vs. cc_orcamento = 0.

> *"Nova União: extremely high social impact — 82% of households without internet. But the backbone is 98 km away and the budget doesn't add up. The Guardian recommends waiting, and fires a priority attention alert: this region cannot be forgotten. It explains why to wait and what would make the region viable."*

#### 3c — Central — pilot with divergence (1:25–1:45)

> *"Central: excellent infrastructure, budget to spare — but low social impact. The system doesn't approve immediately. It flags the divergence and recommends a pilot. Profit alone doesn't justify the investment without social return."*

#### 3d — Simulator: Esperança with partnerships (1:45–2:05)

**On screen:** go to **🧪 Scenario Simulator**. Click `esperanca` on the map. Click **▶️ História do one-pager: Esperança com parcerias** (one-pager story shortcut). Show base card **⏳ Wait** (score 44) and simulated card **🔬 Pilot** (score 50). Show the premise: "Partnerships activated: CAPEX reduced by 28% via infrastructure sharing — budget recalculated."

> *"Esperança: initial recommendation — wait, score 44. The Simulator shows: activating the Bridges Agent's partnerships cuts deployment costs by 28% through infrastructure sharing, the budget is recalculated, and the score rises to 50 — a pilot becomes viable. Not an automatic decision — a hypothesis for the analyst to investigate in the field."*

#### 3e — Map in Analysis and Simulator (2:05–2:15)

**On screen (two moments):**
1. In **🗺️ Region Analysis**: the colored map — green (pilot), blue (invest), yellow (wait), red border (Nova União priority alert). Click Nova União to highlight the red border.
2. In **🧪 Scenario Simulator**: move the **📡 New backbone distance (km)** slider and watch Esperança change color on the map in real time.

*(Optional, if it fits in 90 s: show 3–5 s of the **⚖️ Compare Regions** section — Central × Nova União.)*

> *"The map consolidates all analyses — each color is an explainable recommendation. In the Simulator, moving the backbone distance slider updates the map in real time."*

---

### Block 4 — Built with IBM Bob (2:15–2:45)

> *"The entire pipeline was built with IBM Bob. Bob created the agent tools and published each agent in IBM watsonx Orchestrate. When the YAMLs referenced Llama models that didn't exist on the instance, Bob ran 'orchestrate models list' and switched to the available models — without leaving the IDE. In a separate diagnosis, a cloud import error led Bob to generate the automatic self-contained tool generator."*

---

### Block 5 — Impact and scale (2:45–3:00)

> *"With real public data — IBGE, Anatel, INEP, CNES — this logic scales to any region in Brazil. Here the data is simulated; the architecture is real. Explainable decisions. Auditable. With a voice for those who need connectivity most."*

---

---

## Lista de Trechos de Tela — Quem Grava o Quê

> Cada gravadora salva o arquivo como `clip_XX_nome.mp4` e envia para a pasta compartilhada do grupo antes da edição.

| # | Clip | Quem grava | O que mostrar | Duração sugerida |
|---|---|---|---|---|
| 01 | `clip_01_problema` | Thaly | Imagem/print de região sem conectividade + título do problema | 25 s |
| 02 | `clip_02_diagrama` | Ana | Diagrama dos 5 agentes (print do CONTEXTO_PROJETO.md ou Streamlit "⚙️ Como funciona") | 20 s |
| 03 | `clip_03_como_funciona` | Ana | Aba "⚙️ Como funciona" no Streamlit, zoom 125 % | 5 s |
| 04 | `clip_04_nova_uniao` | Laura | Streamlit — página "🗺️ Análise de Região" → clicar Nova União no mapa (borda vermelha) → ▶ Executar Conselho → status das 5 chamadas ao vivo → cartão amarelo Aguardar (score 30) → radar → alerta ⚠️ Atenção Prioritária → Por que aguardar + Caminhos para viabilizar → conflito cc_impacto_social 78 × cc_orcamento 0 | 35 s |
| 05 | `clip_05_central` | Gabi | Streamlit — Central no mapa → Executar Conselho → cartão verde Começar com piloto (score 60) → conflito cc_orcamento 76 × cc_impacto_social 30 | 20 s |
| 06 | `clip_06_esperanca_simulador` | Mi | Streamlit — página "🧪 Simulador de cenários" → clicar Esperança no mapa → botão "▶️ História do one-pager: Esperança com parcerias" → cartão base Aguardar 44 → cartão simulado Realizar Piloto 50 → premissa CAPEX −28 % | 20 s |
| 07 | `clip_07_mapa` | Ana | Página "🗺️ Análise de Região": mapa colorido → clicar Nova União (borda vermelha). Página "🧪 Simulador": mover slider de distância do backbone → Esperança muda de cor no mapa | 10 s |
| 08 | `clip_08_bob_cria_ferramenta` | Laura | IBM Bob no IDE criando tool_engenharia ou gerar_ferramenta_nuvem.py | 8 s |
| 09 | `clip_09_bob_publica` | Laura | IBM Bob executando orchestrate tools import + agents import no terminal | 8 s |
| 10 | `clip_10_bob_modelo_indisponivel` | Laura | IBM Bob diagnosticando YAMLs com modelos Llama inexistentes → rodando `orchestrate models list` → trocando para groq/openai/gpt-oss-120b | 7 s |
| 11 | `clip_11_bob_gerador` | Laura | IBM Bob escrevendo scripts/gerar_ferramenta_nuvem.py a partir da descrição do problema de ModuleNotFoundError em nuvem | 7 s |
| 12 | `clip_12_orchestrate_agentes` | Laura | Tela do Agent Builder (jp-tok) com cc_engenharia, cc_mercado, cc_impacto_social, cc_orcamento, cc_pontes listados | 5 s |
| 13 | `clip_13_impacto` | Thaly | Mapa ou tela de relatório JSON + texto de fontes (IBGE, Anatel, INEP, CNES) | 15 s |

---

## Dicas de Gravação

### Configurações técnicas

| Item | Configuração recomendada |
|---|---|
| Resolução | **1080p (1920×1080)** — mínimo aceitável pela banca |
| Zoom do navegador | **125 %** — leitura clara em tela pequena |
| Modo escuro | **Desligado** — fundo branco garante contraste nos prints |
| Notificações | **Silenciadas** — Windows: Foco Assistido ativado antes de gravar |
| Microfone | Fone com microfone embutido; gravar em ambiente silencioso |
| Velocidade de clique | Pausar 1–2 s após cada clique para a câmera registrar a transição |

### Ferramenta sugerida

**OBS Studio** (gratuito, open source — https://obsproject.com)
- Captura tela + áudio do microfone simultaneamente
- Exportar em MP4 (H.264), qualidade CRF 18–23
- Configurar "Captura de Janela" para gravar só o navegador ou o IDE

**Alternativa: Clipchamp** (vem instalado no Windows 11)
- Abrir pelo Menu Iniciar → buscar "Clipchamp"
- Gravar tela com narração em uma única tomada
- Exportar em 1080p gratuito

### Fluxo recomendado

1. Gravar cada clip separado (facilita re-gravação de erros pontuais)
2. Revisar cada clip antes de enviar para a pasta do grupo
3. Editar no Clipchamp ou DaVinci Resolve (gratuito): colocar clips na ordem, adicionar narração gravada separadamente sobre os clips
4. Adicionar legendas automáticas (Clipchamp gera automaticamente)
5. Exportar final único em MP4 1080p

---

## Checklist de Publicação

### Antes de publicar

- [ ] Vídeo final exportado em MP4 1080p, duração ≤ 3:00
- [ ] Narração sem cortando ou eco audível
- [ ] Tela do IBM Bob aparece com clareza (clips 08–12)
- [ ] Nomes dos agentes (`cc_engenharia`, `cc_mercado`, `cc_impacto_social`, `cc_orcamento`, `cc_pontes`) legíveis em pelo menos um frame
- [ ] Aviso "dados simulados" aparece ou é mencionado na narração
- [ ] Revisar que nenhuma credencial (API Key, URL privada) aparece na gravação

### Publicação

**Opção A — YouTube (recomendado)**
1. Fazer upload no YouTube
2. Visibilidade: **"Não listado"** (apenas quem tem o link consegue ver)
3. Título sugerido: `Conecta Conselho — IBM AI Experiential Learning Lab`
4. Testar o link em aba anônima (`Ctrl+Shift+N`) antes de enviar para a banca

**Opção B — Google Drive**
1. Fazer upload da pasta/arquivo no Drive
2. Compartilhamento: **"Qualquer pessoa com o link" → Leitor**
3. Testar o link em aba anônima antes de enviar

### Após publicar

- [ ] Link testado em aba anônima ✅
- [ ] Link adicionado ao README do repositório (seção "Vídeo de demonstração")
- [ ] Link enviado para a banca pelo canal oficial da trilha

---

## Observações Finais

- **Cores no app:** 🟢 verde = realizar piloto | 🔵 azul = investir agora | 🟡 amarelo = aguardar | 🔴 borda vermelha = atenção prioritária.
- **Idioma:** decidir entre Português (Seção A) e Inglês (Seção B) como grupo — não misturar nas legendas.
- **Música de fundo:** opcional; se usar, manter volume baixo (~15 % do microfone) e sem direitos autorais (use YouTube Audio Library ou Pixabay Music).
- **Plano B de gravação:** se a nuvem IBM Cloud estiver instável, escolher **"Local"** na barra lateral do app — os resultados são idênticos, calculados deterministicamente.
- **Duração real dos agentes na nuvem:** cada chamada ao Executar Conselho pode levar 5–15 s dependendo da latência. Ensaiar antes para ajustar o ritmo da narração.

---

*Roteiro criado em: 2026-11-04 | Revisado em: 2026-11-06 | Branch: `docs/roteiro-video` | Base: `ROTEIRO_DEMO.md`, `CONTEXTO_PROJETO.md`, `RESULTADOS_REGIOES.md`, `GUIA_PUBLICACAO_AGENTES.md`*
