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

---

## Seção A — Narração em Português

### Bloco 1 — Problema (0:00–0:25)

**O que aparece na tela:** mapa ou imagem estática de regiões rurais sem conectividade; pode ser print do IBGE ou imagem genérica de escola sem sinal. Fundo escuro preferível para contraste.

> *"Quando uma operadora decide onde expandir a internet, o critério costuma ser um só: lucro. Resultado: escolas sem conexão, postos de saúde sem telemedicina e comunidades inteiras fora da rede — exatamente as que mais precisam. O problema não é falta de dados. É falta de um processo que traga outras perspectivas para a mesa."*

---

### Bloco 2 — Solução (0:25–0:45)

**O que aparece na tela:** diagrama conceitual dos 5 agentes e do Guardião (pode ser o fluxo do CONTEXTO_PROJETO.md). Mostrar os nomes dos agentes em destaque.

> *"O Conecta Conselho coloca cinco agentes de IA no IBM watsonx Orchestrate — cada um defende um ponto de vista: Mercado, Impacto Social, Engenharia, Orçamento e Pontes. O Guardião consolida com regras auditáveis e transparentes. Uma pessoa decide — o sistema explica o porquê."*

---

### Bloco 3 — Demonstração (0:45–2:15) — 90 segundos na tela

> *"Veja funcionando."*

#### 3a — Página 'Como funciona' (0:45–0:50, 5 s)

**O que aparece na tela:** aba "Como funciona" do Streamlit aberta, mostrando o fluxo dos 5 agentes. Zoom 125 %, tela cheia no navegador.

> *(silêncio ou música de fundo leve — sem narração)*

---

#### 3b — Nova União no IBM watsonx Orchestrate — chamadas ao vivo (0:50–1:25, 35 s)

**O que aparece na tela:** tela do Streamlit — região `nova_uniao` selecionada. Clicar em **▶ Executar Conselho**. Mostrar os 5 cards dos agentes surgindo com scores e confiança. Exibir o alerta `👤 Escalar a Humano` com consolidado 30. Expandir **⚡ Divergências identificadas (1)** — mostrar D1: social=78 vs. orçamento=0, diferença de 78.

> *"Nova União — impacto social altíssimo: 82 % da população sem internet, vulnerabilidade máxima. Mas a infraestrutura é zero: backbone a 98 km, sem fibra, orçamento inviável. Três gatilhos de segurança disparam ao mesmo tempo — o Guardião escala para análise humana. Não decide sozinho. Explica por quê."*

---

#### 3c — Central — piloto com divergência (1:25–1:45, 20 s)

**O que aparece na tela:** trocar para `central`. Executar Conselho. Mostrar `🔬 Realizar Piloto`, consolidado 60. Abrir divergência D1 — orçamento 76 vs. impacto social 30.

> *"Central: ótima infraestrutura, orçamento folgado — mas impacto social baixo. O sistema não aprova direto. Identifica a divergência e recomenda piloto. O lucro sozinho não justifica o investimento sem retorno social."*

---

#### 3d — Simulador: Esperança com parcerias (1:45–2:05, 20 s)

**O que aparece na tela:** trocar para `esperanca`. Mostrar resultado base `aguardar`, consolidado 44. Abrir o Simulador de Parcerias. Ativar parcerias hipotéticas. Mostrar consolidado subindo de 44 para 50 — recomendação muda para `🔬 Realizar Piloto`.

> *"Esperança: recomendação inicial — aguardar. Mas o Simulador de Pontes mostra: se a prefeitura e duas escolas se tornarem clientes âncora, o consolidado sobe para 50 e o piloto se torna viável. Não é uma decisão automática — é uma hipótese para o analista investigar em campo."*

---

#### 3e — Mapa (2:05–2:15, 10 s)

**O que aparece na tela:** mapa interativo com as regiões coloridas por recomendação (verde = piloto, amarelo = aguardar, vermelho = escalar).

> *"O mapa consolida todas as análises — cada cor é uma recomendação explicável."*

---

### Bloco 4 — Como construímos com o IBM Bob (2:15–2:45)

**O que aparece na tela (sequência de trechos de tela — ver lista completa na Seção de Gravação):**

1. **Bob criando a ferramenta do agente** — tela do IDE com o IBM Bob gerando o código de `tool_engenharia.py` ou `scripts/gerar_ferramenta_nuvem.py` a partir de um prompt.
2. **Bob publicando no Orchestrate** — Bob executando `orchestrate tools import` e `orchestrate agents import` no terminal integrado.
3. **Bob diagnosticando modelo indisponível** — janela do Bob mostrando diagnóstico do erro `"O módulo necessário não foi encontrado."` e sugerindo a solução de self-contained tool.
4. **Bob criando o gerador de ferramentas** — Bob escrevendo `scripts/gerar_ferramenta_nuvem.py` a partir da descrição do problema de import em nuvem.
5. **Tela do watsonx Orchestrate** — Agent Builder com os 5 agentes `cc_engenharia`, `cc_mercado`, `cc_social`, `cc_orcamento`, `cc_pontes` listados.

> *"Todo o pipeline foi construído com o IBM Bob. O Bob criou as ferramentas dos agentes, diagnosticou o erro de importação em nuvem — e gerou o gerador automático de versões self-contained. Ele publicou e testou cada agente no IBM watsonx Orchestrate sem sair do IDE."*

---

### Bloco 5 — Impacto e escala (2:45–3:00)

**O que aparece na tela:** slide ou tela do Streamlit com dados dos agentes; pode voltar para o mapa ou mostrar o botão de download do relatório JSON.

> *"Com dados públicos reais — IBGE, Anatel, INEP, CNES — essa lógica escala para qualquer região do Brasil. Decisões explicáveis. Auditáveis. Com voz de quem mais precisa de conexão."*

---

---

## Seção B — Narração em Inglês

### Block 1 — Problem (0:00–0:25)

> *"When a telecom operator decides where to expand internet access, the criteria is usually just one: profit. The result: schools without connectivity, health clinics without telemedicine, and entire communities left offline — exactly the ones who need it most. The problem isn't a lack of data. It's a lack of a process that brings other perspectives to the table."*

---

### Block 2 — Solution (0:25–0:45)

> *"Conecta Conselho puts five AI agents in IBM watsonx Orchestrate — each one defends a different point of view: Market, Social Impact, Engineering, Budget, and Bridges. The Guardian consolidates with auditable, transparent rules. A human decides — the system explains why."*

---

### Block 3 — Demo (0:45–2:15)

> *"Watch it work."*

#### 3a — 'How it works' page (0:45–0:50)

> *(silence or background music)*

#### 3b — Nova União on IBM watsonx Orchestrate — live calls (0:50–1:25)

> *"Nova União — extremely high social impact: 82% of the population without internet, maximum vulnerability. But infrastructure is near zero: backbone 98 km away, no fiber, financially unviable. Three safety triggers fire simultaneously — the Guardian escalates to a human. It doesn't decide alone. It explains why."*

#### 3c — Central — pilot with divergence (1:25–1:45)

> *"Central: excellent infrastructure, budget to spare — but low social impact. The system doesn't approve immediately. It flags the divergence and recommends a pilot. Profit alone doesn't justify the investment without social return."*

#### 3d — Simulator: Esperança with partnerships (1:45–2:05)

> *"Esperança: initial recommendation — wait. But the Bridges Simulator shows: if the city hall and two schools become anchor clients, the consolidated score rises from 44 to 50 and a pilot becomes viable. Not an automatic decision — a hypothesis for the analyst to investigate in the field."*

#### 3e — Map (2:05–2:15)

> *"The map consolidates all analyses — each color is an explainable recommendation."*

---

### Block 4 — Built with IBM Bob (2:15–2:45)

> *"The entire pipeline was built with IBM Bob. Bob created the agent tools, diagnosed the cloud import error — and generated the automatic self-contained tool generator. It published and tested each agent in IBM watsonx Orchestrate without leaving the IDE."*

---

### Block 5 — Impact and scale (2:45–3:00)

> *"With real public data — IBGE, Anatel, INEP, CNES — this logic scales to any region in Brazil. Explainable decisions. Auditable. With a voice for those who need connectivity most."*

---

---

## Lista de Trechos de Tela — Quem Grava o Quê

> Cada gravadora salva o arquivo como `clip_XX_nome.mp4` e envia para a pasta compartilhada do grupo antes da edição.

| # | Clip | Quem grava | O que mostrar | Duração sugerida |
|---|---|---|---|---|
| 01 | `clip_01_problema` | Thaly | Imagem/print de região sem conectividade + título do problema | 25 s |
| 02 | `clip_02_diagrama` | Ana | Diagrama dos 5 agentes (print do CONTEXTO_PROJETO.md ou Streamlit "Como funciona") | 20 s |
| 03 | `clip_03_como_funciona` | Ana | Aba "Como funciona" no Streamlit, zoom 125 % | 5 s |
| 04 | `clip_04_nova_uniao` | Laura | Streamlit — nova_uniao → Executar Conselho → cards → alerta escalar → divergência D1 | 35 s |
| 05 | `clip_05_central` | Gabi | Streamlit — central → Executar Conselho → realizar piloto → divergência D1 | 20 s |
| 06 | `clip_06_esperanca_simulador` | Mi | Streamlit — esperanca → aguardar → Simulador → parcerias → piloto | 20 s |
| 07 | `clip_07_mapa` | Ana | Mapa interativo com regiões coloridas | 10 s |
| 08 | `clip_08_bob_cria_ferramenta` | Laura | IBM Bob no IDE criando tool_engenharia ou gerar_ferramenta_nuvem.py | 8 s |
| 09 | `clip_09_bob_publica` | Laura | IBM Bob executando orchestrate tools import + agents import no terminal | 8 s |
| 10 | `clip_10_bob_diagnostico` | Laura | IBM Bob diagnosticando erro de ModuleNotFoundError e sugerindo self-contained | 7 s |
| 11 | `clip_11_bob_gerador` | Laura | IBM Bob escrevendo scripts/gerar_ferramenta_nuvem.py a partir da descrição do problema | 7 s |
| 12 | `clip_12_orchestrate_agentes` | Laura | Tela do Agent Builder (jp-tok) com cc_engenharia, cc_mercado, cc_social, cc_orcamento, cc_pontes listados | 5 s |
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
- [ ] Nomes dos agentes (`cc_engenharia`, `cc_mercado`, `cc_social`, `cc_orcamento`, `cc_pontes`) legíveis em pelo menos um frame
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

- **Idioma:** decidir entre Português (Seção A) e Inglês (Seção B) como grupo — não misturar nas legendas.
- **Música de fundo:** opcional; se usar, manter volume baixo (~15 % do microfone) e sem direitos autorais (use YouTube Audio Library ou Pixabay Music).
- **Plano B de gravação:** se a nuvem IBM Cloud estiver instável, gravar o Streamlit em modo local (`$env:CC_MODO="local"; streamlit run conecta-conselho/app.py`) — os resultados são idênticos, calculados deterministicamente.
- **Duração real dos agentes na nuvem:** cada chamada ao Executar Conselho pode levar 5–15 s dependendo da latência. Ensaiar antes para ajustar o ritmo da narração.

---

*Roteiro criado em: 2026-11-04 | Branch: `docs/roteiro-video` | Base: `ROTEIRO_DEMO.md`, `CONTEXTO_PROJETO.md`, `RESULTADOS_REGIOES.md`, `GUIA_PUBLICACAO_AGENTES.md`*
