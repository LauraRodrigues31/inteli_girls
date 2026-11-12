# data/README.md — Conecta Conselho

> ⚠️ **TODOS OS DADOS NESTE DIRETÓRIO SÃO FICTÍCIOS E SIMULADOS.**
> Não representam indicadores reais de nenhum município, estado ou região do Brasil.
> Criados exclusivamente para desenvolvimento e teste do sistema Conecta Conselho.

---

## Visão Geral

Este diretório contém a base de dados simulada do **Conecta Conselho**, um sistema multiagente para apoio a decisões de expansão de conectividade em regiões brasileiras fictícias.

### Arquivos

| Arquivo | Descrição |
|---|---|
| `regioes.json` | **Fonte única da verdade.** Dados completos de todas as 6 regiões, organizados hierarquicamente por perspectiva. |
| `regioes.csv` | Versão tabular gerada automaticamente a partir do JSON. Use para exploração em planilhas e análises tabulares. |
| `gerar_csv.py` | Script para regenerar o CSV a partir do JSON. Execute sempre que o JSON for alterado. |
| `README.md` | Este documento. |

---

## Estrutura do JSON

```
regioes.json
├── metadados                    # Versão, aviso, fórmulas e premissas
└── regioes[]                    # Lista de 6 regiões
    ├── id                       # Identificador único (slug)
    ├── nome                     # Nome da região
    ├── descricao_perfil         # Resumo do perfil
    ├── mercado                  # Indicadores de mercado e demanda
    ├── social                   # Indicadores de impacto social
    ├── engenharia               # Indicadores de viabilidade técnica
    ├── financeiro               # Indicadores de orçamento e retorno
    └── parcerias                # Oportunidades de parceria
```

---

## Regiões Simuladas

| ID | Nome | Perfil Principal |
|---|---|---|
| `aurora` | Região Aurora | Alto potencial econômico e boa infraestrutura |
| `horizonte` | Região Horizonte | Grande impacto social, renda mais baixa |
| `esperanca` | Região Esperança | Alta demanda, custos elevados por topografia |
| `central` | Região Central | Infraestrutura sólida, menor custo de expansão |
| `vale_verde` | Região Vale Verde | Oportunidades estratégicas de parcerias |
| `nova_uniao` | Região Nova União | Baixa viabilidade técnica e financeira |

---

## Fórmulas e Premissas

| Cálculo | Fórmula |
|---|---|
| Receita mensal | `clientes_potenciais × (taxa_adesao_pct ÷ 100) × ticket_medio_mensal` |
| Payback (meses) | `capex ÷ (receita_mensal − opex_mensal)`, apenas quando `receita > opex` |
| Domicílios sem internet | `domicilios_total × (1 − percentual_conectados ÷ 100)` |
| Clientes potenciais | Equivalente aos domicílios sem internet |
| Pessoas beneficiadas | `domicilios_sem_internet × 3,2 moradores/domicílio` |
| Consistência demográfica | `populacao_estimada ≥ domicilios_total × 3` |

---

## Como Regenerar o CSV

```bash
# A partir da raiz do projeto
python conecta-conselho/data/gerar_csv.py

# Ou dentro da pasta data/
python gerar_csv.py
```

O CSV contém as mesmas informações do JSON em formato tabular. Listas (ex: `tecnologias_viaveis`)
são representadas como strings separadas por ` | `. **Nunca edite o CSV manualmente** — toda
manutenção deve ser feita no JSON e o CSV regenerado.

---

## Convenções de Dados

- **Unidade monetária:** Reais (BRL), valores numéricos sem símbolos de moeda.
- **Percentuais:** Escala **0 a 100** (nunca 0 a 1).
- **Booleanos:** `true` / `false`.
- **Índices:** Escala 0 a 100 (documentado no `metadados.convencoes`).
- **Listas:** Arrays de strings.
- **Payback inviável:** `payback_meses: null` quando `receita_mensal ≤ opex_mensal`.

---

## Consumo pelos Agentes Especialistas

Cada agente deve usar o módulo `tools/consultar_regiao.py`. As funções disponíveis são:

```python
from tools.consultar_regiao import (
    listar_regioes,          # Agente Guardião: lista todas as regiões
    consultar_regiao,        # Todos os agentes: dados completos
    consultar_mercado,       # Agente Mercado
    consultar_social,        # Agente Impacto Social
    consultar_engenharia,    # Agente Engenharia
    consultar_financeiro,    # Agente Orçamento
    consultar_parcerias,     # Agente Pontes
)
```

Para integração futura com IBM watsonx Orchestrate ADK, cada função deverá ser
decorada com `@tool` conforme as convenções do ADK 2.19.1. **Não importar ou publicar
ferramentas automaticamente nesta etapa.**
