"""
Testes automatizados para o Agente Orcamento — Conecta Conselho.

Execute com:
    python -m pytest conecta-conselho/tests/ -v

AVISO: Os dados testados sao SIMULADOS e ficticios.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Garante que tools/ na raiz seja encontrado antes de conecta-conselho/tools/
_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT / "tools"))
sys.path.insert(1, str(_ROOT / "conecta-conselho"))

import tool_orcamento as _mod  # noqa: E402


def _call(regiao_id: str) -> dict:
    """Invoca analisar_orcamento e desempacota ToolResponse se necessario."""
    result = _mod.analisar_orcamento(regiao_id)
    if hasattr(result, "content"):
        return result.content
    return result


# ---------------------------------------------------------------------------
# Testes obrigatorios (especificados no enunciado)
# ---------------------------------------------------------------------------


def test_nova_uniao_score_zero_payback():
    """Nova Uniao tem payback_meses nulo → score_payback deve ser 0."""
    r = _call("nova_uniao")
    assert r["indicadores"]["score_payback"] == 0  # payback_meses e null


def test_central_maior_score_que_esperanca():
    """Central (payback 31 meses) deve ter score maior que Esperanca (payback 107 meses)."""
    c = _call("central")
    e = _call("esperanca")
    assert c["score"] > e["score"]


def test_margem_mensal_calculada_corretamente():
    """Margem mensal = receita - opex, verificado contra os indicadores."""
    r = _call("aurora")
    dados = r["indicadores"]
    margem_esperada = dados["receita_mensal_reais"] - dados["opex_mensal_reais"]
    assert abs(dados["margem_mensal_reais"] - margem_esperada) < 1.0


def test_regiao_inexistente():
    """Regiao inexistente deve retornar erro nao nulo e score zero."""
    r = _call("inexistente")
    assert r["erro"] is not None
    assert r["score"] == 0


# ---------------------------------------------------------------------------
# Testes de estrutura de retorno
# ---------------------------------------------------------------------------


def test_campos_obrigatorios_presentes():
    """Resultado deve conter todos os campos do schema obrigatorio."""
    r = _call("central")
    campos = [
        "agente", "regiao_id", "regiao_nome", "score", "confianca",
        "indicadores", "justificativa", "riscos", "limitacoes", "simulado", "erro",
    ]
    for campo in campos:
        assert campo in r, f"Campo ausente: {campo}"


def test_indicadores_obrigatorios_presentes():
    """Sub-dicionario indicadores deve conter todos os campos esperados."""
    r = _call("central")
    ind = r["indicadores"]
    campos = [
        "capex_reais", "opex_mensal_reais", "orcamento_disponivel_reais",
        "receita_mensal_reais", "payback_meses", "deficit_orcamentario_reais",
        "margem_mensal_reais", "cobertura_orcamentaria_pct", "viavel_financeiramente",
        "score_payback", "score_cobertura_orcamento", "score_margem",
    ]
    for campo in campos:
        assert campo in ind, f"Indicador ausente: {campo}"


def test_simulado_sempre_true():
    """Campo simulado deve ser True para qualquer entrada, inclusive invalida."""
    for rid in ["aurora", "central", "inexistente"]:
        r = _call(rid)
        assert r["simulado"] is True, f"simulado deve ser True para '{rid}'"


def test_agente_nome_correto():
    """Campo agente deve ser 'orcamento'."""
    r = _call("central")
    assert r["agente"] == "orcamento"


def test_score_inteiro_0_a_100():
    """Score deve ser inteiro entre 0 e 100 para todas as regioes validas."""
    for rid in ["aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"]:
        r = _call(rid)
        assert isinstance(r["score"], int), f"Score nao inteiro em '{rid}'"
        assert 0 <= r["score"] <= 100, f"Score fora do intervalo em '{rid}': {r['score']}"


def test_limitacoes_contem_aviso_simulado():
    """Campo limitacoes deve conter o aviso obrigatorio sobre dados simulados."""
    aviso_esperado = "Valores financeiros baseados em dados simulados. Nao usar para decisoes reais."
    for rid in ["aurora", "central"]:
        r = _call(rid)
        textos = " ".join(r["limitacoes"])
        # Compara removendo acentos para robustez com diferentes encodings
        import unicodedata
        def remover_acentos(s: str) -> str:
            return "".join(
                c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn"
            )
        assert remover_acentos(aviso_esperado).lower() in remover_acentos(textos).lower(), (
            f"Aviso obrigatorio ausente em limitacoes para '{rid}'"
        )


# ---------------------------------------------------------------------------
# Testes de valores financeiros
# ---------------------------------------------------------------------------


def test_nova_uniao_payback_nulo():
    """Nova Uniao deve ter payback_meses = None (operacao deficitaria)."""
    r = _call("nova_uniao")
    assert r["indicadores"]["payback_meses"] is None


def test_nova_uniao_viavel_false():
    """Nova Uniao: margem negativa → viavel_financeiramente deve ser False."""
    r = _call("nova_uniao")
    assert r["indicadores"]["viavel_financeiramente"] is False
    assert r["indicadores"]["margem_mensal_reais"] < 0


def test_nova_uniao_score_zero():
    """Nova Uniao deve ter score final zero (payback nulo + margem negativa)."""
    r = _call("nova_uniao")
    assert r["score"] == 0


def test_central_viavel_true():
    """Central deve ter viavel_financeiramente = True (margem positiva)."""
    r = _call("central")
    assert r["indicadores"]["viavel_financeiramente"] is True
    assert r["indicadores"]["margem_mensal_reais"] > 0


def test_deficit_orcamentario_central_zero():
    """Central: orcamento > capex → deficit deve ser 0."""
    r = _call("central")
    assert r["indicadores"]["deficit_orcamentario_reais"] == 0


def test_deficit_orcamentario_nova_uniao_positivo():
    """Nova Uniao: capex muito maior que orcamento → deficit > 0."""
    r = _call("nova_uniao")
    assert r["indicadores"]["deficit_orcamentario_reais"] > 0


def test_cobertura_orcamentaria_central():
    """Central: orcamento=3.000.000, capex=1.900.000 → cobertura ~ 157.89%."""
    r = _call("central")
    cobertura = r["indicadores"]["cobertura_orcamentaria_pct"]
    assert abs(cobertura - 157.89) < 0.1


def test_margem_positiva_para_regioes_viaveis():
    """Todas as regioes com viavel=True devem ter margem > 0."""
    for rid in ["aurora", "horizonte", "esperanca", "central", "vale_verde"]:
        r = _call(rid)
        ind = r["indicadores"]
        if ind["viavel_financeiramente"]:
            assert ind["margem_mensal_reais"] > 0, (
                f"Margem nao positiva em '{rid}' mas viavel=True"
            )


# ---------------------------------------------------------------------------
# Testes dos sub-scores
# ---------------------------------------------------------------------------


def test_score_payback_central():
    """Central: payback=31 → score_payback = round(100 - ((31-12)/108)*100) = 82."""
    r = _call("central")
    assert r["indicadores"]["score_payback"] == 82


def test_score_payback_esperanca():
    """Esperanca: payback=107 → score_payback = round(100 - ((107-12)/108)*100) = 12."""
    r = _call("esperanca")
    payback = 107
    esperado = round(100 - ((payback - 12) / 108) * 100)
    assert r["indicadores"]["score_payback"] == esperado


def test_score_cobertura_central_100():
    """Central: cobertura > 100% → score_cobertura_orcamento deve ser 100."""
    r = _call("central")
    assert r["indicadores"]["score_cobertura_orcamento"] == 100


def test_score_cobertura_nova_uniao_zero():
    """Nova Uniao: cobertura muito baixa (28%) → score_cobertura_orcamento deve ser 0."""
    r = _call("nova_uniao")
    # cobertura = 3.500.000 / 12.500.000 * 100 = 28% (< 50%)
    assert r["indicadores"]["score_cobertura_orcamento"] == 0


def test_score_margem_nova_uniao_zero():
    """Nova Uniao: margem < 0 → score_margem deve ser 0."""
    r = _call("nova_uniao")
    assert r["indicadores"]["score_margem"] == 0


def test_sub_scores_sao_inteiros_0_a_100():
    """Todos os sub-scores devem ser inteiros entre 0 e 100."""
    for rid in ["aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"]:
        r = _call(rid)
        ind = r["indicadores"]
        for sub in ["score_payback", "score_cobertura_orcamento", "score_margem"]:
            val = ind[sub]
            assert isinstance(val, int), f"{sub} nao inteiro em '{rid}'"
            assert 0 <= val <= 100, f"{sub} fora do intervalo em '{rid}': {val}"


# ---------------------------------------------------------------------------
# Testes de erros e casos borda
# ---------------------------------------------------------------------------


def test_regiao_inexistente_erro_nao_nulo():
    """Regiao invalida deve ter campo erro preenchido."""
    r = _call("inexistente")
    assert r["erro"] is not None
    assert isinstance(r["erro"], str)
    assert len(r["erro"]) > 0


def test_regiao_inexistente_indicadores_zerados():
    """Regiao invalida deve ter todos os indicadores numericos zerados."""
    r = _call("inexistente")
    ind = r["indicadores"]
    assert ind["capex_reais"] == 0
    assert ind["opex_mensal_reais"] == 0
    assert ind["score_payback"] == 0
    assert ind["score_cobertura_orcamento"] == 0
    assert ind["score_margem"] == 0
    assert ind["viavel_financeiramente"] is False


def test_regiao_id_preservado_no_retorno():
    """O regiao_id de entrada deve ser preservado no retorno."""
    for rid in ["central", "nova_uniao", "inexistente"]:
        r = _call(rid)
        assert r["regiao_id"] == rid


def test_todas_regioes_validas_sem_erro():
    """Todas as 6 regioes validas devem retornar sem erro."""
    for rid in ["aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"]:
        r = _call(rid)
        assert r["erro"] is None, f"Erro inesperado em '{rid}': {r['erro']}"
        assert r["regiao_nome"] != ""


# ---------------------------------------------------------------------------
# Testes de consistencia matematica
# ---------------------------------------------------------------------------


def test_formula_margem_todas_regioes():
    """margem = receita - opex deve ser exato para todas as regioes validas."""
    for rid in ["aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"]:
        r = _call(rid)
        ind = r["indicadores"]
        margem_calc = ind["receita_mensal_reais"] - ind["opex_mensal_reais"]
        assert abs(ind["margem_mensal_reais"] - margem_calc) < 1.0, (
            f"Margem incorreta em '{rid}': {ind['margem_mensal_reais']} != {margem_calc}"
        )


def test_formula_deficit_todas_regioes():
    """deficit = max(0, capex - orcamento) para todas as regioes validas."""
    for rid in ["aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"]:
        r = _call(rid)
        ind = r["indicadores"]
        deficit_calc = max(0, ind["capex_reais"] - ind["orcamento_disponivel_reais"])
        assert ind["deficit_orcamentario_reais"] == deficit_calc, (
            f"Deficit incorreto em '{rid}'"
        )


def test_formula_score_final_ponderado():
    """Score final = round(0.40*payback + 0.35*cobertura + 0.25*margem) para central."""
    r = _call("central")
    ind = r["indicadores"]
    score_calc = round(
        0.40 * ind["score_payback"]
        + 0.35 * ind["score_cobertura_orcamento"]
        + 0.25 * ind["score_margem"]
    )
    assert r["score"] == score_calc
