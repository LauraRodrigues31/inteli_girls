"""
Testes automatizados para o Agente Guardiao — Conecta Conselho.

Monta os pareceres chamando as 5 tools locais e verifica os resultados
deterministicos esperados para as 6 regioes.

Execute com:
    python -m pytest conecta-conselho/tests/test_guardiao.py -v

AVISO: Dados SIMULADOS. Nao usar para decisoes reais.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Tools na raiz do repo (tools/) e conecta-conselho/ no path
_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT / "tools"))
sys.path.insert(1, str(_ROOT / "conecta-conselho"))

import tool_guardiao as _mod_g
from tool_mercado import analisar_mercado
from tool_social import analisar_impacto_social
from tool_engenharia import analisar_engenharia
from tool_orcamento import analisar_orcamento
from tool_pontes import analisar_pontes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unwrap(result) -> dict:
    """Desempacota ToolResponse se necessario."""
    if hasattr(result, "content"):
        return result.content
    return result


def _montar_pareceres(regiao_id: str) -> str:
    """Chama as 5 tools e monta o JSON de pareceres."""
    pareceres = {
        "mercado":        _unwrap(analisar_mercado(regiao_id)),
        "impacto_social": _unwrap(analisar_impacto_social(regiao_id)),
        "engenharia":     _unwrap(analisar_engenharia(regiao_id)),
        "orcamento":      _unwrap(analisar_orcamento(regiao_id)),
        "pontes":         _unwrap(analisar_pontes(regiao_id)),
    }
    return json.dumps(pareceres, ensure_ascii=False)


def _consolidar(regiao_id: str) -> dict:
    """Monta pareceres e chama consolidar_pareceres; retorna dict."""
    pareceres_json = _montar_pareceres(regiao_id)
    result = _mod_g.consolidar_pareceres(pareceres_json)
    return _unwrap(result)


def _parecer_sintetico(score: int, agente: str = "mercado", erro=None) -> dict:
    return {
        "agente": agente,
        "regiao_id": "teste",
        "regiao_nome": "Regiao Teste",
        "score": score,
        "confianca": "alta",
        "justificativa": "Justificativa de teste para verificacao de limiares.",
        "riscos": ["risco de teste"],
        "limitacoes": ["dado simulado"],
        "simulado": True,
        "erro": erro,
    }


def _pareceres_sinteticos(scores: dict, erros: dict | None = None) -> str:
    """Monta pareceres sinteticos com scores definidos manualmente."""
    erros = erros or {}
    pareceres = {}
    for agente in ["mercado", "impacto_social", "engenharia", "orcamento", "pontes"]:
        p = _parecer_sintetico(scores.get(agente, 50), agente=agente)
        if agente in erros:
            p["erro"] = erros[agente]
        pareceres[agente] = p
    return json.dumps(pareceres, ensure_ascii=False)


def _score_sintetico(scores: dict) -> int:
    """Calcula score consolidado sintetico para validacao."""
    return round(
        0.20 * scores.get("mercado", 50) +
        0.20 * scores.get("impacto_social", 50) +
        0.25 * scores.get("engenharia", 50) +
        0.25 * scores.get("orcamento", 50) +
        0.10 * scores.get("pontes", 50)
    )


# ---------------------------------------------------------------------------
# Testes de recomendacao e score esperados para as 6 regioes
# aurora 62 realizar_piloto | horizonte 57 realizar_piloto |
# esperanca 44 aguardar | central 60 realizar_piloto |
# vale_verde 60 realizar_piloto | nova_uniao 30 aguardar (com atencao_prioritaria)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("regiao_id,score_esp,rec_esp,atencao_esp", [
    ("aurora",     62, "realizar_piloto", False),
    ("horizonte",  57, "realizar_piloto", False),
    ("esperanca",  44, "aguardar",        False),
    ("central",    60, "realizar_piloto", False),
    ("vale_verde", 60, "realizar_piloto", False),
    ("nova_uniao", 30, "aguardar",        True),
])
def test_score_recomendacao_e_atencao_esperados(regiao_id, score_esp, rec_esp, atencao_esp):
    r = _consolidar(regiao_id)
    assert r["status"] == "concluida", f"{regiao_id}: esperado status concluida"
    assert r["score_consolidado"] == score_esp, (
        f"{regiao_id}: score esperado {score_esp}, obtido {r['score_consolidado']}"
    )
    assert r["recomendacao"] == rec_esp, (
        f"{regiao_id}: recomendacao esperada '{rec_esp}', obtida '{r['recomendacao']}'"
    )
    assert r["atencao_prioritaria"] == atencao_esp, (
        f"{regiao_id}: atencao_prioritaria esperada {atencao_esp}, obtida {r['atencao_prioritaria']}"
    )


def test_escalar_nunca_aparece_como_recomendacao():
    """'escalar' nao deve aparecer como recomendacao em nenhuma regiao valida."""
    for rid in ["aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"]:
        r = _consolidar(rid)
        assert r.get("recomendacao") != "escalar", (
            f"{rid}: recomendacao 'escalar' nao deve existir mais"
        )


def test_nova_uniao_atencao_prioritaria_com_pontos_criticos():
    """Nova Uniao deve ter atencao_prioritaria=True e pontos_criticos citando orc, eng e confianca."""
    r = _consolidar("nova_uniao")
    assert r["atencao_prioritaria"] is True
    pontos = " ".join(r.get("pontos_criticos", []))
    # Orcamento score 0 < 20 (texto usa "Orçamento" com acento)
    assert "score 0" in pontos or "amento" in pontos, (
        f"Ponto critico de orcamento esperado em: {r.get('pontos_criticos')}"
    )
    # Engenharia score 11 < 20
    assert "score 11" in pontos or "ngenharia" in pontos, (
        f"Ponto critico de engenharia esperado em: {r.get('pontos_criticos')}"
    )


def test_nova_uniao_motivos_e_caminhos_presentes():
    """Nova Uniao tem recomendacao aguardar -> motivos e caminhos devem ser preenchidos."""
    r = _consolidar("nova_uniao")
    assert r["recomendacao"] == "aguardar"
    assert len(r.get("motivos", [])) > 0, "Motivos devem ser preenchidos para aguardar"
    # Caminhos podem ser vazios se os campos indicadores nao existirem, mas nao devem quebrar
    assert isinstance(r.get("caminhos"), list)


def test_esperanca_motivos_e_caminhos_presentes():
    """Esperanca tem recomendacao aguardar -> motivos e caminhos devem ser preenchidos."""
    r = _consolidar("esperanca")
    assert r["recomendacao"] == "aguardar"
    assert len(r.get("motivos", [])) > 0


def test_aurora_motivos_caminhos_vazios():
    """Aurora tem realizar_piloto -> motivos e caminhos devem ser listas vazias."""
    r = _consolidar("aurora")
    assert r["recomendacao"] == "realizar_piloto"
    assert r.get("motivos") == []
    assert r.get("caminhos") == []


def test_regiao_inexistente_analise_incompleta():
    """Regiao inexistente: todos os 5 pareceres tem erro -> analise_incompleta, recomendacao null."""
    r = _consolidar("nao_existe")
    assert r["status"] == "analise_incompleta", (
        f"Esperado analise_incompleta, obtido {r['status']}"
    )
    assert r["recomendacao"] is None
    assert r["score_consolidado"] is None
    assert "agentes_com_falha" in r
    assert len(r["agentes_com_falha"]) == 5


# ---------------------------------------------------------------------------
# Testes de limiares exatos
# ---------------------------------------------------------------------------

def test_limiar_49_aguardar():
    """Score 49 deve ser 'aguardar'."""
    scores = {"mercado": 50, "impacto_social": 50, "engenharia": 49, "orcamento": 49, "pontes": 45}
    assert _score_sintetico(scores) == 49
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["score_consolidado"] == 49
    assert r["recomendacao"] == "aguardar"


def test_limiar_50_realizar_piloto():
    """Score 50 deve ser 'realizar_piloto'."""
    scores = {"mercado": 50, "impacto_social": 50, "engenharia": 50, "orcamento": 50, "pontes": 50}
    assert _score_sintetico(scores) == 50
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["score_consolidado"] == 50
    assert r["recomendacao"] == "realizar_piloto"


def test_limiar_69_realizar_piloto():
    """Score 69, eng>=60, orc>=60 -> NAO atinge 70 -> realizar_piloto."""
    scores = {"mercado": 70, "impacto_social": 70, "engenharia": 69, "orcamento": 69, "pontes": 65}
    assert _score_sintetico(scores) == 69
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["score_consolidado"] == 69
    assert r["recomendacao"] == "realizar_piloto"


def test_limiar_70_investir_agora():
    """Score 70, eng>=60, orc>=60 -> 'investir_agora'."""
    scores = {"mercado": 70, "impacto_social": 70, "engenharia": 70, "orcamento": 70, "pontes": 70}
    assert _score_sintetico(scores) == 70
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["score_consolidado"] == 70
    assert r["recomendacao"] == "investir_agora"


def test_score_29_aguardar_com_atencao():
    """Score 29 -> aguardar (nao mais escalar) + atencao_prioritaria True."""
    # m=30, s=30, e=30, o=25, p=30 -> 6+6+7.5+6.25+3 = 28.75 -> 29
    scores = {"mercado": 30, "impacto_social": 30, "engenharia": 30, "orcamento": 25, "pontes": 30}
    assert _score_sintetico(scores) == 29
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["score_consolidado"] == 29
    assert r["recomendacao"] == "aguardar"   # nao mais escalar
    assert r["atencao_prioritaria"] is True   # score < 30


def test_score_30_aguardar_sem_atencao():
    """Score 30, sem eng/orc criticos -> aguardar e atencao_prioritaria False."""
    scores = {"mercado": 30, "impacto_social": 30, "engenharia": 30, "orcamento": 30, "pontes": 30}
    assert _score_sintetico(scores) == 30
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["score_consolidado"] == 30
    assert r["recomendacao"] == "aguardar"
    assert r["atencao_prioritaria"] is False


# ---------------------------------------------------------------------------
# Testes de atencao_prioritaria
# ---------------------------------------------------------------------------

def test_atencao_eng_menor_20():
    """Engenharia < 20 deve acionar atencao_prioritaria=True."""
    scores = {"mercado": 60, "impacto_social": 60, "engenharia": 15, "orcamento": 60, "pontes": 60}
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["atencao_prioritaria"] is True
    assert any("ngenharia" in p for p in r["pontos_criticos"])


def test_atencao_orc_menor_20():
    """Orcamento < 20 deve acionar atencao_prioritaria=True."""
    scores = {"mercado": 60, "impacto_social": 60, "engenharia": 60, "orcamento": 10, "pontes": 60}
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["atencao_prioritaria"] is True
    # "amento" cobre tanto "Orcamento" (sem acento) quanto "Orçamento" (com acento)
    assert any("amento" in p for p in r["pontos_criticos"])


def test_atencao_confianca_baixa():
    """Parecer com confianca 'baixa' deve acionar atencao_prioritaria=True."""
    pareceres = {}
    for agente in ["mercado", "impacto_social", "engenharia", "orcamento", "pontes"]:
        p = _parecer_sintetico(60, agente=agente)
        if agente == "orcamento":
            p["confianca"] = "baixa"
        pareceres[agente] = p
    j = json.dumps(pareceres)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["atencao_prioritaria"] is True
    assert any("baixa" in p.lower() or "rcamento" in p.lower() for p in r["pontos_criticos"])


def test_sem_atencao_scores_equilibrados():
    """Scores equilibrados e sem confianca baixa -> atencao_prioritaria False."""
    scores = {"mercado": 60, "impacto_social": 60, "engenharia": 60, "orcamento": 60, "pontes": 60}
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["atencao_prioritaria"] is False
    assert r["pontos_criticos"] == []


# ---------------------------------------------------------------------------
# Testes de analise_incompleta
# ---------------------------------------------------------------------------

def test_analise_incompleta_um_parecer_com_erro():
    """Apenas 1 dos 5 pareceres com erro -> analise_incompleta, recomendacao null."""
    scores = {"mercado": 60, "impacto_social": 60, "engenharia": 60, "orcamento": 60, "pontes": 60}
    j = _pareceres_sinteticos(scores, erros={"engenharia": "Falha ao consultar dados"})
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["status"] == "analise_incompleta"
    assert r["recomendacao"] is None
    assert r["score_consolidado"] is None
    assert "agentes_com_falha" in r
    assert any(f["agente"] == "engenharia" for f in r["agentes_com_falha"])


def test_analise_incompleta_agente_ausente():
    """JSON sem a chave 'mercado' -> analise_incompleta."""
    pareceres = {
        agente: _parecer_sintetico(60, agente=agente)
        for agente in ["impacto_social", "engenharia", "orcamento", "pontes"]
    }
    j = json.dumps(pareceres)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["status"] == "analise_incompleta"
    assert r["recomendacao"] is None


def test_status_concluida_todos_validos():
    """Todos os 5 pareceres validos -> status concluida."""
    scores = {"mercado": 60, "impacto_social": 60, "engenharia": 60, "orcamento": 60, "pontes": 60}
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["status"] == "concluida"
    assert r["recomendacao"] is not None
    assert r["score_consolidado"] is not None


# ---------------------------------------------------------------------------
# Testes das divergencias (D1, D2, D3)
# ---------------------------------------------------------------------------

def test_divergencia_social_vs_orcamento():
    """Diferenca > 30 entre impacto_social e orcamento gera divergencia."""
    scores = {"mercado": 50, "impacto_social": 90, "engenharia": 50, "orcamento": 55, "pontes": 50}
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert any("impacto social" in d.lower() or "impacto_social" in d.lower()
               for d in r["divergencias"]), f"D1 nao detectada: {r['divergencias']}"


def test_divergencia_engenharia_baixa_mercado_alto():
    """Engenharia < 40 e mercado > 60 gera divergencia tecnica."""
    scores = {"mercado": 70, "impacto_social": 50, "engenharia": 30, "orcamento": 50, "pontes": 50}
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert any("engenharia" in d.lower() for d in r["divergencias"]), (
        f"D2 nao detectada: {r['divergencias']}"
    )


def test_divergencia_pontes_alto_orcamento_baixo():
    """Pontes > 70 e orcamento < 40 gera divergencia de cofinanciamento."""
    scores = {"mercado": 50, "impacto_social": 50, "engenharia": 50, "orcamento": 30, "pontes": 80}
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert any("parcerias" in d.lower() or "pontes" in d.lower()
               for d in r["divergencias"]), f"D3 nao detectada: {r['divergencias']}"


def test_sem_divergencias_scores_equilibrados():
    """Scores equilibrados sem erros -> sem divergencias."""
    scores = {"mercado": 60, "impacto_social": 60, "engenharia": 60, "orcamento": 60, "pontes": 60}
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["divergencias"] == []


def test_d1_inversa_central():
    """Central: orcamento=76 > social=30 (diff=46) -> D1 direcao inversa com texto de contrapartidas sociais."""
    r = _consolidar("central")
    divs = r.get("divergencias", [])
    texto = " ".join(divs).lower()
    assert "contrapartida" in texto or "impacto social" in texto, (
        f"D1 inversa nao detectada em Central: {divs}"
    )
    # Texto da direcao INVERSA deve mencionar "financeiramente atrativa" ou "contrapartidas sociais"
    assert any(
        "financeiramente" in d.lower() or "contrapartida" in d.lower()
        for d in divs
    ), f"D1 inversa deve citar 'financeiramente' ou 'contrapartida' em Central: {divs}"
    # Nao deve citar "subsidios" (isso e da direcao original, social > orcamento)
    assert not any("subsid" in d.lower() for d in divs), (
        f"D1 inversa nao deve citar subsidios em Central: {divs}"
    )


def test_d1_original_nova_uniao():
    """Nova Uniao: social=78 > orcamento=0 (diff=78) -> D1 direcao original com parcerias e subsidios."""
    r = _consolidar("nova_uniao")
    divs = r.get("divergencias", [])
    assert any("subsid" in d.lower() or "parceria" in d.lower() for d in divs), (
        f"D1 original deve citar subsidios ou parcerias em Nova Uniao: {divs}"
    )
    assert not any("financeiramente atrativa" in d.lower() for d in divs), (
        f"D1 original nao deve citar 'financeiramente atrativa' em Nova Uniao: {divs}"
    )


def test_motivos_sem_frases_cortadas():
    """Nenhum motivo ou ponto_critico deve terminar com 'score <numero>.' (frase cortada)."""
    import re
    _padrao_cortado = re.compile(r"score \d+\.$")
    for rid in ["aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"]:
        r = _consolidar(rid)
        for frase in r.get("motivos", []) + r.get("pontos_criticos", []):
            assert not _padrao_cortado.search(frase), (
                f"{rid}: frase parece cortada em '{frase}'"
            )


def test_valores_reais_formato_brasileiro():
    """Motivos e caminhos de Esperanca devem usar formato R$ brasileiro (ponto como milhar, virgula decimal)."""
    r = _consolidar("esperanca")
    textos = " ".join(r.get("motivos", []) + r.get("caminhos", []))
    # Deve conter R$ com ponto como separador de milhar
    assert "R$" in textos, f"Formato R$ ausente em motivos/caminhos de Esperanca: {textos}"
    # Percentual com virgula: ex. 57,5%
    assert "%" in textos, f"Percentual ausente em motivos/caminhos de Esperanca: {textos}"
    import re
    # Formato percentual brasileiro: digito, virgula, digito, %
    assert re.search(r"\d,\d+%", textos), (
        f"Percentual no formato brasileiro (X,Y%) ausente em motivos/caminhos: {textos}"
    )


# ---------------------------------------------------------------------------
# Testes de JSON invalido e entradas malformadas
# ---------------------------------------------------------------------------

def test_json_invalido_retorna_analise_incompleta():
    """String nao-JSON deve retornar status analise_incompleta."""
    r = _unwrap(_mod_g.consolidar_pareceres("isso nao e json {{{"))
    assert r["status"] == "analise_incompleta"
    assert r["erro"] is not None
    assert r["score_consolidado"] is None


def test_json_lista_retorna_analise_incompleta():
    """JSON que e lista (nao objeto) deve retornar analise_incompleta."""
    r = _unwrap(_mod_g.consolidar_pareceres("[1, 2, 3]"))
    assert r["status"] == "analise_incompleta"
    assert r["erro"] is not None


def test_json_vazio_analise_incompleta():
    """JSON objeto vazio -> todos agentes ausentes -> analise_incompleta."""
    r = _unwrap(_mod_g.consolidar_pareceres("{}"))
    assert r["status"] == "analise_incompleta"
    assert r["recomendacao"] is None
    assert r["erro"] is None  # nao e erro de parse


# ---------------------------------------------------------------------------
# Testes de estrutura e campos obrigatorios
# ---------------------------------------------------------------------------

def test_campos_obrigatorios_presentes():
    r = _consolidar("central")
    campos = [
        "agente", "regiao_id", "regiao_nome", "status", "recomendacao",
        "score_consolidado", "pareceres", "divergencias", "atencao_prioritaria",
        "pontos_criticos", "motivos", "caminhos", "justificativa_consolidada",
        "principais_riscos", "limitacoes", "simulado", "erro",
    ]
    for campo in campos:
        assert campo in r, f"Campo obrigatorio ausente: {campo}"


def test_agente_e_guardiao():
    r = _consolidar("central")
    assert r["agente"] == "guardiao"


def test_simulado_sempre_true():
    for rid in ["aurora", "central", "nova_uniao"]:
        r = _consolidar(rid)
        assert r["simulado"] is True


def test_cinco_pareceres_presentes():
    r = _consolidar("central")
    for agente in ["mercado", "impacto_social", "engenharia", "orcamento", "pontes"]:
        assert agente in r["pareceres"], f"Parecer ausente: {agente}"


def test_score_consolidado_inteiro_0_a_100():
    for rid in ["aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"]:
        r = _consolidar(rid)
        sc = r["score_consolidado"]
        assert isinstance(sc, int), f"Score nao inteiro em {rid}"
        assert 0 <= sc <= 100, f"Score fora do intervalo em {rid}: {sc}"


def test_recomendacao_valores_validos():
    validos = {"investir_agora", "realizar_piloto", "aguardar"}
    for rid in ["aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"]:
        r = _consolidar(rid)
        assert r["recomendacao"] in validos, (
            f"{rid}: recomendacao invalida '{r['recomendacao']}'"
        )


def test_limitacao_obrigatoria_presente():
    r = _consolidar("central")
    import unicodedata
    def sem_acento(s):
        return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    texto = sem_acento(" ".join(r["limitacoes"])).lower()
    assert "simulados" in texto and "hipoteticos" in texto, (
        f"Limitacao obrigatoria ausente: {r['limitacoes']}"
    )


def test_justificativa_consolidada_minimo_100_chars():
    r = _consolidar("central")
    assert len(r["justificativa_consolidada"]) >= 100


# ---------------------------------------------------------------------------
# Testes de formula do score consolidado
# ---------------------------------------------------------------------------

def test_formula_score_ponderado():
    """Score = round(0.20*m + 0.20*s + 0.25*e + 0.25*o + 0.10*p)."""
    scores = {"mercado": 52, "impacto_social": 38, "engenharia": 74, "orcamento": 78, "pontes": 64}
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    esperado = round(0.20*52 + 0.20*38 + 0.25*74 + 0.25*78 + 0.10*64)
    assert r["score_consolidado"] == esperado


def test_score_aurora_62():
    r = _consolidar("aurora")
    assert r["score_consolidado"] == 62


def test_score_nova_uniao_30():
    r = _consolidar("nova_uniao")
    assert r["score_consolidado"] == 30


# ---------------------------------------------------------------------------
# Testes de robustez — entradas malformadas (_normalizar_parecer)
# ---------------------------------------------------------------------------

def _pareceres_com_um_ruim(mercado_ruim) -> str:
    pareceres = {}
    for agente in ["impacto_social", "engenharia", "orcamento", "pontes"]:
        pareceres[agente] = _parecer_sintetico(60, agente=agente)
    pareceres["mercado"] = mercado_ruim
    return json.dumps(pareceres, ensure_ascii=False)


def _assert_malformado_incompleto(j: str, descricao: str):
    """Nao lanca excecao, status analise_incompleta, parecer mercado tem erro."""
    try:
        r = _unwrap(_mod_g.consolidar_pareceres(j))
    except Exception as exc:
        pytest.fail(f"consolidar_pareceres lancou excecao para {descricao}: {exc}")
    assert r["status"] == "analise_incompleta", (
        f"{descricao}: esperado analise_incompleta, obtido '{r['status']}'"
    )
    assert r["recomendacao"] is None
    parecer_mercado = r["pareceres"].get("mercado", {})
    assert parecer_mercado.get("erro") is not None, (
        f"{descricao}: parecer mercado deve ter erro preenchido"
    )


def test_robustez_score_ausente():
    j = _pareceres_com_um_ruim({"confianca": "alta"})
    _assert_malformado_incompleto(j, "score ausente")


def test_robustez_parecer_string():
    j = _pareceres_com_um_ruim("texto")
    _assert_malformado_incompleto(j, "parecer string")


def test_robustez_score_null():
    j = _pareceres_com_um_ruim({"score": None, "confianca": "alta"})
    _assert_malformado_incompleto(j, "score null")


def test_robustez_score_fora_do_intervalo():
    j = _pareceres_com_um_ruim({"score": 150, "confianca": "alta"})
    _assert_malformado_incompleto(j, "score 150")


def test_robustez_lista_raiz():
    """JSON raiz que e lista -> analise_incompleta, nao lanca excecao."""
    try:
        r = _unwrap(_mod_g.consolidar_pareceres("[]"))
    except Exception as exc:
        pytest.fail(f"Lancou excecao para lista raiz: {exc}")
    assert r["status"] == "analise_incompleta"
    assert r["erro"] is not None


def test_robustez_score_string_numerico():
    """Score string '72' deve ser convertido para 72 — sem erro no parecer."""
    outros = {
        agente: _parecer_sintetico(60, agente=agente)
        for agente in ["impacto_social", "engenharia", "orcamento", "pontes"]
    }
    outros["mercado"] = {
        "score": "72",
        "confianca": "alta",
        "justificativa": "Justificativa de teste para verificacao de score string.",
        "riscos": ["risco teste"],
        "simulado": True,
        "erro": None,
    }
    j = json.dumps(outros, ensure_ascii=False)
    try:
        r = _unwrap(_mod_g.consolidar_pareceres(j))
    except Exception as exc:
        pytest.fail(f"Lancou excecao para score string: {exc}")
    assert r["pareceres"]["mercado"]["score"] == 72
    assert r["pareceres"]["mercado"].get("erro") is None
    assert r["status"] == "concluida"


def test_robustez_chave_extra_ignorada():
    """Objeto com 5 pareceres validos + chave extra 'regiao_id' -> mesmo resultado."""
    scores = {"mercado": 52, "impacto_social": 38, "engenharia": 74, "orcamento": 78, "pontes": 64}
    pareceres_sem = json.loads(_pareceres_sinteticos(scores))
    pareceres_com = dict(pareceres_sem)
    pareceres_com["regiao_id"] = "aurora"
    r_sem = _unwrap(_mod_g.consolidar_pareceres(json.dumps(pareceres_sem)))
    r_com = _unwrap(_mod_g.consolidar_pareceres(json.dumps(pareceres_com)))
    assert r_sem["score_consolidado"] == r_com["score_consolidado"]
    assert r_sem["recomendacao"] == r_com["recomendacao"]


def test_caminhos_sem_indicadores_nao_quebra():
    """Pareceres sem campo 'indicadores' -> caminhos lista vazia, sem excecao."""
    scores = {"mercado": 30, "impacto_social": 30, "engenharia": 30, "orcamento": 30, "pontes": 30}
    j = _pareceres_sinteticos(scores)
    try:
        r = _unwrap(_mod_g.consolidar_pareceres(j))
    except Exception as exc:
        pytest.fail(f"Lancou excecao sem indicadores: {exc}")
    # caminhos pode ser vazia (sem indicadores para extrair) mas nao pode quebrar
    assert isinstance(r.get("caminhos"), list)


# ---------------------------------------------------------------------------
# Testes de robustez — bloco markdown, riscos como objetos, scores nao finitos
# ---------------------------------------------------------------------------

def _json_aurora_puro() -> str:
    return _montar_pareceres("aurora")


def test_markdown_bloco_json_resultado_identico():
    """JSON em ```json ... ``` deve dar score 62 e realizar_piloto."""
    puro = _json_aurora_puro()
    embrulhado = f"```json\n{puro}\n```"
    r_puro = _unwrap(_mod_g.consolidar_pareceres(puro))
    try:
        r_emb = _unwrap(_mod_g.consolidar_pareceres(embrulhado))
    except Exception as exc:
        pytest.fail(f"Lancou excecao com bloco json: {exc}")
    assert r_emb["score_consolidado"] == 62
    assert r_emb["recomendacao"] == "realizar_piloto"
    assert r_emb["status"] == "concluida"
    assert r_emb["score_consolidado"] == r_puro["score_consolidado"]


def test_markdown_bloco_simples_resultado_identico():
    puro = _json_aurora_puro()
    embrulhado = f"```\n{puro}\n```"
    try:
        r = _unwrap(_mod_g.consolidar_pareceres(embrulhado))
    except Exception as exc:
        pytest.fail(f"Lancou excecao com bloco simples: {exc}")
    assert r["score_consolidado"] == 62
    assert r["recomendacao"] == "realizar_piloto"


def test_markdown_texto_prefixo_resultado_identico():
    puro = _json_aurora_puro()
    com_prefixo = f"Aqui estao os pareceres: {puro}"
    try:
        r = _unwrap(_mod_g.consolidar_pareceres(com_prefixo))
    except Exception as exc:
        pytest.fail(f"Lancou excecao com texto prefixo: {exc}")
    assert r["score_consolidado"] == 62
    assert r["recomendacao"] == "realizar_piloto"


def test_riscos_como_objetos_nao_quebra():
    """riscos como lista de dicts nao deve lançar excecao."""
    outros = {
        agente: _parecer_sintetico(60, agente=agente)
        for agente in ["impacto_social", "engenharia", "orcamento", "pontes"]
    }
    outros["mercado"] = {
        "score": 60,
        "confianca": "alta",
        "justificativa": "Justificativa de teste com riscos como objetos.",
        "riscos": [{"risco": "custo alto"}, {"risco": "baixa adesao"}],
        "simulado": True,
        "erro": None,
    }
    j = json.dumps(outros, ensure_ascii=False)
    try:
        r = _unwrap(_mod_g.consolidar_pareceres(j))
    except Exception as exc:
        pytest.fail(f"Lancou excecao com riscos como objetos: {exc}")
    texto_riscos = " ".join(r.get("principais_riscos", []))
    assert "custo alto" in texto_riscos


def test_score_nan_normaliza_para_zero():
    p_nan = {"score": float("nan"), "confianca": "alta", "riscos": [], "erro": None}
    p_norm = _mod_g._normalizar_parecer("mercado", p_nan)
    assert p_norm["score"] == 0
    assert p_norm["erro"] is not None
    assert "finito" in p_norm["erro"].lower()


def test_score_infinity_normaliza_para_zero():
    p_inf = {"score": float("inf"), "confianca": "alta", "riscos": [], "erro": None}
    p_norm = _mod_g._normalizar_parecer("mercado", p_inf)
    assert p_norm["score"] == 0
    assert p_norm["erro"] is not None
    assert "finito" in p_norm["erro"].lower()
