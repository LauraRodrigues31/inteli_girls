"""
Testes obrigatórios do Agente Mercado — Conecta Conselho.

Execução:
    python -m pytest conecta-conselho/tests/test_agente_mercado.py -v

Todos os testes exercitam apenas a lógica Python (sem IBM Cloud).
"""

from __future__ import annotations

import sys
from pathlib import Path

import importlib.util as _ilu

import pytest

# Importa tool_mercado via importlib para evitar colisão de nomes entre
# `tools/` da raiz do workspace e `tools/` de `conecta-conselho/`.
_ROOT = Path(__file__).resolve().parent.parent.parent       # raiz do workspace
_TOOL_PATH = _ROOT / "tools" / "tool_mercado.py"

_spec = _ilu.spec_from_file_location("tool_mercado", _TOOL_PATH)
_mod = _ilu.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

analisar_mercado = _mod.analisar_mercado
calcular_score_mercado = _mod.calcular_score_mercado

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

REGIOES_VALIDAS = ["aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"]

CAMPOS_OBRIGATORIOS = [
    "agente",
    "regiao_id",
    "regiao_nome",
    "score",
    "confianca",
    "indicadores",
    "justificativa",
    "riscos",
    "limitacoes",
    "simulado",
    "erro",
]

CAMPOS_INDICADORES_CALCULADOS = [
    "score_renda_relativa",
    "score_crescimento",
    "score_mercado_potencial",
    "score_competitividade",
]

# ---------------------------------------------------------------------------
# Testes de contrato de saída
# ---------------------------------------------------------------------------


def test_retorna_todos_campos_obrigatorios():
    """Todos os 11 campos do contrato (Seção 3.2) devem estar presentes."""
    resultado = analisar_mercado("aurora")
    for campo in CAMPOS_OBRIGATORIOS:
        assert campo in resultado, f"Campo obrigatório ausente: '{campo}'"


def test_retorna_score_inteiro_entre_0_e_100():
    """Score deve ser inteiro no intervalo [0, 100] para todas as regiões válidas."""
    for rid in REGIOES_VALIDAS:
        resultado = analisar_mercado(rid)
        score = resultado["score"]
        assert isinstance(score, int), f"{rid}: score deve ser int, obteve {type(score)}"
        assert 0 <= score <= 100, f"{rid}: score fora do intervalo [0, 100]: {score}"


def test_campo_simulado_sempre_true():
    """O campo `simulado` deve ser True para todas as regiões válidas."""
    for rid in REGIOES_VALIDAS:
        assert analisar_mercado(rid)["simulado"] is True, f"{rid}: simulado != True"


def test_campo_erro_nulo_para_regioes_validas():
    """O campo `erro` deve ser None para todas as regiões válidas."""
    for rid in REGIOES_VALIDAS:
        resultado = analisar_mercado(rid)
        assert resultado["erro"] is None, f"{rid}: erro inesperado: {resultado['erro']}"


def test_confianca_valor_valido():
    """O campo `confianca` deve ser um dos quatro valores permitidos."""
    valores_validos = {"alta", "media", "baixa", "nao_avaliada"}
    for rid in REGIOES_VALIDAS:
        resultado = analisar_mercado(rid)
        assert resultado["confianca"] in valores_validos, (
            f"{rid}: confianca inválida: '{resultado['confianca']}'"
        )


# ---------------------------------------------------------------------------
# Testes de região inexistente
# ---------------------------------------------------------------------------


def test_regiao_inexistente_retorna_erro():
    """ID inexistente deve retornar erro não nulo, score 0 e confianca 'nao_avaliada'."""
    resultado = analisar_mercado("nao_existe")
    assert resultado["erro"] is not None, "erro deve ser não nulo para região inexistente"
    assert resultado["score"] == 0, f"score deve ser 0, obteve {resultado['score']}"
    assert resultado["confianca"] == "nao_avaliada", (
        f"confianca deve ser 'nao_avaliada', obteve '{resultado['confianca']}'"
    )


def test_regiao_inexistente_contem_campos_obrigatorios():
    """Mesmo em erro, todos os campos do contrato devem estar presentes."""
    resultado = analisar_mercado("xyz_invalido")
    for campo in CAMPOS_OBRIGATORIOS:
        assert campo in resultado, f"Campo ausente na saída de erro: '{campo}'"


# ---------------------------------------------------------------------------
# Testes de lógica de score
# ---------------------------------------------------------------------------


def test_score_aurora_maior_que_nova_uniao():
    """
    Aurora (renda R$4.200) deve ter score maior que Nova União (renda R$1.200),
    pois todos os outros fatores também favorecem Aurora.
    """
    score_aurora = analisar_mercado("aurora")["score"]
    score_nova_uniao = analisar_mercado("nova_uniao")["score"]
    assert score_aurora > score_nova_uniao, (
        f"Aurora ({score_aurora}) deveria ter score maior que Nova União ({score_nova_uniao})"
    )


def test_indicadores_contem_campos_calculados():
    """Os quatro campos de sub-score calculados devem estar presentes em `indicadores`."""
    resultado = analisar_mercado("aurora")
    for campo in CAMPOS_INDICADORES_CALCULADOS:
        assert campo in resultado["indicadores"], (
            f"Campo calculado ausente em indicadores: '{campo}'"
        )


def test_indicadores_contem_campos_brutos():
    """Os campos brutos do modelo `DadosMercado` devem estar presentes em `indicadores`."""
    campos_brutos = [
        "populacao_estimada",
        "domicilios_total",
        "renda_media_mensal_reais",
        "taxa_crescimento_populacional_pct",
        "percentual_domicilios_conectados",
        "clientes_potenciais",
        "ticket_medio_mensal_reais",
        "numero_concorrentes",
    ]
    resultado = analisar_mercado("aurora")
    for campo in campos_brutos:
        assert campo in resultado["indicadores"], f"Campo bruto ausente em indicadores: '{campo}'"


def test_limitacoes_contem_aviso_simulado():
    """O campo `limitacoes` deve sempre incluir o aviso obrigatório sobre dados simulados."""
    for rid in REGIOES_VALIDAS:
        resultado = analisar_mercado(rid)
        assert any("simulado" in lim.lower() for lim in resultado["limitacoes"]), (
            f"{rid}: limitacoes não contém aviso sobre dado simulado"
        )


def test_agente_identificado_como_mercado():
    """O campo `agente` deve sempre ser 'mercado'."""
    for rid in REGIOES_VALIDAS:
        assert analisar_mercado(rid)["agente"] == "mercado", f"{rid}: agente != 'mercado'"


# ---------------------------------------------------------------------------
# Testes unitários de calcular_score_mercado
# ---------------------------------------------------------------------------


def test_calcular_score_renda_minima():
    """Renda 800 → score_renda_relativa = 0."""
    dados = {
        "renda_media_mensal_reais": 800,
        "taxa_crescimento_populacional_pct": 0,
        "percentual_domicilios_conectados": 100,
        "numero_concorrentes": 5,
    }
    scores = calcular_score_mercado(dados)
    assert scores["score_renda_relativa"] == 0


def test_calcular_score_renda_maxima():
    """Renda 5000 → score_renda_relativa = 100."""
    dados = {
        "renda_media_mensal_reais": 5000,
        "taxa_crescimento_populacional_pct": 5,
        "percentual_domicilios_conectados": 0,
        "numero_concorrentes": 0,
    }
    scores = calcular_score_mercado(dados)
    assert scores["score_renda_relativa"] == 100


def test_calcular_score_competitividade_zero_concorrentes():
    """0 concorrentes → score_competitividade = 100."""
    dados = {
        "renda_media_mensal_reais": 2000,
        "taxa_crescimento_populacional_pct": 2,
        "percentual_domicilios_conectados": 50,
        "numero_concorrentes": 0,
    }
    scores = calcular_score_mercado(dados)
    assert scores["score_competitividade"] == 100


def test_calcular_score_competitividade_cinco_concorrentes():
    """5+ concorrentes → score_competitividade = 0."""
    dados = {
        "renda_media_mensal_reais": 2000,
        "taxa_crescimento_populacional_pct": 2,
        "percentual_domicilios_conectados": 50,
        "numero_concorrentes": 5,
    }
    scores = calcular_score_mercado(dados)
    assert scores["score_competitividade"] == 0


def test_calcular_score_final_e_inteiro():
    """Score final deve ser int."""
    dados = {
        "renda_media_mensal_reais": 3000,
        "taxa_crescimento_populacional_pct": 2.5,
        "percentual_domicilios_conectados": 60,
        "numero_concorrentes": 2,
    }
    scores = calcular_score_mercado(dados)
    assert isinstance(scores["score_final"], int)


def test_calcular_score_nao_extrapola_limites():
    """Sub-scores e score final nunca devem extrapolar [0, 100]."""
    dados_extremos = [
        {"renda_media_mensal_reais": 0, "taxa_crescimento_populacional_pct": 100,
         "percentual_domicilios_conectados": 0, "numero_concorrentes": 0},
        {"renda_media_mensal_reais": 99999, "taxa_crescimento_populacional_pct": 0,
         "percentual_domicilios_conectados": 100, "numero_concorrentes": 99},
    ]
    for dados in dados_extremos:
        s = calcular_score_mercado(dados)
        for campo in ["score_renda_relativa", "score_crescimento",
                      "score_mercado_potencial", "score_competitividade", "score_final"]:
            assert 0 <= s[campo] <= 100, f"{campo}={s[campo]} fora de [0,100]"


# ---------------------------------------------------------------------------
# Testes de regressão de valores esperados
# ---------------------------------------------------------------------------


def test_score_aurora_valor_esperado():
    """
    Aurora: renda=4200, cresc=2.1, pct_conn=62, conc=3
      renda_rel   = (4200-800)/(5000-800)*100 = 80.952 → round=81
      crescimento = 2.1/5*100 = 42.0            → round=42
      potencial   = 100-62 = 38
      competit    = 100-(3/5)*100 = 40
      final       = 0.30*80.952 + 0.20*42 + 0.30*38 + 0.20*40
                  = 24.286 + 8.4 + 11.4 + 8.0 = 52.086 → 52
    """
    resultado = analisar_mercado("aurora")
    assert resultado["score"] == 52, f"Score esperado 52, obteve {resultado['score']}"


def test_score_horizonte_confianca_alta():
    """
    Horizonte tem todos os 8 campos obrigatórios preenchidos → confianca deve ser 'alta'.
    """
    resultado = analisar_mercado("horizonte")
    assert resultado["confianca"] == "alta"
