"""
Testes obrigatórios do Agente Pontes — Conecta Conselho.

Executar da raiz do projeto:
    python -m pytest conecta-conselho/tests/test_agente_pontes.py -v

Todos os dados são SIMULADOS — nenhum contrato ou acordo real existe.
"""

import importlib.util
import sys
from pathlib import Path

from tools.tool_pontes import analisar_pontes

# ---------------------------------------------------------------------------
# Import robusto de consultar_parcerias — funciona com hífen no nome do dir
# ---------------------------------------------------------------------------
_consultar_regiao_path = (
    Path(__file__).parent.parent / "tools" / "consultar_regiao.py"
)
_spec = importlib.util.spec_from_file_location("consultar_regiao", _consultar_regiao_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_consultar_parcerias_base = _mod.consultar_parcerias


# ---------------------------------------------------------------------------
# Helper: desempacota ToolResponse do ADK (r.content) ou dict simples
# ---------------------------------------------------------------------------

def _dados(r) -> dict:
    """Retorna o dicionário de dados independente de ser ToolResponse ou dict."""
    return r.content if hasattr(r, "content") else r


# ===========================================================================
# TESTES OBRIGATÓRIOS (definidos no PLANO_AGENTE_PONTES.md e PADRAO sec. 10)
# ===========================================================================

# 1. Vale Verde (maturidade alta, 10 parceiros) > Nova União (maturidade baixa, 3)
# ---------------------------------------------------------------------------

def test_vale_verde_maior_que_nova_uniao():
    vale = _dados(analisar_pontes("vale_verde"))
    nova = _dados(analisar_pontes("nova_uniao"))
    assert vale["score"] > nova["score"], (
        f"Esperado score vale_verde > nova_uniao, "
        f"obtido {vale['score']} vs {nova['score']}"
    )


# 2. Campo limitacoes contém aviso obrigatório de hipótese simulada
# ---------------------------------------------------------------------------

def test_limitacoes_contem_aviso_hipotetico():
    r = _dados(analisar_pontes("aurora"))
    assert any("hipotéticas simuladas" in l for l in r["limitacoes"]), (
        "Campo 'limitacoes' deve conter o aviso sobre parcerias hipotéticas simuladas."
    )


# 3. infraestrutura_compartilhavel bate com a base de dados
# ---------------------------------------------------------------------------

def test_infraestrutura_compativel_com_base():
    base = _consultar_parcerias_base("central")["dados"]["infraestrutura_compartilhavel"]
    r = _dados(analisar_pontes("central"))
    assert r["indicadores"]["infraestrutura_compartilhavel"] == base, (
        f"Esperado infraestrutura_compartilhavel={base}, "
        f"obtido {r['indicadores']['infraestrutura_compartilhavel']}"
    )


# 4. Região inexistente retorna erro não nulo e score 0
# ---------------------------------------------------------------------------

def test_regiao_inexistente():
    r = _dados(analisar_pontes("nao_existe"))
    assert r["erro"] is not None, "Campo 'erro' deve ser não-nulo para região inexistente."
    assert r["score"] == 0, f"Score deve ser 0 para região inexistente, obtido {r['score']}."


# 5. total_parceiros_possiveis == len(publicos) + len(privados)
# ---------------------------------------------------------------------------

def test_total_parceiros_calculado():
    r = _dados(analisar_pontes("horizonte"))
    ind = r["indicadores"]
    esperado = len(ind["parceiros_publicos_possiveis"]) + len(ind["parceiros_privados_possiveis"])
    assert ind["total_parceiros_possiveis"] == esperado, (
        f"total_parceiros_possiveis={ind['total_parceiros_possiveis']} "
        f"não bate com publicos+privados={esperado}"
    )


# ===========================================================================
# TESTES DO CONTRATO OBRIGATÓRIO (Seção 3.2 do PADRAO_DESENVOLVIMENTO_AGENTES)
# ===========================================================================

# 6. Todos os campos obrigatórios do contrato estão presentes
# ---------------------------------------------------------------------------

def test_campos_obrigatorios_presentes():
    r = _dados(analisar_pontes("aurora"))
    campos = ["agente", "regiao_id", "regiao_nome", "score", "confianca",
              "indicadores", "justificativa", "riscos", "limitacoes", "simulado", "erro"]
    for campo in campos:
        assert campo in r, f"Campo obrigatório '{campo}' ausente na saída."


# 7. Campo "agente" é sempre "pontes"
# ---------------------------------------------------------------------------

def test_campo_agente_correto():
    r = _dados(analisar_pontes("vale_verde"))
    assert r["agente"] == "pontes", f"Campo 'agente' deve ser 'pontes', obtido '{r['agente']}'"


# 8. Score é inteiro entre 0 e 100
# ---------------------------------------------------------------------------

def test_score_inteiro_entre_0_e_100():
    for regiao_id in ["aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"]:
        r = _dados(analisar_pontes(regiao_id))
        assert isinstance(r["score"], int), f"Score deve ser inteiro para '{regiao_id}'"
        assert 0 <= r["score"] <= 100, f"Score fora de 0-100 para '{regiao_id}': {r['score']}"


# 9. simulado é sempre True
# ---------------------------------------------------------------------------

def test_simulado_sempre_true():
    for regiao_id in ["aurora", "nao_existe"]:
        r = _dados(analisar_pontes(regiao_id))
        assert r["simulado"] is True, f"Campo 'simulado' deve ser True para '{regiao_id}'"


# 10. Indicadores contêm todos os sub-scores e campos obrigatórios do padrão
# ---------------------------------------------------------------------------

def test_indicadores_campos_obrigatorios():
    r = _dados(analisar_pontes("esperanca"))
    ind = r["indicadores"]
    campos = [
        "quantidade_instituicoes_ancora",
        "total_parceiros_possiveis",
        "parceiros_publicos_possiveis",
        "parceiros_privados_possiveis",
        "infraestrutura_compartilhavel",
        "oportunidades_reducao_custos",
        "percentual_economia_potencial_pct",
        "maturidade_parcerias",
        "score_quantidade_parceiros",
        "score_infraestrutura",
        "score_economia_potencial",
        "score_maturidade",
    ]
    for campo in campos:
        assert campo in ind, f"Campo obrigatório 'indicadores.{campo}' ausente."


# 11. justificativa tem mínimo 50 caracteres
# ---------------------------------------------------------------------------

def test_justificativa_minimo_50_chars():
    r = _dados(analisar_pontes("nova_uniao"))
    assert len(r["justificativa"]) >= 50, (
        f"justificativa deve ter ≥50 chars, tem {len(r['justificativa'])}"
    )


# 12. riscos é lista não vazia para regiões válidas
# ---------------------------------------------------------------------------

def test_riscos_lista_nao_vazia():
    r = _dados(analisar_pontes("horizonte"))
    assert isinstance(r["riscos"], list), "Campo 'riscos' deve ser uma lista."
    assert len(r["riscos"]) > 0, "Campo 'riscos' não pode ser vazio para região válida."


# 13. confianca tem valor válido
# ---------------------------------------------------------------------------

def test_confianca_valor_valido():
    valores_validos = {"alta", "media", "baixa", "nao_avaliada"}
    for regiao_id in ["aurora", "nao_existe"]:
        r = _dados(analisar_pontes(regiao_id))
        assert r["confianca"] in valores_validos, (
            f"confianca='{r['confianca']}' não é um valor válido para '{regiao_id}'"
        )
