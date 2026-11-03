# Resultados das Regiões — Conecta Conselho

> ⚠️ **AVISO: TODOS OS DADOS SÃO SIMULADOS E FICTÍCIOS.**
> Os scores abaixo foram gerados a partir de `conecta-conselho/data/regioes.json` (base simulada) usando
> as fórmulas determinísticas documentadas em `PADRAO_DESENVOLVIMENTO_AGENTES.md` (Seções 6–10 e 11).
> Não representam indicadores reais de nenhuma região brasileira.
> **Finalidade:** gabarito para o Agente Guardião, para o Streamlit e para conferência pós-publicação na nuvem.

---

## Tabela 1 — Score e Confiança por Agente e Região

Todos os campos da base estão presentes e com valores válidos → confiança **alta** em todos os casos.

| Região | Score Mercado | Conf. | Score Social | Conf. | Score Engenharia | Conf. | Score Orçamento | Conf. | Score Pontes | Conf. |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Aurora | **52** | alta | **38** | alta | **74** | alta | **78** | alta | **64** | alta |
| Horizonte | **50** | alta | **76** | alta | **49** | alta | **60** | alta | **43** | alta |
| Esperança | **63** | alta | **66** | alta | **34** | alta | **20** | alta | **43** | alta |
| Central | **37** | alta | **30** | alta | **86** | alta | **76** | alta | **66** | alta |
| Vale Verde | **56** | alta | **59** | alta | **58** | alta | **58** | alta | **80** | alta |
| Nova União | **50** | alta | **78** | alta | **11** | alta | **0** | alta | **21** | alta |

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
- `investir_agora`: consolidado ≥ 70 **E** orçamento ≥ 60 **E** engenharia ≥ 60
- `realizar_piloto`: consolidado ≥ 50 e não atende `investir_agora`
- `aguardar`: 30 ≤ consolidado < 50
- `escalar`: consolidado < 30

Regras de divergência identificadas pelo Guardião:
1. **D1** — `|social − orçamento| > 30`: alto impacto social vs. baixa viabilidade financeira
2. **D2** — `engenharia < 40` e `mercado > 60`: boa demanda mas viabilidade técnica baixa
3. **D3** — `pontes > 70` e `orçamento < 40`: parcerias podem viabilizar o que o orçamento não consegue sozinho

| Região | Consolidado | Recomendação | Divergências |
|---|:---:|---|---|
| Aurora | **62** | `realizar_piloto` | Nenhuma (social=38, orçamento=78: diff=40 → **D1 não dispara** pois é orçamento − social = +40, não social alto vs. orçamento baixo; eng=74 ≥ 40; pontes=64 < 70) |
| Horizonte | **57** | `realizar_piloto` | **D1**: social=76, orçamento=60, diff=16 — não dispara. **Nota:** diff=16 < 30, sem divergência formal. Nenhuma D1/D2/D3. |
| Esperança | **44** | `aguardar` | **D2**: engenharia=34 < 40 e mercado=63 > 60 (boa demanda, viabilidade técnica baixa). **D1**: social=66, orçamento=20, diff=46 > 30 (alto impacto social mas viabilidade financeira baixa). |
| Central | **60** | `realizar_piloto` | Nenhuma (social=30, orçamento=76: social < orçamento, diff=46 mas é social baixo; eng=86 ≥ 40; pontes=66 < 70) |
| Vale Verde | **60** | `realizar_piloto` | **D3**: pontes=80 > 70 e orçamento=58 — orçamento ≥ 40, D3 não dispara (orçamento não < 40). Nenhuma divergência formal. |
| Nova União | **30** | `aguardar` ← regras atuais | **D1**: social=78, orçamento=0, diff=78 > 30 (alto impacto social, viabilidade financeira nula). **D2**: engenharia=11 < 40 e mercado=50 — mercado ≤ 60, D2 não dispara. |

---

> **Nota 1 — Nova União e a regra em aprovação:**
> Pelos critérios atuais (Seção 11), Nova União tem consolidado = 30 e cai em `aguardar`
> (30 ≤ consolidado < 50). Entretanto, o critério de conclusão 16.2 afirma que
> *"Nova União recebe `escalar`"*, reconhecendo que o perfil da região (orçamento=0, engenharia=11)
> é insuficiente para qualquer triagem positiva.
>
> **Regra extra em aprovação pelo grupo:**
> _Escalar também quando: consolidado < 30, OU engenharia < 20, OU orçamento < 20,
> OU qualquer parecer retornou `erro != null` ou `confianca == "baixa"`._
>
> Com essa regra, Nova União (engenharia=11 < 20, orçamento=0 < 20) receberia `escalar`.
> O teste `test_nova_uniao_recomendacao_escalar` (Seção 11) e o critério 16.2 já pressupõem
> essa regra aprovada.

> **Nota 2 — Nenhuma região atinge `investir_agora` com a base atual:**
> O critério exige consolidado ≥ 70 **E** orçamento ≥ 60 **E** engenharia ≥ 60.
> A região com melhor consolidado é Aurora (62) e Central/Vale Verde (60) — todas abaixo de 70.

---

*Gerado em: 2026-11-03 | Commit: `4cd4e92` | Branch: `docs/roteiro-demo`*
*Script de cálculo: `%TEMP%\calcular_scores_cc2.py` (não commitado) | Fórmulas: PADRAO_DESENVOLVIMENTO_AGENTES.md Seções 6–11*
