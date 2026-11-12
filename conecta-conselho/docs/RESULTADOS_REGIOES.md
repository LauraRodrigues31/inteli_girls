# Resultados das Regiões — Conecta Conselho

> ⚠️ **AVISO: TODOS OS DADOS SÃO SIMULADOS E FICTÍCIOS.**
> Os scores abaixo foram gerados a partir de `conecta-conselho/data/regioes.json` (base simulada) usando
> as fórmulas determinísticas documentadas em `PADRAO_DESENVOLVIMENTO_AGENTES.md` (Seções 6–10 e 11).
> Não representam indicadores reais de nenhuma região brasileira.
> **Finalidade:** gabarito para o Agente Guardião, para a interface web e para conferência pós-publicação na nuvem.

---

## Tabela 1 — Score e Confiança por Agente e Região

Scores e confiança extraídos diretamente das tools (`analisar_mercado`, `analisar_impacto_social`, `analisar_engenharia`, `analisar_orcamento`, `analisar_pontes`).
Nova União: `analisar_orcamento` retorna `confiança = baixa` pois a margem mensal é negativa (receita < OPEX) — campo `viavel_financeiramente = False`.

| Região | Score Mercado | Conf. | Score Social | Conf. | Score Engenharia | Conf. | Score Orçamento | Conf. | Score Pontes | Conf. |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Aurora | **52** | alta | **38** | alta | **74** | alta | **78** | alta | **64** | alta |
| Horizonte | **50** | alta | **76** | alta | **49** | alta | **60** | alta | **43** | alta |
| Esperança | **63** | alta | **66** | alta | **34** | alta | **20** | alta | **43** | alta |
| Central | **37** | alta | **30** | alta | **86** | alta | **76** | alta | **66** | alta |
| Vale Verde | **56** | alta | **59** | alta | **58** | alta | **58** | alta | **80** | alta |
| Nova União | **50** | alta | **78** | alta | **11** | alta | **0** | **baixa** | **21** | alta |

### Metodologia dos sub-scores (resumo)

| Agente | Sub-scores principais | Pesos |
|---|---|---|
| Mercado | renda_relativa · crescimento · mercado_potencial · competitividade | 30 / 20 / 30 / 20 % |
| Social | exclusao_digital · infraestrutura_social · vulnerabilidade · alcance | 35 / 30 / 20 / 15 % |
| Engenharia | backbone · cobertura_fibra · prazo · base_viabilidade | 25 / 25 / 20 / 30 % |
| Orçamento | payback · cobertura_orcamento · margem | 40 / 35 / 25 % |
| Pontes | quantidade_parceiros · infraestrutura · economia_potencial · maturidade | 30 / 25 / 25 / 20 % |

> **Detalhe de arredondamento:** sub-scores são mantidos como float; o `round()` é aplicado **somente no score final** de cada agente e no score consolidado. Isso altera em ±1 ponto alguns valores quando comparado a arredondar cada sub-score individualmente (ex.: vale_verde orçamento: 58,43 → 58, não 59).

---

## Tabela 2 — Score Consolidado, Recomendação e Divergências

Fórmula do consolidado: `round(0.20·mercado + 0.20·social + 0.25·engenharia + 0.25·orçamento + 0.10·pontes)`

Critérios de recomendação (Seção 11, PADRÃO):
- `analise_incompleta`: algum parecer com erro, confiança baixa, `orçamento < 20`, `engenharia < 20` ou `score_consolidado < 30` — **avaliada antes das demais**
- `investir_agora`: consolidado ≥ 70 **E** orçamento ≥ 60 **E** engenharia ≥ 60
- `realizar_piloto`: consolidado ≥ 50 e não atende `investir_agora`
- `aguardar`: 30 ≤ consolidado < 50

O **Alerta de Atenção Prioritária** (`atencao_prioritaria: true`) é acionado quando pontos críticos indicam risco elevado dentro de uma recomendação válida. Nova União recebe `aguardar` com `atencao_prioritaria: true`.

Regras de divergência identificadas pelo Guardião (`_identificar_divergencias` em `tools/tool_guardiao.py`):
1. **D1** — `|social − orçamento| > 30`: divergência nos **dois sentidos** — tanto orçamento alto com social baixo quanto social alto com orçamento baixo
2. **D2** — `engenharia < 40` e `mercado > 60`: boa demanda mas viabilidade técnica baixa
3. **D3** — `pontes > 70` e `orçamento < 40`: parcerias podem viabilizar o que o orçamento não consegue sozinho

| Região | Consolidado | Recomendação | Alerta | Divergências |
|---|:---:|---|:---:|---|
| Aurora | **62** | `realizar_piloto` | — | **D1**: \|social 38 − orçamento 78\| = 40 > 30 → alto orçamento contrastado com baixo impacto social |
| Horizonte | **57** | `realizar_piloto` | — | Nenhuma |
| Esperança | **44** | `aguardar` | — | **D1**: \|social 66 − orçamento 20\| = 46 > 30. **D2**: eng=34 < 40 e mercado=63 > 60 |
| Central | **60** | `realizar_piloto` | — | **D1**: \|social 30 − orçamento 76\| = 46 > 30 |
| Vale Verde | **60** | `realizar_piloto` | — | Nenhuma |
| Nova União | **30** | `aguardar` | ⚠️ | **D1**: \|social 78 − orçamento 0\| = 78 > 30; pontos críticos: orçamento 0, engenharia 11, margem negativa |

---

## Motivos e Caminhos por Região

Textos extraídos de `consolidar_pareceres` (`chamar_guardiao(regiao, fonte="local")`).

### Esperança — Aguardar (score 44)

**Motivos:**
- Engenharia (score 34): backbone a 62 km; 8% de cobertura de fibra; prazo de 20 meses.
- Orçamento (score 20): orçamento cobre 57,5% do CAPEX (déficit de R$ 3.700.000); payback de 107 meses.
- Pontes (score 43): 4 parceiros possíveis; maturidade de parcerias baixa.

**Caminhos para viabilizar:**
- Tecnologias alternativas viáveis: Fibra óptica FTTH para área central, Fixed Wireless Access (FWA) para encostas e áreas de difícil acesso, Conexão via satélite LEO para comunidades isoladas.
- Oportunidades de redução de custos via parcerias: Compartilhamento de infraestrutura de postes com distribuidora de energia.
- Infraestrutura compartilhável identificada: pode reduzir CAPEX.
- 4 instituições âncora identificadas com potencial de economia de 28,0% nos custos.
- Implantação em fases: o orçamento cobre 57,5% do CAPEX (déficit de R$ 3.700.000).

### Nova União — Aguardar ⚠️ (score 30, atencao_prioritaria: true)

**Pontos críticos:**
- Orçamento com score 0: margem mensal de R$ -50.002,15; cobertura orçamentária de 28,0%; déficit de R$ 9.000.000.
- Engenharia com score 11: backbone a 98 km; 0% de cobertura de fibra; prazo de implantação de 28 meses.
- Confiança baixa no parecer de Orçamento.

**Motivos:**
- Engenharia (score 11): backbone a 98 km; 0% de cobertura de fibra; prazo de 28 meses.
- Orçamento (score 0): orçamento cobre 28,0% do CAPEX (déficit de R$ 9.000.000); payback indefinido (margem negativa); margem mensal negativa (R$ -50.002,15).
- Pontes (score 21): 3 parceiros possíveis; maturidade de parcerias baixa.

**Caminhos para viabilizar:**
- Tecnologias alternativas viáveis: Conexão via satélite LEO (única opção de curto prazo), Fixed Wireless Access (FWA) com backhaul via satélite, Fibra óptica FTTH apenas a longo prazo, condicionado a expansão de backbone.
- Oportunidades de redução de custos via parcerias: Uso de satélite LEO elimina necessidade de infraestrutura terrestre de backhaul.
- 3 instituições âncora identificadas com potencial de economia de 12,0% nos custos.
- Implantação em fases: o orçamento cobre 28,0% do CAPEX (déficit de R$ 9.000.000).

---

## Cenários Simulados

Resultados de `simular_cenario` (`conecta-conselho/simulador.py`) — recalculado localmente com as mesmas regras dos agentes.

> ⚠️ **Dados simulados.** Os cenários abaixo são hipotéticos e demonstrativos.

| Região | Parâmetro alterado | Score base | Rec. base | Score simulado | Rec. simulada | Alerta |
|---|---|:---:|---|:---:|---|:---:|
| Esperança | *(base — sem alteração)* | 44 | `aguardar` | 44 | `aguardar` | — |
| Esperança | `usar_parcerias=True` | 44 | `aguardar` | **50** | **`realizar_piloto`** | — |
| Esperança | `distancia_backbone_km=20` | 44 | `aguardar` | **46** | `aguardar` | — |
| Esperança | `backbone=20 km + parcerias` | 44 | `aguardar` | **53** | **`realizar_piloto`** | — |
| Esperança | `teto=R$ 8.700.000` (= CAPEX) | 44 | `aguardar` | **51** | **`realizar_piloto`** | — |
| Nova União | `usar_parcerias=True` | 30 | `aguardar` | **30** | `aguardar` | ⚠️ |
| Nova União | `distancia_backbone_km=20` | 30 | `aguardar` | **35** | `aguardar` | ⚠️ |
| Horizonte | `usar_parcerias=True` | 57 | `realizar_piloto` | **60** | `realizar_piloto` | — |

**Interpretação do one-pager:** A Esperança demonstra que uma região em "Aguardar" pode virar "Realizar piloto" quando parcerias reduzem o CAPEX em 28% — de score 44 para 50. Nova União permanece em "Aguardar" com alerta mesmo com parcerias ou melhoria de backbone, pois a margem mensal é negativa e o déficit orçamentário é estrutural.

---

> **Nota — Nova União: recomendação `aguardar` com `atencao_prioritaria: true`**
> Consolidado = 30 (30 ≤ score < 50 → `aguardar`). O sistema aciona o alerta de atenção prioritária
> pelos três gatilhos simultâneos:
> - orçamento = 0 (margem mensal negativa — R$ -50.002,15)
> - engenharia = 11 (backbone a 98 km, 0% de fibra)
> - confiança do Orçamento = baixa

> **Nota — Nenhuma região atinge `investir_agora` com a base atual:**
> O critério exige consolidado ≥ 70 **E** orçamento ≥ 60 **E** engenharia ≥ 60.
> A região com melhor consolidado é Aurora (62) e Central/Vale Verde (60) — todas abaixo de 70.

---

*Atualizado em: 2026-11-05 | Branch: `docs/documentacao-final`*
*Fonte: saída real de `tools/tool_guardiao.py` (`consolidar_pareceres`) e `conecta-conselho/simulador.py` | Fórmulas: PADRAO_DESENVOLVIMENTO_AGENTES.md Seções 6–11*
