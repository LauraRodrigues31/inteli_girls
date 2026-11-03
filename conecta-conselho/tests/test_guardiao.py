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


# ---------------------------------------------------------------------------
# Testes de recomendacao esperada para as 6 regioes
# (aurora 62 realizar_piloto | horizonte 57 realizar_piloto |
#  esperanca 44 aguardar | central 60 realizar_piloto |
#  vale_verde 60 realizar_piloto | nova_uniao 30 escalar)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("regiao_id,score_esp,rec_esp", [
    ("aurora",     62, "realizar_piloto"),
    ("horizonte",  57, "realizar_piloto"),
    ("esperanca",  44, "aguardar"),
    ("central",    60, "realizar_piloto"),
    ("vale_verde", 60, "realizar_piloto"),
    ("nova_uniao", 30, "escalar"),
])
def test_score_e_recomendacao_esperados(regiao_id, score_esp, rec_esp):
    r = _consolidar(regiao_id)
    assert r["score_consolidado"] == score_esp, (
        f"{regiao_id}: score esperado {score_esp}, obtido {r['score_consolidado']}"
    )
    assert r["recomendacao"] == rec_esp, (
        f"{regiao_id}: recomendacao esperada '{rec_esp}', obtida '{r['recomendacao']}'"
    )


# ---------------------------------------------------------------------------
# Testes de limiares exatos (29/30, 49/50, 69/70)
# ---------------------------------------------------------------------------

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


def test_limiar_29_escalar():
    """Score consolidado 29 deve resultar em 'escalar'."""
    # m=30, s=30, e=30, o=26, p=30 -> round(0.20*30+0.20*30+0.25*30+0.25*26+0.10*30) = round(29.5)=30? ajusta
    # Vamos calcular direto: precisamos exatamente 29
    # 0.20*a + 0.20*b + 0.25*c + 0.25*d + 0.10*e = 29 com todos >=20
    # Usa: m=30, s=30, e=25, o=25, p=30 -> 6+6+6.25+6.25+3 = 27.5 -> 28; ajusta
    # m=30, s=30, e=30, o=25, p=30 -> 6+6+7.5+6.25+3 = 28.75 -> 29 ✓
    scores = {"mercado": 30, "impacto_social": 30, "engenharia": 30, "orcamento": 25, "pontes": 30}
    assert _score_sintetico(scores) == 29
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["score_consolidado"] == 29
    assert r["recomendacao"] == "escalar"


def test_limiar_30_aguardar():
    """Score consolidado 30 SEM eng<20 nem orc<20 deve ser 'aguardar'."""
    # m=30, s=30, e=30, o=30, p=30 -> 6+6+7.5+7.5+3 = 30 ✓
    scores = {"mercado": 30, "impacto_social": 30, "engenharia": 30, "orcamento": 30, "pontes": 30}
    assert _score_sintetico(scores) == 30
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["score_consolidado"] == 30
    assert r["recomendacao"] == "aguardar"


def test_limiar_49_aguardar():
    """Score consolidado 49 deve ser 'aguardar'."""
    # m=50, s=50, e=49, o=49, p=45
    # 10+10+12.25+12.25+4.5 = 49 ✓
    scores = {"mercado": 50, "impacto_social": 50, "engenharia": 49, "orcamento": 49, "pontes": 45}
    assert _score_sintetico(scores) == 49
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["score_consolidado"] == 49
    assert r["recomendacao"] == "aguardar"


def test_limiar_50_realizar_piloto():
    """Score consolidado 50 deve ser 'realizar_piloto'."""
    # m=50, s=50, e=50, o=50, p=50 -> 10+10+12.5+12.5+5 = 50 ✓
    scores = {"mercado": 50, "impacto_social": 50, "engenharia": 50, "orcamento": 50, "pontes": 50}
    assert _score_sintetico(scores) == 50
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["score_consolidado"] == 50
    assert r["recomendacao"] == "realizar_piloto"


def test_limiar_69_realizar_piloto():
    """Score 69, eng>=60, orc>=60 -> NAO atinge 70 -> realizar_piloto."""
    # m=70, s=70, e=69, o=69, p=65
    # 14+14+17.25+17.25+6.5 = 69 ✓
    scores = {"mercado": 70, "impacto_social": 70, "engenharia": 69, "orcamento": 69, "pontes": 65}
    assert _score_sintetico(scores) == 69
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["score_consolidado"] == 69
    assert r["recomendacao"] == "realizar_piloto"


def test_limiar_70_investir_agora():
    """Score 70, eng>=60, orc>=60 -> 'investir_agora'."""
    # m=70, s=70, e=70, o=70, p=70 -> 14+14+17.5+17.5+7 = 70 ✓
    scores = {"mercado": 70, "impacto_social": 70, "engenharia": 70, "orcamento": 70, "pontes": 70}
    assert _score_sintetico(scores) == 70
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["score_consolidado"] == 70
    assert r["recomendacao"] == "investir_agora"


# ---------------------------------------------------------------------------
# Testes das divergencias
# ---------------------------------------------------------------------------

def test_divergencia_social_vs_orcamento():
    """Diferenca > 30 entre impacto_social e orcamento gera divergencia."""
    scores = {"mercado": 50, "impacto_social": 90, "engenharia": 50, "orcamento": 55, "pontes": 50}
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert any("impacto_social" in d or "impacto social" in d.lower() for d in r["divergencias"]), (
        f"Divergencia social/orcamento nao detectada: {r['divergencias']}"
    )


def test_divergencia_engenharia_baixa_mercado_alto():
    """Engenharia < 40 e mercado > 60 gera divergencia tecnica."""
    scores = {"mercado": 70, "impacto_social": 50, "engenharia": 30, "orcamento": 50, "pontes": 50}
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert any("engenharia" in d.lower() or "tecnica" in d.lower() for d in r["divergencias"]), (
        f"Divergencia engenharia/mercado nao detectada: {r['divergencias']}"
    )


def test_divergencia_pontes_alto_orcamento_baixo():
    """Pontes > 70 e orcamento < 40 gera divergencia de cofinanciamento."""
    scores = {"mercado": 50, "impacto_social": 50, "engenharia": 50, "orcamento": 30, "pontes": 80}
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert any("pontes" in d.lower() or "parceria" in d.lower() or "cofinanciamento" in d.lower()
               for d in r["divergencias"]), (
        f"Divergencia pontes/orcamento nao detectada: {r['divergencias']}"
    )


def test_sem_divergencias_scores_equilibrados():
    """Scores equilibrados nao devem gerar divergencias."""
    scores = {"mercado": 60, "impacto_social": 60, "engenharia": 60, "orcamento": 60, "pontes": 60}
    j = _pareceres_sinteticos(scores)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    # Nenhuma das 3 regras ativa; sem erro: sem divergencias
    assert r["divergencias"] == []


# ---------------------------------------------------------------------------
# Testes de parecer com erro
# ---------------------------------------------------------------------------

def test_parecer_com_erro_gera_escalar():
    """Qualquer parecer com erro != null deve forcar recomendacao 'escalar'."""
    scores = {"mercado": 60, "impacto_social": 60, "engenharia": 60, "orcamento": 60, "pontes": 60}
    j = _pareceres_sinteticos(scores, erros={"engenharia": "Regiao nao encontrada"})
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["recomendacao"] == "escalar"


def test_parecer_com_erro_registrado_em_divergencias():
    """Parecer com erro deve aparecer no campo divergencias."""
    scores = {"mercado": 50, "impacto_social": 50, "engenharia": 50, "orcamento": 50, "pontes": 50}
    j = _pareceres_sinteticos(scores, erros={"mercado": "Falha ao consultar dados"})
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert any("mercado" in d.lower() for d in r["divergencias"])


def test_confianca_baixa_gera_escalar():
    """Parecer com confianca 'baixa' deve forcar recomendacao 'escalar'."""
    pareceres = {}
    for agente in ["mercado", "impacto_social", "engenharia", "orcamento", "pontes"]:
        p = _parecer_sintetico(60, agente=agente)
        if agente == "orcamento":
            p["confianca"] = "baixa"
        pareceres[agente] = p
    j = json.dumps(pareceres)
    r = _unwrap(_mod_g.consolidar_pareceres(j))
    assert r["recomendacao"] == "escalar"


# ---------------------------------------------------------------------------
# Testes de JSON invalido
# ---------------------------------------------------------------------------

def test_json_invalido_retorna_erro():
    """String nao-JSON deve retornar erro nao nulo."""
    r = _unwrap(_mod_g.consolidar_pareceres("isso nao e json {{{"))
    assert r["erro"] is not None
    assert r["score_consolidado"] == 0


def test_json_lista_retorna_erro():
    """JSON que e lista (nao objeto) deve retornar erro."""
    r = _unwrap(_mod_g.consolidar_pareceres("[1, 2, 3]"))
    assert r["erro"] is not None


def test_json_vazio_trata_agentes_ausentes():
    """JSON objeto vazio deve tratar todos os agentes como ausentes (score 0)."""
    r = _unwrap(_mod_g.consolidar_pareceres("{}"))
    assert r["score_consolidado"] == 0
    assert r["recomendacao"] == "escalar"
    assert r["erro"] is None  # nao e erro de parse, apenas agentes ausentes


# ---------------------------------------------------------------------------
# Testes de estrutura e campos obrigatorios
# ---------------------------------------------------------------------------

def test_campos_obrigatorios_presentes():
    r = _consolidar("central")
    campos = [
        "agente", "regiao_id", "regiao_nome", "recomendacao", "score_consolidado",
        "pareceres", "divergencias", "justificativa_consolidada",
        "principais_riscos", "principais_oportunidades", "limitacoes", "simulado", "erro",
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
        assert isinstance(r["score_consolidado"], int), f"Score nao inteiro em {rid}"
        assert 0 <= r["score_consolidado"] <= 100, f"Score fora do intervalo em {rid}"


def test_recomendacao_valores_validos():
    validos = {"investir_agora", "realizar_piloto", "aguardar", "escalar"}
    for rid in ["aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"]:
        r = _consolidar(rid)
        assert r["recomendacao"] in validos, f"{rid}: recomendacao invalida '{r['recomendacao']}'"


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


def test_nova_uniao_recomendacao_escalar():
    """Nova Uniao: orcamento=0 < 20 -> forcado para 'escalar'."""
    r = _consolidar("nova_uniao")
    assert r["recomendacao"] == "escalar"


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
    """Aurora deve ter score_consolidado == 62."""
    r = _consolidar("aurora")
    assert r["score_consolidado"] == 62


def test_score_nova_uniao_30():
    """Nova Uniao deve ter score_consolidado == 30."""
    r = _consolidar("nova_uniao")
    assert r["score_consolidado"] == 30


# ---------------------------------------------------------------------------
# Testes de robustez — entradas malformadas (_normalizar_parecer)
# ---------------------------------------------------------------------------

def _pareceres_com_um_ruim(mercado_ruim) -> str:
    """5 pareceres validos exceto mercado que recebe o valor indicado."""
    pareceres = {}
    for agente in ["impacto_social", "engenharia", "orcamento", "pontes"]:
        pareceres[agente] = _parecer_sintetico(60, agente=agente)
    pareceres["mercado"] = mercado_ruim
    return json.dumps(pareceres, ensure_ascii=False)


def _assert_malformado_escalar(j: str, descricao: str):
    """Nao lanca excecao, recomendacao escalar, parecer mercado tem erro."""
    try:
        r = _unwrap(_mod_g.consolidar_pareceres(j))
    except Exception as exc:
        pytest.fail(f"consolidar_pareceres lancou excecao para {descricao}: {exc}")
    assert r["recomendacao"] == "escalar", (
        f"{descricao}: esperado 'escalar', obtido '{r['recomendacao']}'"
    )
    parecer_mercado = r["pareceres"].get("mercado", {})
    assert parecer_mercado.get("erro") is not None, (
        f"{descricao}: parecer mercado deve ter erro preenchido"
    )


def test_robustez_score_ausente():
    """Parecer sem campo score -> score 0, erro preenchido, recomendacao escalar."""
    j = _pareceres_com_um_ruim({"confianca": "alta"})
    _assert_malformado_escalar(j, "score ausente")


def test_robustez_parecer_string():
    """Parecer que e string (nao dict) -> erro, escalar."""
    j = _pareceres_com_um_ruim("texto")
    _assert_malformado_escalar(j, "parecer string")


def test_robustez_score_null():
    """Parecer com score null -> score 0, erro, escalar."""
    j = _pareceres_com_um_ruim({"score": None, "confianca": "alta"})
    _assert_malformado_escalar(j, "score null")


def test_robustez_score_fora_do_intervalo():
    """Parecer com score 150 -> score 0, erro, escalar."""
    j = _pareceres_com_um_ruim({"score": 150, "confianca": "alta"})
    _assert_malformado_escalar(j, "score 150")


def test_robustez_lista_raiz():
    """JSON raiz que e lista -> erro no resultado, nao lanca excecao."""
    try:
        r = _unwrap(_mod_g.consolidar_pareceres("[]"))
    except Exception as exc:
        pytest.fail(f"consolidar_pareceres lancou excecao para lista raiz: {exc}")
    assert r["erro"] is not None
    assert r["recomendacao"] == "escalar"


def test_robustez_score_string_numerico():
    """Score como string numerica '72' deve ser convertido para 72, sem erro."""
    outros = {
        agente: _parecer_sintetico(60, agente=agente)
        for agente in ["impacto_social", "engenharia", "orcamento", "pontes"]
    }
    outros["mercado"] = {
        "score": "72",
        "confianca": "alta",
        "justificativa": "Justificativa de teste para verificacao de score string.",
        "riscos": ["risco teste"],
        "limitacoes": ["dado simulado"],
        "simulado": True,
        "erro": None,
    }
    j = json.dumps(outros, ensure_ascii=False)
    try:
        r = _unwrap(_mod_g.consolidar_pareceres(j))
    except Exception as exc:
        pytest.fail(f"consolidar_pareceres lancou excecao para score string: {exc}")
    assert r["pareceres"]["mercado"]["score"] == 72, (
        f"Score string '72' deveria ser convertido para 72, obtido {r['pareceres']['mercado']['score']}"
    )
    assert r["pareceres"]["mercado"].get("erro") is None, (
        "Score string numerico valido nao deve gerar erro"
    )


def test_robustez_chave_extra_ignorada():
    """Objeto com os 5 pareceres + chave extra 'regiao_id' deve dar mesmo resultado."""
    scores = {"mercado": 52, "impacto_social": 38, "engenharia": 74, "orcamento": 78, "pontes": 64}
    pareceres_sem = json.loads(_pareceres_sinteticos(scores))
    pareceres_com = dict(pareceres_sem)
    pareceres_com["regiao_id"] = "aurora"  # chave extra que nao e agente

    r_sem = _unwrap(_mod_g.consolidar_pareceres(json.dumps(pareceres_sem)))
    r_com = _unwrap(_mod_g.consolidar_pareceres(json.dumps(pareceres_com)))

    assert r_sem["score_consolidado"] == r_com["score_consolidado"], (
        "Chave extra nao deve alterar score_consolidado"
    )
    assert r_sem["recomendacao"] == r_com["recomendacao"], (
        "Chave extra nao deve alterar recomendacao"
    )


# ---------------------------------------------------------------------------
# Testes de robustez — bloco markdown, riscos como objetos, scores nao finitos
# ---------------------------------------------------------------------------

def _json_aurora_puro() -> str:
    """Retorna o JSON dos 5 pareceres da aurora (montado pelas tools reais)."""
    return _montar_pareceres("aurora")


def test_markdown_bloco_json_resultado_identico():
    """JSON embrulhado em ```json ... ``` deve dar score 62 e realizar_piloto."""
    puro = _json_aurora_puro()
    embrulhado = f"```json\n{puro}\n```"
    r_puro = _unwrap(_mod_g.consolidar_pareceres(puro))
    try:
        r_emb = _unwrap(_mod_g.consolidar_pareceres(embrulhado))
    except Exception as exc:
        pytest.fail(f"Lancou excecao com bloco ```json: {exc}")
    assert r_emb["score_consolidado"] == 62
    assert r_emb["recomendacao"] == "realizar_piloto"
    assert r_emb["erro"] is None
    assert r_emb["score_consolidado"] == r_puro["score_consolidado"]


def test_markdown_bloco_simples_resultado_identico():
    """JSON embrulhado em ``` ... ``` (sem 'json') deve dar mesmo resultado."""
    puro = _json_aurora_puro()
    embrulhado = f"```\n{puro}\n```"
    try:
        r = _unwrap(_mod_g.consolidar_pareceres(embrulhado))
    except Exception as exc:
        pytest.fail(f"Lancou excecao com bloco ```: {exc}")
    assert r["score_consolidado"] == 62
    assert r["recomendacao"] == "realizar_piloto"
    assert r["erro"] is None


def test_markdown_texto_prefixo_resultado_identico():
    """JSON precedido de texto livre deve dar mesmo resultado."""
    puro = _json_aurora_puro()
    com_prefixo = f"Aqui estao os pareceres: {puro}"
    try:
        r = _unwrap(_mod_g.consolidar_pareceres(com_prefixo))
    except Exception as exc:
        pytest.fail(f"Lancou excecao com texto prefixo: {exc}")
    assert r["score_consolidado"] == 62
    assert r["recomendacao"] == "realizar_piloto"
    assert r["erro"] is None


def test_riscos_como_objetos_nao_quebra():
    """riscos como lista de dicts nao deve lançar excecao e texto deve aparecer."""
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
    # "custo alto" deve aparecer em principais_riscos
    texto_riscos = " ".join(r.get("principais_riscos", []))
    assert "custo alto" in texto_riscos, (
        f"'custo alto' nao encontrado em principais_riscos: {r.get('principais_riscos')}"
    )


def test_score_nan_escalar_com_erro():
    """Score NaN (aceito pelo json.loads) deve gerar score 0 e erro no parecer."""
    # json.loads aceita NaN em alguns contextos mas nao e JSON valido estrito;
    # testamos via float direto no normalizador
    outros = {
        agente: _parecer_sintetico(60, agente=agente)
        for agente in ["impacto_social", "engenharia", "orcamento", "pontes"]
    }
    # Simula o que chegaria: um parecer com score float('nan') apos parse
    # Usamos _normalizar_parecer diretamente pois json.loads rejeita NaN literal
    p_nan = {"score": float("nan"), "confianca": "alta", "riscos": [], "erro": None}
    p_norm = _mod_g._normalizar_parecer("mercado", p_nan)
    assert p_norm["score"] == 0
    assert p_norm["erro"] is not None
    assert "finito" in p_norm["erro"].lower()


def test_score_infinity_escalar_com_erro():
    """Score Infinity deve gerar score 0 e erro no parecer."""
    p_inf = {"score": float("inf"), "confianca": "alta", "riscos": [], "erro": None}
    p_norm = _mod_g._normalizar_parecer("mercado", p_inf)
    assert p_norm["score"] == 0
    assert p_norm["erro"] is not None
    assert "finito" in p_norm["erro"].lower()
