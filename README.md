# Conecta Conselho

Sistema multiagente que apoia decisões de expansão de conectividade em regiões brasileiras fictícias, avaliando viabilidade técnica, financeira, social e de parcerias antes de recomendar uma ação.

> ⚠️ **Todos os dados são FICTÍCIOS e SIMULADOS.** Nenhum indicador representa município, estado ou região real do Brasil.

**🔗 Protótipo público:** https://conecta-conselho.streamlit.app

---

## O problema

Operadoras precisam priorizar onde expandir conectividade, conciliando viabilidade comercial, restrições de infraestrutura, orçamento e benefício social. Uma análise isolada pode favorecer áreas rentáveis e ignorar localidades desassistidas. O Conecta Conselho reúne perspectivas especializadas e testa se instituições âncora — escolas, unidades de saúde e outros equipamentos públicos — poderiam melhorar o cenário de atendimento. O sistema **apoia** a triagem de oportunidades, mas **não autoriza** obras nem substitui análise de campo.

---

## Fluxo

```mermaid
flowchart TD
    U["Usuário (Streamlit)"]
    M["cc_mercado"]
    S["cc_impacto_social"]
    E["cc_engenharia"]
    O["cc_orcamento"]
    P["cc_pontes"]
    C["consolidar_pareceres (Python)"]
    D1["✅ Investir agora"]
    D2["🔬 Realizar piloto"]
    D3["⏳ Aguardar"]
    D4["⚠️ Análise incompleta"]

    U -->|"IBM watsonx Orchestrate (paralelo)"| M & S & E & O & P
    M & S & E & O & P -->|"pareceres JSON"| C
    C --> D1 & D2 & D3 & D4
```

Os 5 agentes são chamados em paralelo via `ThreadPoolExecutor`. A consolidação é feita localmente em Python por `consolidar_pareceres` (`tools/tool_guardiao.py`) — nunca pelo LLM.

---

## Agentes

| Agente | Nome no workspace | Pergunta que responde | Tool Python | YAML |
|---|---|---|---|---|
| Mercado | `cc_mercado` | Vale a pena financeiramente? | `tools/tool_mercado.py` | `agents/agente_mercado.yaml` |
| Impacto Social | `cc_impacto_social` | Quem ganha com a conexão? | `tools/tool_social.py` | `agents/agente_social.yaml` |
| Engenharia | `cc_engenharia` | Dá para construir? | `tools/tool_engenharia.py` | `agents/agente_engenharia.yaml` |
| Orçamento | `cc_orcamento` | Cabe no limite de custo e prazo? | `tools/tool_orcamento.py` | `agents/agente_orcamento.yaml` |
| Pontes | `cc_pontes` | Dá para tornar a região viável? | `tools/tool_pontes.py` | `agents/agente_pontes.yaml` |

---

## Páginas do app

As mesmas três telas existem no front React (oficial) e na interface Streamlit (legado).

| Página | Descrição |
|---|---|
| **📖 Como funciona** | Página inicial interativa — apresenta os agentes, sliders para brincar com o Guardião ao vivo e legenda das recomendações |
| **🔍 Análise de Região** | Executa os 5 agentes (IBM ou local), exibe pareceres, recomendação, alerta de atenção prioritária, motivos e caminhos, ranking da sessão e download do relatório JSON. Inclui o **mapa interativo** colorido pela recomendação do Guardião (verde = piloto, azul = investir, amarelo = aguardar, borda vermelha = atenção prioritária) — a pessoa escolhe a região clicando no mapa. Também possui abas de comparação lado a lado e histórico/ranking |
| **🧪 Simulador de cenários** | "E se…?" — simula impacto de parcerias, teto de investimento e distância do backbone; prova que Esperança vai de 44 (Aguardar) → 50 (Piloto) com parcerias. O **mapa interativo** também está disponível aqui para selecionar a região de simulação |

---

## Estrutura de pastas

```
inteli_girls/
├── agents/                    # YAMLs dos agentes ADK
├── tools/                     # Ferramentas Python dos agentes (tool_<nome>.py)
├── scripts/                   # Scripts de publicação e teste na nuvem
├── api/                       # Backend FastAPI usado pelo front-end
├── frontend/                  # Interface web atual (React + Vite + IBM Carbon)
├── conecta-conselho/
│   ├── app.py                 # Interface Streamlit (legado; roteador st.navigation)
│   ├── integracao.py          # Camada multi-fonte (local / nuvem)
│   ├── cliente_nuvem.py       # Conexão IBM watsonx Orchestrate
│   ├── simulador.py           # Motor de cenários determinístico
│   ├── paginas/               # Uma página por arquivo (como_funciona, analise, simulador) + mapa_seletor (componente do mapa)
│   ├── data/                  # regioes.json e regioes.csv (dados simulados)
│   ├── models/                # Modelos Pydantic (regiao.py)
│   ├── tools/                 # consultar_regiao.py (consultas compartilhadas)
│   ├── tests/                 # Testes automatizados (mais de mil testes)
│   └── docs/                  # Documentação do projeto
├── requirements.txt
└── pytest.ini
```

---

## Como rodar localmente (Windows / PowerShell)

> **Pré-requisito:** Python 3.12.x — verifique antes de começar:
> ```powershell
> python --version   # precisa exibir Python 3.12.x
> ```

> **PowerShell — política de execução:** em PCs novos ou corporativos, o PowerShell pode bloquear scripts `.ps1`. Se o comando de ativação falhar, rode primeiro:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

```powershell
git clone --branch main https://github.com/LauraRodrigues31/inteli_girls.git
cd inteli_girls

python -m venv venv
venv\Scripts\Activate.ps1

pip install -r requirements.txt
python -m pytest -q
```

A suíte completa tem **mais de 1 000 testes automatizados** e todos devem passar.

### Interface web (React + FastAPI)

A interface atual é um front-end **React** (pasta `frontend/`) que conversa com um backend **FastAPI** (pasta `api/`). São dois processos, então abra **dois terminais**.

> **Pré-requisitos:** Python 3.12 (já instalado nos passos acima) e **Node.js 18 ou superior** (`node --version`).

**Terminal 1 — backend** (na raiz do projeto, com o venv ativo):

```powershell
venv\Scripts\Activate.ps1
uvicorn api.main:app --reload --port 8000
```

A API fica em http://localhost:8000 (documentação interativa em http://localhost:8000/docs).

**Terminal 2 — front-end:**

```powershell
cd frontend
npm install                # só na primeira vez
copy .env.example .env     # só na primeira vez
npm run dev
```

Abra **http://localhost:5173**. O front só carrega as regiões se o backend (terminal 1) estiver rodando.

Mais detalhes (estrutura, páginas, endpoints, build): [frontend/README.md](frontend/README.md).

**Modo local × nuvem:** o padrão é o modo **local** (cálculos determinísticos, sem nuvem e **sem credenciais**). Na tela *Análise de Região*, a opção "IBM watsonx Orchestrate" usa os agentes publicados na nuvem e exige `WXO_URL`, `WXO_API_KEY` e os `CC_AGENT_ID_*` no arquivo `.env` da raiz (arquivo não versionado; peça os valores a quem publica os agentes).

### Interface Streamlit (legado)

> **Streamlit (legado):** a interface anterior continua no repositório em `conecta-conselho/app.py`, mas **não é mais a interface oficial**.

```powershell
# Com o venv ativo:
python -m streamlit run conecta-conselho/app.py
```

> Rodar fora do venv causa erro de módulo do ADK.

Fonte dos pareceres (barra lateral):

- **IBM watsonx Orchestrate**: vira o padrão quando `WXO_URL`, `WXO_API_KEY` e os 5 `CC_AGENT_ID_*` estão definidos. Resultados da nuvem ficam em cache por 6 h por região; o botão **🔄 Consultar a IBM novamente** ignora o cache. Análises incompletas nunca ficam em cache.
- **Local**: cálculos determinísticos sem nuvem. É o padrão quando faltam credenciais ou IDs, e o plano B se a nuvem falhar (botão **🖥️ Analisar no modo Local**).

As variáveis são lidas primeiro do ambiente do processo (`os.environ`) e depois do `.env` na raiz.

#### Cartografia fictícia

O mapa da Análise de Região e do Simulador lê `conecta-conselho/data/territorio_ficticio.geojson`.
As feições são organizadas por `properties.camada`, incluindo regiões, litoral, rios,
vias, áreas protegidas, relevo, núcleos urbanos e fibra. Para regenerar o arquivo
a partir da malha de referência, na raiz do projeto execute:

```powershell
python scripts/gerar_geografia_ficticia.py
```

O gerador usa apenas a biblioteca padrão do Python. A semente é fixa, e cada
trecho compartilhado é detalhado uma vez e reutilizado pelas regiões vizinhas.
O arquivo GeoJSON usa uma origem angular fictícia em `(0, 0)`, codificando a
malha local como `[x / 1000, -y / 1000]`. O componente converte esses valores
de volta para o plano de desenho. Por isso, a carta tem orientação norte e
zoom, mas não usa escala em quilômetros. As distâncias e os indicadores
exibidos são os da base simulada. Todas as camadas são locais.

### Deploy do site React no Render

O arquivo [`render.yaml`](render.yaml) define um único serviço: a API FastAPI também serve o front compilado (`frontend/dist`). No Render, use *New › Blueprint*, escolha este repositório e a branch desejada. O site sobe em modo local; para o modo nuvem, cadastre `WXO_URL`, `WXO_API_KEY` e os 5 `CC_AGENT_ID_*` em *Environment* (dependências de produção em [`requirements-deploy.txt`](requirements-deploy.txt)).

### Deploy no Streamlit Cloud

1. Em *Create app*, aponte para este repositório, branch `main` e arquivo `conecta-conselho/app.py`.
2. Em *Advanced settings*, escolha **Python 3.12**.
3. Em *Secrets*, cole as variáveis no nível raiz do TOML (o Streamlit as expõe como variáveis de ambiente):

```toml
WXO_URL = "https://..."
WXO_API_KEY = "..."
CC_AGENT_ID_MERCADO = "..."
CC_AGENT_ID_SOCIAL = "..."
CC_AGENT_ID_ENGENHARIA = "..."
CC_AGENT_ID_ORCAMENTO = "..."
CC_AGENT_ID_PONTES = "..."
```

Sem os Secrets, o app sobe normalmente no modo Local.

---

## Como as decisões são calculadas

Os scores vêm de **funções Python determinísticas**, nunca do LLM. O Guardião calcula a média ponderada dos cinco pareceres:

| Agente | Peso |
|---|---|
| Engenharia | 25% |
| Orçamento | 25% |
| Mercado | 20% |
| Impacto Social | 20% |
| Pontes | 10% |

Critérios de recomendação:

| Recomendação | Critério |
|---|---|
| **Investir agora** | `score_consolidado ≥ 70` **E** `orcamento ≥ 60` **E** `engenharia ≥ 60` |
| **Realizar piloto** | `score_consolidado ≥ 50` e não atende critérios acima |
| **Aguardar** | `30 ≤ score_consolidado < 50` |
| **⚠️ Análise incompleta** | Algum agente retornou erro, confiança baixa, `score < 20` em orçamento ou engenharia, ou `score_consolidado < 30` |

O **Alerta de Atenção Prioritária** é acionado quando os pontos críticos indicam risco elevado mesmo dentro de uma recomendação válida (ex.: Nova União — aguardar com alerta).

> ⚠️ Os pesos e limiares acima são **hipóteses do MVP** para fins de demonstração. Não representam metodologia real de decisão de investimento.

Resultados por região: [RESULTADOS_REGIOES.md](conecta-conselho/docs/RESULTADOS_REGIOES.md)

---

## Capturas de tela

**Como funciona** — página inicial com a equipe e o fluxo interativo dos agentes:
![Como funciona](conecta-conselho/docs/prints/front_como_funciona.png)

**Análise de Região › Indicadores** — mapa das regiões e indicadores por perspectiva:
![Análise — indicadores](conecta-conselho/docs/prints/front_analise_indicadores.png)

**Análise de Região › Conselho (Central)** — recomendação *Realizar piloto*, com os pareceres dos 5 agentes:
![Análise — Central](conecta-conselho/docs/prints/front_analise_conselho_central.png)

**Análise de Região › Conselho (Nova União)** — recomendação *Aguardar* com alerta de **Atenção Prioritária**:
![Análise — Nova União](conecta-conselho/docs/prints/front_analise_conselho_nova_uniao.png)

**Simulador de cenários** — atalho "Esperança + parcerias", comparando cenário base e com parcerias:
![Simulador — Esperança](conecta-conselho/docs/prints/front_simulador_esperanca.png)

> ℹ️ Prints do front-end React em modo local (dados simulados), resolução 1440 px.

### Prints da interface Streamlit (legado)

**Como funciona** — página inicial interativa com os agentes:
![Como funciona](conecta-conselho/docs/prints/print_como_funciona.png)

**Análise de Região** — mapa interativo colorido pela recomendação do Guardião (borda vermelha = atenção prioritária):
![Análise — mapa colorido](conecta-conselho/docs/prints/print_analise_mapa.png)

**Nova União selecionada** — modo IBM watsonx Orchestrate:
![Análise — Nova União IBM](conecta-conselho/docs/prints/print_analise_nova_uniao_ibm.png)

**Central selecionada**:
![Análise — Central](conecta-conselho/docs/prints/print_analise_central.png)

**Comparar regiões** — Central × Nova União lado a lado:
![Comparar regiões](conecta-conselho/docs/prints/print_comparar_central_nova_uniao.png)

**Simulador de cenários** — atalho Esperança com parcerias + mapa:
![Simulador — Esperança](conecta-conselho/docs/prints/print_simulador_esperanca_mapa.png)

> ℹ️ Prints capturados em https://conecta-conselho.streamlit.app · zoom 125% · dados simulados

---

## Publicação na IBM

A publicação no watsonx Orchestrate é feita por uma única pessoa do grupo. Veja [conecta-conselho/docs/GUIA_PUBLICACAO_AGENTES.md](conecta-conselho/docs/GUIA_PUBLICACAO_AGENTES.md).

---

## Limitações

- Todos os dados são simulados e fictícios; nenhum indicador representa localidade real.
- O sistema **apoia a triagem** de oportunidades — não autoriza investimentos, obras ou contratos.
- Não substitui análise de campo, regulação ou negociação comercial.

---

## Equipe

Laura Rodrigues · Ana Beggiato · Milena Castro · Gabriela Silva · Thalyta Viana
Trilha 3 · Telecomunicações inteligentes com **Fundação Telefônica**  
AI Experiential Learning Lab · **IBM SkillsBuild**
