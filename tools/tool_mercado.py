"""
Ferramenta do Agente Mercado — Conecta Conselho.

Analisa o potencial econômico e a demanda por conectividade de uma região.
Todos os dados são SIMULADOS e fictícios.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Importa `consultar_mercado` via importlib para evitar colisão entre o
# pacote `tools/` da raiz do workspace e o `tools/` de `conecta-conselho/`.
import importlib.util as _ilu

_CONSULTAR_PATH = (
    Path(__file__).resolve().parent.parent
    / "conecta-conselho"
    / "tools"
    / "consultar_regiao.py"
)
_spec = _ilu.spec_from_file_location("consultar_regiao", _CONSULTAR_PATH)
_mod = _ilu.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]
consultar_mercado = _mod.consultar_mercado

try:
    from ibm_watsonx_orchestrate.agent_builder.tools import tool as _tool_decorator
except ImportError:  # execução local sem o SDK instalado
    def _tool_decorator(fn):  # type: ignore[misc]
        return fn


# ---------------------------------------------------------------------------
# Cálculo determinístico do score — nunca estimado pelo LLM
# ---------------------------------------------------------------------------

def calcular_score_mercado(dados: dict) -> dict:
    """
    Calcula o score de mercado de 0 a 100 pela média ponderada de quatro
    sub-scores.  Todos os cálculos são determinísticos e testáveis.

    Sub-scores (cada um de 0 a 100):
      - score_renda_relativa (peso 30 %):
          Escala linear: renda 800 → 0 ; renda 5 000 → 100
          formula: min(100, max(0, (renda - 800) / (5 000 - 800) * 100))

      - score_crescimento (peso 20 %):
          Escala linear: crescimento 0 % → 0 ; crescimento 5 % → 100
          formula: min(100, max(0, crescimento_pct / 5.0 * 100))

      - score_mercado_potencial (peso 30 %):
          Percentual de domicílios SEM internet (mais potencial não atendido →
          maior score).  O campo percentual_domicilios_conectados já está em
          escala 0-100, então: percentual_sem = 100 - percentual_conectados.

      - score_competitividade (peso 20 %):
          Penaliza concorrentes: 0 → 100 ; 5+ → 0
          formula: min(100, max(0, 100 - (concorrentes / 5) * 100))

    Score final = 0.30 * renda + 0.20 * crescimento + 0.30 * potencial
                  + 0.20 * competitividade   → arredondado para inteiro.
    """
    renda = dados.get("renda_media_mensal_reais", 0)
    crescimento = dados.get("taxa_crescimento_populacional_pct", 0)
    pct_conectados = dados.get("percentual_domicilios_conectados", 0)
    concorrentes = dados.get("numero_concorrentes", 0)

    pct_sem_internet = 100 - pct_conectados

    score_renda = min(100, max(0, (renda - 800) / (5000 - 800) * 100))
    score_crescimento = min(100, max(0, crescimento / 5.0 * 100))
    score_potencial = min(100, max(0, float(pct_sem_internet)))
    score_competitividade = min(100, max(0, 100 - (concorrentes / 5) * 100))

    score_final = (
        0.30 * score_renda
        + 0.20 * score_crescimento
        + 0.30 * score_potencial
        + 0.20 * score_competitividade
    )

    return {
        "score_renda_relativa": round(score_renda),
        "score_crescimento": round(score_crescimento),
        "score_mercado_potencial": round(score_potencial),
        "score_competitividade": round(score_competitividade),
        "score_final": round(score_final),
    }


def _determinar_confianca(dados: dict) -> str:
    """Determina a confiança com base na completude dos dados (regra da Seção 3.3)."""
    campos_obrigatorios = [
        "populacao_estimada",
        "domicilios_total",
        "renda_media_mensal_reais",
        "taxa_crescimento_populacional_pct",
        "percentual_domicilios_conectados",
        "clientes_potenciais",
        "ticket_medio_mensal_reais",
        "numero_concorrentes",
    ]
    presentes = sum(1 for c in campos_obrigatorios if dados.get(c) is not None)
    if presentes == len(campos_obrigatorios):
        return "alta"
    if presentes >= 6:
        return "media"
    return "baixa"


# ---------------------------------------------------------------------------
# Ferramenta principal decorada com @tool
# ---------------------------------------------------------------------------

@_tool_decorator
def analisar_mercado(regiao_id: str) -> dict:
    """
    Analisa o potencial de mercado de uma região do Conecta Conselho.

    Args:
        regiao_id: Identificador da região. Valores válidos:
                   aurora, horizonte, esperanca, central, vale_verde, nova_uniao

    Returns:
        Parecer estruturado com score de 0-100, indicadores calculados e justificativa.
    """
    resultado = consultar_mercado(regiao_id)

    # Região não encontrada ou erro na consulta
    if "erro" in resultado:
        ids_validos = "aurora, horizonte, esperanca, central, vale_verde, nova_uniao"
        return {
            "agente": "mercado",
            "regiao_id": regiao_id,
            "regiao_nome": None,
            "score": 0,
            "confianca": "nao_avaliada",
            "indicadores": {},
            "justificativa": (
                f"Região '{regiao_id}' não encontrada na base de dados. "
                f"IDs válidos: {ids_validos}."
            ),
            "riscos": [],
            "limitacoes": ["Região não encontrada na base simulada."],
            "simulado": True,
            "erro": resultado["erro"],
        }

    dados = resultado["dados"]
    scores = calcular_score_mercado(dados)
    confianca = _determinar_confianca(dados)

    renda = dados.get("renda_media_mensal_reais", 0)
    crescimento = dados.get("taxa_crescimento_populacional_pct", 0)
    clientes = dados.get("clientes_potenciais", 0)
    concorrentes = dados.get("numero_concorrentes", 0)
    ticket = dados.get("ticket_medio_mensal_reais", 0)
    pct_conectados = dados.get("percentual_domicilios_conectados", 0)

    justificativa = (
        f"A {resultado['nome']} apresenta renda média de R$ {renda:,.0f}/mês, "
        f"taxa de crescimento de {crescimento}% a.a. e {clientes:,} clientes "
        f"potenciais (domicílios sem internet). "
        f"Com {concorrentes} concorrente(s) e ticket médio de R$ {ticket}/mês, "
        f"o score final de {scores['score_final']} reflete "
        f"{'alto' if scores['score_final'] >= 70 else 'moderado' if scores['score_final'] >= 45 else 'baixo'} "
        f"potencial de mercado. "
        f"O percentual de domicílios já conectados ({pct_conectados}%) limita o mercado endereçável."
    ).replace(",", ".")

    riscos = []
    if concorrentes >= 3:
        riscos.append(
            f"{concorrentes} concorrentes estabelecidos podem reduzir a taxa de adesão e comprimir margens."
        )
    if renda < 2000:
        riscos.append("Renda média baixa pode dificultar monetização e aumentar inadimplência.")
    if pct_conectados > 70:
        riscos.append("Mercado já amplamente conectado — baixo potencial de novos clientes.")
    if crescimento < 1.0:
        riscos.append("Crescimento populacional estagnado limita expansão futura da base de clientes.")
    if not riscos:
        riscos.append("Risco de saturação do mercado em médio prazo dado o crescimento esperado.")

    return {
        "agente": "mercado",
        "regiao_id": resultado["id"],
        "regiao_nome": resultado["nome"],
        "score": scores["score_final"],
        "confianca": confianca,
        "indicadores": {
            "populacao_estimada": dados.get("populacao_estimada"),
            "domicilios_total": dados.get("domicilios_total"),
            "renda_media_mensal_reais": renda,
            "taxa_crescimento_populacional_pct": crescimento,
            "percentual_domicilios_conectados": pct_conectados,
            "clientes_potenciais": clientes,
            "ticket_medio_mensal_reais": ticket,
            "numero_concorrentes": concorrentes,
            "score_renda_relativa": scores["score_renda_relativa"],
            "score_crescimento": scores["score_crescimento"],
            "score_mercado_potencial": scores["score_mercado_potencial"],
            "score_competitividade": scores["score_competitividade"],
        },
        "justificativa": justificativa,
        "riscos": riscos,
        "limitacoes": [
            "Dado simulado — não reflete condições reais de mercado",
            "Número de concorrentes pode ser impreciso em cenário real",
            "Taxa de adesão projetada é estimativa sem validação de campo",
        ],
        "simulado": True,
        "erro": None,
    }


# ---------------------------------------------------------------------------
# Execução direta para smoke-test rápido
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    def _unpack(r):
        return r.content if hasattr(r, "content") else r

    for rid in ["aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"]:
        r = _unpack(analisar_mercado(rid))
        print(f"{rid:12s} → score={r['score']:3d}  confianca={r['confianca']}")

    print("\n--- Região inexistente ---")
    err = _unpack(analisar_mercado("nao_existe"))
    print(json.dumps(err, ensure_ascii=False, indent=2))
