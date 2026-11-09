# Conecta Conselho — Frontend React

Interface web do sistema multiagente **Conecta Conselho**, construída com:

- **React 18 + TypeScript 5 + Vite**
- **IBM Carbon Design System v11** (`@carbon/react`)
- **IBM Plex Sans** (tipografia oficial IBM)
- **recharts** — radar e gráfico comparativo
- **react-leaflet** — mapa interativo das regiões
- **FastAPI** — backend Python que reutiliza as ferramentas existentes

> ⚠️ Todos os dados são **simulados e fictícios**.

---

## Pré-requisitos

- Node.js ≥ 18
- Python 3.12 (mesmo ambiente do projeto)

---

## Como rodar

### 1. Backend (FastAPI)

```powershell
# Ative o venv existente do projeto
.venv\Scripts\Activate.ps1

# Instale as dependências da API (já estão no requirements.txt raiz,
# mas se precisar instalar separado:)
pip install fastapi "uvicorn[standard]"

# Suba o servidor (a partir da raiz do projeto)
uvicorn api.main:app --reload --port 8000
```

A API ficará disponível em: http://localhost:8000  
Docs interativas: http://localhost:8000/docs

### 2. Frontend (React)

```powershell
cd frontend

# Instale as dependências
npm install

# Copie o arquivo de ambiente
copy .env.example .env

# Suba o servidor de desenvolvimento
npm run dev
```

O app abrirá em: **http://localhost:5173**

---

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | URL base do backend FastAPI |

Copie `.env.example` para `.env` e ajuste se necessário.

---

## Estrutura do frontend

```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
└── src/
    ├── main.tsx              # Entrypoint
    ├── App.tsx               # Roteador + providers
    ├── api/
    │   └── client.ts         # Axios: listarRegioes, executarAnalise, simularCenario
    ├── types/
    │   └── index.ts          # Tipos TypeScript (Region, GuardianResult, etc.)
    ├── context/
    │   └── AppContext.tsx     # Estado global (histórico, região, fonte)
    ├── pages/
    │   ├── ComoFunciona.tsx  # Landing page — fluxo, agentes, critérios
    │   ├── Analise.tsx       # Análise de região — indicadores + Conselho + ranking
    │   └── Simulador.tsx     # What-if com parcerias
    ├── components/
    │   ├── layout/           # AppHeader, SimulatedDataBanner
    │   ├── analysis/         # AgentCard, GuardianResult, ScoreProgressBar, RadarChart…
    │   ├── indicators/       # IndicatorTabs, IndicatorTable
    │   ├── map/              # RegionMap (react-leaflet, choropleth)
    │   ├── simulator/        # ScenarioInputs, ScenarioComparison
    │   └── common/           # EmptyState, LoadingSkeleton
    └── styles/
        └── global.css        # Variáveis IBM, overrides Carbon, Leaflet tooltip
```

---

## Páginas

| Rota | Página | Descrição |
|---|---|---|
| `/` | Como Funciona | Landing com hero IBM dark, 6 tiles de agentes, fluxo SVG e critérios |
| `/analise` | Análise de Região | Sidebar + mapa + 5 abas de indicadores + resultado do Guardião |
| `/simulador` | Simulador de Cenários | Parâmetros de parceria + comparação base × parcerias |

---

## Build para produção

```powershell
cd frontend
npm run build
# Saída em frontend/dist/
```

---

## Backend — endpoints

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/regioes` | Lista todas as regiões |
| `GET` | `/regioes/{id}` | Dados completos de uma região |
| `POST` | `/analise/{id}` | Executa o Conselho (`{"fonte": "local"\|"nuvem"}`) |
| `GET` | `/relatorio/{id}` | Baixa o último relatório JSON da região |
| `GET` | `/docs` | Swagger UI interativo |
