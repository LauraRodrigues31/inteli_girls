"""
Testes do Agente Engenharia — Conecta Conselho.

Carrega tools/tool_engenharia.py pelo caminho do arquivo para evitar conflito
de nomes entre a pasta tools/ da raiz e conecta-conselho/tools/.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Carregamento da ferramenta via caminho absoluto
# ---------------------------------------------------------------------------

_TOOL_PATH = Path(__file__).resolve().parent.parent.parent / "tools" / "tool_engenharia.py"

spec = importlib.util.spec_from_file_location("tool_engenharia", _TOOL_PATH)
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)

montar_parecer = _mod.montar_parecer
calcular_score_engenharia = _mod.calcular_score_engenharia
calcular_confianca = _mod.calcular_confianca

# ---------------------------------------------------------------------------
# Dados esperados (pré-calculados — reprodução determinística)
# ---------------------------------------------------------------------------

SCORES_ESPERADOS = {
    "central":    86,
    "aurora":     74,
    "vale_verde": 58,
    "horizonte":  49,
    "esperanca":  34,
    "nova_uniao": 11,
}

REGIOES_VALIDAS = list(SCORES_ESPERADOS.keys())

CAMPOS_CONTRATO = {
    "agente", "regiao_id", "regiao_nome", "score", "confianca",
    "indicadores", "justificativa", "riscos", "limitacoes", "simulado", "erro",
}

CAMPOS_INDICADORES = {
    "tipo_infraestrutura_disponivel",
    "distancia_backbone_km",
    "percentual_cobertura_fibra",
    "capacidade_infraestrutura_existente",
    "dificuldades_tecnicas",
    "prazo_implantacao_meses",
    "tecnologias_viaveis",
    "indice_viabilidade_tecnica",
    "score_backbone",
    "score_cobertura_fibra",
    "score_prazo",
    "score_base_viabilidade",
}

LIMITACOES_OBRIGATORIAS = [
    "Dado simulado — não reflete condições reais",
    "Índice de viabilidade técnica é estimativa simulada",
]

# ---------------------------------------------------------------------------
# Testes obrigatórios (Seção 8 do padrão)
# ---------------------------------------------------------------------------


def test_score_central_maior_que_nova_uniao():
    """central (backbone 8 km) deve ser tecnicamente mais viável que nova_uniao (98 km)."""
    r_central = montar_parecer("central")
    r_nova = montar_parecer("nova_uniao")
    assert r_central["score"] > r_nova["score"]


def test_score_nova_uniao_menor_ou_igual_30():
    """nova_uniao tem backbone de 98 km, fibra 0% e viabilidade 18 — score deve ser ≤ 30."""
    r = montar_parecer("nova_uniao")
    assert r["score"] <= 30


def test_score_central_maior_que_esperanca():
    """central (viabilidade 88) deve ter score maior que esperanca (viabilidade 38)."""
    r_central = montar_parecer("central")
    r_esp = montar_parecer("esperanca")
    assert r_central["score"] > r_esp["score"]


def test_regiao_inexistente_retorna_erro():
    """ID inválido deve retornar erro não nulo, score 0 e confiança nao_avaliada."""
    r = montar_parecer("nao_existe")
    assert r["erro"] is not None
    assert r["score"] == 0
    assert r["confianca"] == "nao_avaliada"


def test_simulado_sempre_true():
    """O campo simulado deve ser True para todas as regiões válidas."""
    for rid in REGIOES_VALIDAS:
        r = montar_parecer(rid)
        assert r["simulado"] is True, f"simulado=False para {rid}"


def test_indice_viabilidade_tecnica_bate_com_base():
    """indice_viabilidade_tecnica nos indicadores deve vir direto da base."""
    base = {
        "central":    88,
        "aurora":     78,
        "vale_verde": 62,
        "horizonte":  51,
        "esperanca":  38,
        "nova_uniao": 18,
    }
    for rid, valor_base in base.items():
        r = montar_parecer(rid)
        assert r["indicadores"]["indice_viabilidade_tecnica"] == valor_base, (
            f"{rid}: esperado {valor_base}, obtido {r['indicadores']['indice_viabilidade_tecnica']}"
        )


# ---------------------------------------------------------------------------
# Testes extras
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("regiao_id", REGIOES_VALIDAS)
def test_score_inteiro_entre_0_e_100(regiao_id):
    """Score deve ser inteiro no intervalo [0, 100]."""
    r = montar_parecer(regiao_id)
    assert isinstance(r["score"], int), f"{regiao_id}: score não é inteiro"
    assert 0 <= r["score"] <= 100, f"{regiao_id}: score fora do intervalo"


@pytest.mark.parametrize("regiao_id, score_esperado", SCORES_ESPERADOS.items())
def test_scores_exatos(regiao_id, score_esperado):
    """Scores calculados devem bater exatamente com os valores de referência."""
    r = montar_parecer(regiao_id)
    assert r["score"] == score_esperado, (
        f"{regiao_id}: esperado {score_esperado}, obtido {r['score']}"
    )


@pytest.mark.parametrize("frase", LIMITACOES_OBRIGATORIAS)
def test_limitacoes_obrigatorias_presentes(frase):
    """As duas frases obrigatórias devem aparecer em limitacoes para todas as regiões."""
    for rid in REGIOES_VALIDAS:
        r = montar_parecer(rid)
        assert frase in r["limitacoes"], (
            f"{rid}: frase ausente em limitacoes: '{frase}'"
        )


@pytest.mark.parametrize("regiao_id", REGIOES_VALIDAS)
def test_todos_campos_do_contrato_presentes(regiao_id):
    """O parecer deve conter todos os campos do contrato da Seção 8."""
    r = montar_parecer(regiao_id)
    faltando = CAMPOS_CONTRATO - set(r.keys())
    assert not faltando, f"{regiao_id}: campos ausentes no contrato: {faltando}"


@pytest.mark.parametrize("regiao_id", REGIOES_VALIDAS)
def test_todos_campos_de_indicadores_presentes(regiao_id):
    """Todos os campos de indicadores (8 da base + 4 sub-scores) devem estar presentes."""
    r = montar_parecer(regiao_id)
    faltando = CAMPOS_INDICADORES - set(r["indicadores"].keys())
    assert not faltando, f"{regiao_id}: campos ausentes em indicadores: {faltando}"


@pytest.mark.parametrize("regiao_id", REGIOES_VALIDAS)
def test_justificativa_minimo_50_chars(regiao_id):
    """Justificativa deve ter no mínimo 50 caracteres."""
    r = montar_parecer(regiao_id)
    assert len(r["justificativa"]) >= 50, (
        f"{regiao_id}: justificativa muito curta ({len(r['justificativa'])} chars)"
    )


@pytest.mark.parametrize("regiao_id", REGIOES_VALIDAS)
def test_riscos_nao_vazios(regiao_id):
    """Lista de riscos não deve ser vazia para regiões válidas."""
    r = montar_parecer(regiao_id)
    assert len(r["riscos"]) > 0, f"{regiao_id}: riscos está vazio"


@pytest.mark.parametrize("regiao_id", REGIOES_VALIDAS)
def test_reprodutibilidade(regiao_id):
    """A mesma região chamada duas vezes deve devolver o mesmo resultado."""
    r1 = montar_parecer(regiao_id)
    r2 = montar_parecer(regiao_id)
    assert r1 == r2, f"{regiao_id}: resultados diferentes entre chamadas"


def test_campo_agente_e_engenharia():
    """O campo agente deve ser exatamente 'engenharia' para todas as regiões."""
    for rid in REGIOES_VALIDAS:
        r = montar_parecer(rid)
        assert r["agente"] == "engenharia", f"{rid}: agente='{r['agente']}'"


def test_erro_nulo_em_regioes_validas():
    """O campo erro deve ser None para todas as regiões válidas."""
    for rid in REGIOES_VALIDAS:
        r = montar_parecer(rid)
        assert r["erro"] is None, f"{rid}: erro não é None: {r['erro']}"


def test_regiao_inexistente_indicadores_vazios():
    """Para região inexistente, indicadores deve ser {}."""
    r = montar_parecer("nao_existe")
    assert r["indicadores"] == {}


def test_regiao_inexistente_regiao_nome_null():
    """Para região inexistente, regiao_nome deve ser None."""
    r = montar_parecer("nao_existe")
    assert r["regiao_nome"] is None
