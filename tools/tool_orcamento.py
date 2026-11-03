"""
Ferramenta: Agente Orçamento — Conecta Conselho
Analisa a viabilidade financeira e orçamentária de expansão de conectividade.

AVISO: Todos os cálculos usam dados SIMULADOS. Não usar para decisões reais.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Garante que conecta-conselho/ seja encontrado independente de onde o script é chamado
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT / "conecta-conselho"))

from ibm_watsonx_orchestrate.agent_builder.tools import tool

from tools.consultar_regiao import consultar_financeiro  # noqa: E402


# ---------------------------------------------------------------------------
# Funções de cálculo determinístico
# ---------------------------------------------------------------------------


def calcular_indicadores_financeiros(dados: dict) -> dict:
    """
    Calcula todos os indicadores financeiros deterministicamente a partir dos
    dados brutos da base. Nenhum valor é estimado pelo LLM.
    """
    capex: float = float(dados["capex_reais"])
    opex: float = float(dados["opex_mensal_reais"])
    orcamento: float = float(dados["orcamento_disponivel_reais"])
    receita: float = float(dados["receita_mensal_reais"])
    payback_meses = dados["payback_meses"]  # pode ser None (null)

    # margem_mensal = receita - opex
    margem_mensal: float = receita - opex

    # deficit_orcamentario = max(0, capex - orcamento)
    deficit_orcamentario: float = max(0.0, capex - orcamento)

    # cobertura_orcamentaria_pct = (orcamento / capex) * 100
    cobertura_orcamentaria_pct: float = (orcamento / capex) * 100 if capex > 0 else 0.0

    # viavel_financeiramente = margem_mensal > 0
    viavel_financeiramente: bool = margem_mensal > 0

    return {
        "capex_reais": int(capex),
        "opex_mensal_reais": int(opex),
        "orcamento_disponivel_reais": int(orcamento),
        "receita_mensal_reais": round(receita, 2),
        "payback_meses": payback_meses,
        "deficit_orcamentario_reais": int(deficit_orcamentario),
        "margem_mensal_reais": round(margem_mensal, 2),
        "cobertura_orcamentaria_pct": round(cobertura_orcamentaria_pct, 2),
        "viavel_financeiramente": viavel_financeiramente,
        # sub-scores serão preenchidos por calcular_score_orcamento
        "score_payback": 0,
        "score_cobertura_orcamento": 0,
        "score_margem": 0,
    }


def calcular_score_orcamento(indicadores: dict) -> dict:
    """
    Calcula os sub-scores e o score final de viabilidade orçamentária (0–100).
    Todos os cálculos são determinísticos em Python.
    """
    payback = indicadores["payback_meses"]
    orcamento = indicadores["orcamento_disponivel_reais"]
    capex = indicadores["capex_reais"]
    margem = indicadores["margem_mensal_reais"]

    # --- score_payback (peso 40%) ---
    if payback is None:
        score_payback = 0
    elif payback <= 12:
        score_payback = 100
    elif payback >= 120:
        score_payback = 0
    else:
        score_payback = min(100, max(0, 100 - ((payback - 12) / 108) * 100))

    # --- score_cobertura_orcamento (peso 35%) ---
    cobertura_pct = (orcamento / capex) * 100 if capex > 0 else 0.0
    if cobertura_pct >= 100:
        score_cobertura = 100
    elif cobertura_pct <= 50:
        score_cobertura = 0
    else:
        score_cobertura = min(100, max(0, (cobertura_pct - 50) / 50 * 100))

    # --- score_margem (peso 25%) ---
    if margem <= 0:
        score_margem = 0
    else:
        score_margem = min(100, max(0, margem / 200_000 * 100))

    # --- score final ---
    score_final = round(0.40 * score_payback + 0.35 * score_cobertura + 0.25 * score_margem)

    indicadores["score_payback"] = round(score_payback)
    indicadores["score_cobertura_orcamento"] = round(score_cobertura)
    indicadores["score_margem"] = round(score_margem)

    return score_final, indicadores


def _determinar_confianca(indicadores: dict) -> str:
    """
    Determina o nível de confiança com base na completude dos dados.
    - alta: todos os campos numéricos presentes e coerentes
    - media: payback nulo mas restante ok
    - baixa: déficit muito alto ou margem muito negativa
    """
    if not indicadores["viavel_financeiramente"]:
        return "baixa"
    if indicadores["payback_meses"] is None:
        return "media"
    return "alta"


def _construir_justificativa(regiao_nome: str, indicadores: dict, score: int) -> str:
    """Constrói justificativa textual determinística a partir dos indicadores."""
    viavel = indicadores["viavel_financeiramente"]
    payback = indicadores["payback_meses"]
    cobertura = indicadores["cobertura_orcamentaria_pct"]
    margem = indicadores["margem_mensal_reais"]
    deficit = indicadores["deficit_orcamentario_reais"]

    partes = [f"{regiao_nome} obteve score orçamentário de {score}/100."]

    if viavel:
        partes.append(
            f"A margem mensal calculada é R$ {margem:,.2f}, indicando operação superavitária."
        )
    else:
        partes.append(
            f"A margem mensal é negativa (R$ {margem:,.2f}), tornando a operação deficitária sem subsídio."
        )

    if payback is not None:
        partes.append(f"Payback estimado em {payback} meses.")
    else:
        partes.append("Payback incalculável: receita não cobre OPEX mensal.")

    if deficit > 0:
        partes.append(
            f"Déficit orçamentário de R$ {deficit:,.0f} (cobertura: {cobertura:.1f}% do CAPEX)."
        )
    else:
        partes.append(
            f"Orçamento cobre 100% do CAPEX (cobertura: {cobertura:.1f}%)."
        )

    return " ".join(partes)


# ---------------------------------------------------------------------------
# Ferramenta principal decorada com @tool
# ---------------------------------------------------------------------------


@tool
def analisar_orcamento(regiao_id: str) -> dict:
    """
    Analisa a viabilidade financeira e orçamentária de expansão de conectividade
    em uma região do sistema Conecta Conselho.

    Calcula indicadores financeiros com fórmulas determinísticas em Python e
    produz um score de viabilidade de 0 a 100. Quanto maior o score, mais
    viável financeiramente o projeto.

    Args:
        regiao_id: Identificador da região (ex: 'central', 'aurora', 'nova_uniao').

    Returns:
        Dicionário com score, indicadores financeiros, justificativa e riscos.
        Campo 'simulado' sempre True. Campo 'erro' não nulo se região inexistente.
    """
    _base_result = {
        "agente": "orcamento",
        "regiao_id": regiao_id,
        "regiao_nome": "",
        "score": 0,
        "confianca": "nao_avaliada",
        "indicadores": {
            "capex_reais": 0,
            "opex_mensal_reais": 0,
            "orcamento_disponivel_reais": 0,
            "receita_mensal_reais": 0.0,
            "payback_meses": None,
            "deficit_orcamentario_reais": 0,
            "margem_mensal_reais": 0.0,
            "cobertura_orcamentaria_pct": 0.0,
            "viavel_financeiramente": False,
            "score_payback": 0,
            "score_cobertura_orcamento": 0,
            "score_margem": 0,
        },
        "justificativa": "",
        "riscos": [],
        "limitacoes": [
            "Valores financeiros baseados em dados simulados. Não usar para decisões reais."
        ],
        "simulado": True,
        "erro": None,
    }

    # Consulta dados financeiros
    resultado = consultar_financeiro(regiao_id)

    # Verifica erro de região não encontrada
    if "erro" in resultado:
        _base_result["erro"] = resultado.get("mensagem", resultado["erro"])
        _base_result["justificativa"] = (
            f"Região '{regiao_id}' não encontrada na base de dados."
        )
        return _base_result

    regiao_nome: str = resultado["nome"]
    dados_fin: dict = resultado["dados"]

    # Calcula indicadores deterministicamente
    indicadores = calcular_indicadores_financeiros(dados_fin)
    score, indicadores = calcular_score_orcamento(indicadores)

    confianca = _determinar_confianca(indicadores)
    justificativa = _construir_justificativa(regiao_nome, indicadores, score)
    riscos: list = dados_fin.get("riscos_financeiros", [])

    _base_result.update(
        {
            "regiao_nome": regiao_nome,
            "score": score,
            "confianca": confianca,
            "indicadores": indicadores,
            "justificativa": justificativa,
            "riscos": riscos,
        }
    )
    return _base_result


# ---------------------------------------------------------------------------
# Helpers para execucao direta (compativel com wrapper @tool)
# ---------------------------------------------------------------------------


def _run_analise(regiao_id: str) -> dict:
    """Chama analisar_orcamento e desempacota o ToolResponse se necessario."""
    result = analisar_orcamento(regiao_id)
    if hasattr(result, "content"):
        return result.content
    return result


if __name__ == "__main__":
    import json

    for rid in ["aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"]:
        r = _run_analise(rid)
        print(
            f"{rid:12s} | score={r['score']:3d} | payback={str(r['indicadores']['payback_meses']):>4s} | "
            f"margem={r['indicadores']['margem_mensal_reais']:>12.2f} | "
            f"viavel={r['indicadores']['viavel_financeiramente']}"
        )
    print()
    print("--- central (detalhado) ---")
    print(json.dumps(_run_analise("central"), indent=2, ensure_ascii=False))
    print()
    print("--- inexistente ---")
    print(json.dumps(_run_analise("inexistente"), indent=2, ensure_ascii=False))
