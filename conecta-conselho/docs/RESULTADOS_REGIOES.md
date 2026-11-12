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
- `escalar`: consolidado < 30 *OU* engenharia < 20 *OU* orçamento < 20 *OU* algum parecer com erro ou confiança baixa (regra adotada pelo grupo — ver Nota 1) — **avaliada antes das demais**
- `investir_agora`: consolidado ≥ 70 **E** orçamento ≥ 60 **E** engenharia ≥ 60
- `realizar_piloto`: consolidado ≥ 50 e não atende `investir_agora`
- `aguardar`: 30 ≤ consolidado < 50

Regras de divergência identificadas pelo Guardião (`_identificar_divergencias` em `tools/tool_guardiao.py`):
1. **D1** — `|social − orçamento| > 30`: divergência nos **dois sentidos** — tanto orçamento alto com social baixo quanto social alto com orçamento baixo
2. **D2** — `engenharia < 40` e `mercado > 60`: boa demanda mas viabilidade técnica baixa
3. **D3** — `pontes > 70` e `orçamento < 40`: parcerias podem viabilizar o que o orçamento não consegue sozinho

| Região | Consolidado | Recomendação | Divergências |
|---|:---:|---|---|
| Aurora | **62** | `realizar_piloto` | **D1**: \|social 38 − orçamento 78\| = 40 > 30 → alto orçamento contrastado com baixo impacto social |
| Horizonte | **57** | `realizar_piloto` | Nenhuma (\|social 76 − orçamento 60\| = 16 < 30; eng=49 ≥ 40; pontes=43 < 70) |
| Esperança | **44** | `aguardar` | **D1**: \|social 66 − orçamento 20\| = 46 > 30 (alto impacto social, baixa viabilidade financeira). **D2**: eng=34 < 40 e mercado=63 > 60 (boa demanda, viabilidade técnica insuficiente) |
| Central | **60** | `realizar_piloto` | **D1**: \|social 30 − orçamento 76\| = 46 > 30 → alto orçamento contrastado com baixo impacto social |
| Vale Verde | **60** | `realizar_piloto` | Nenhuma (\|social 59 − orçamento 58\| = 1 < 30; pontes=80 mas orçamento=58 ≥ 40) |
| Nova União | **30** | `escalar` | **D1**: \|social 78 − orçamento 0\| = 78 > 30 (alto impacto social, viabilidade financeira nula). Escalonamento por: orçamento=0 < 20, engenharia=11 < 20 e confiança do Orçamento = baixa |

---

> **Nota 1 — Nova União: recomendação `escalar`**
> Consolidado = 30, que pelos critérios básicos cairia em `aguardar` (30 ≤ consolidado < 50).
> A **regra extra adotada pelo grupo** (implementada em `_determinar_recomendacao` no `tools/tool_guardiao.py`)
> força `escalar` quando: orçamento < 20 **OU** engenharia < 20 **OU** qualquer parecer com
> `erro != null` ou `confianca == "baixa"`.
>
> Nova União aciona três gatilhos simultâneos:
> - orçamento = 0 < 20
> - engenharia = 11 < 20
> - confiança do Orçamento = `baixa` (margem mensal negativa)
>
> O teste `test_nova_uniao_recomendacao_escalar` e a saída real do Guardião confirmam `escalar`.

> **Nota 2 — Nenhuma região atinge `investir_agora` com a base atual:**
> O critério exige consolidado ≥ 70 **E** orçamento ≥ 60 **E** engenharia ≥ 60.
> A região com melhor consolidado é Aurora (62) e Central/Vale Verde (60) — todas abaixo de 70.

---

*Gerado em: 2026-11-03 | Commit: `1010f96` | Branch: `docs/roteiro-demo`*
*Fonte: saída real de `tools/tool_guardiao.py` (`consolidar_pareceres`) e tools especializadas | Fórmulas: PADRAO_DESENVOLVIMENTO_AGENTES.md Seções 6–11*
