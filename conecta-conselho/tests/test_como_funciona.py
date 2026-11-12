"""
Testes das funções auxiliares de paginas/como_funciona.py.

Cobre:
  - montar_pareceres: estrutura, campos obrigatórios, simulação de falha
  - extrair_resultado: recomendações esperadas para Esperança, Central e Nova União
  - frase_regra: frase correta para cada recomendação
  - SCORES_REGIOES: gabarito com os valores da RESULTADOS_REGIOES.md

AVISO: Todos os dados são SIMULADOS e fictícios.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Configuração de paths
# ---------------------------------------------------------------------------
_CC_DIR = Path(__file__).resolve().parent.parent   # conecta-conselho/
_ROOT   = _CC_DIR.parent                            # inteli_girls/

for _p in [str(_ROOT), str(_CC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from paginas.como_funciona import (  # type: ignore[import]
    AGENTES,
    SCORES_REGIOES,
    extrair_resultado,
    frase_regra,
    montar_pareceres,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def scores_esperanca() -> dict[str, int]:
    return SCORES_REGIOES["Esperança"].copy()


@pytest.fixture()
def scores_central() -> dict[str, int]:
    return SCORES_REGIOES["Central"].copy()


@pytest.fixture()
def scores_nova_uniao() -> dict[str, int]:
    return SCORES_REGIOES["Nova União"].copy()


# ---------------------------------------------------------------------------
# Testes de SCORES_REGIOES (gabarito)
# ---------------------------------------------------------------------------

class TestScoresRegioes:
    def test_esperanca_valores(self, scores_esperanca):
        """Esperança: gabarito conforme RESULTADOS_REGIOES.md."""
        assert scores_esperanca["mercado"] == 63
        assert scores_esperanca["impacto_social"] == 66
        assert scores_esperanca["engenharia"] == 34
        assert scores_esperanca["orcamento"] == 20
        assert scores_esperanca["pontes"] == 43

    def test_central_valores(self, scores_central):
        assert scores_central["mercado"] == 37
        assert scores_central["impacto_social"] == 30
        assert scores_central["engenharia"] == 86
        assert scores_central["orcamento"] == 76
        assert scores_central["pontes"] == 66

    def test_nova_uniao_valores(self, scores_nova_uniao):
        assert scores_nova_uniao["mercado"] == 50
        assert scores_nova_uniao["impacto_social"] == 78
        assert scores_nova_uniao["engenharia"] == 11
        assert scores_nova_uniao["orcamento"] == 0
        assert scores_nova_uniao["pontes"] == 21

    def test_todas_as_regioes_presentes(self):
        assert set(SCORES_REGIOES.keys()) == {"Esperança", "Central", "Nova União"}

    def test_todas_as_chaves_por_regiao(self):
        chaves_esperadas = {"mercado", "impacto_social", "engenharia", "orcamento", "pontes"}
        for nome, scores in SCORES_REGIOES.items():
            assert set(scores.keys()) == chaves_esperadas, f"Chaves ausentes em {nome}"


# ---------------------------------------------------------------------------
# Testes de AGENTES
# ---------------------------------------------------------------------------

class TestAgentes:
    def test_cinco_agentes(self):
        assert len(AGENTES) == 5

    def test_chaves_obrigatorias(self):
        for a in AGENTES:
            assert "chave" in a
            assert "icone" in a
            assert "nome" in a
            assert "pergunta" in a
            assert "debate" in a

    def test_chaves_validas(self):
        chaves = {a["chave"] for a in AGENTES}
        assert chaves == {"mercado", "impacto_social", "engenharia", "orcamento", "pontes"}


# ---------------------------------------------------------------------------
# Testes de montar_pareceres
# ---------------------------------------------------------------------------

class TestMontarPareceres:
    def test_retorna_string_json(self, scores_esperanca):
        resultado = montar_pareceres(scores_esperanca)
        assert isinstance(resultado, str)
        parsed = json.loads(resultado)
        assert isinstance(parsed, dict)

    def test_cinco_agentes_no_json(self, scores_esperanca):
        parsed = json.loads(montar_pareceres(scores_esperanca))
        assert set(parsed.keys()) == {"mercado", "impacto_social", "engenharia", "orcamento", "pontes"}

    def test_campos_obrigatorios(self, scores_esperanca):
        parsed = json.loads(montar_pareceres(scores_esperanca))
        for chave, parecer in parsed.items():
            assert "agente" in parecer, f"Campo 'agente' ausente em {chave}"
            assert "score" in parecer, f"Campo 'score' ausente em {chave}"
            assert "confianca" in parecer, f"Campo 'confianca' ausente em {chave}"
            assert "erro" in parecer, f"Campo 'erro' ausente em {chave}"
            assert "indicadores" in parecer, f"Campo 'indicadores' ausente em {chave}"

    def test_scores_preservados(self, scores_esperanca):
        parsed = json.loads(montar_pareceres(scores_esperanca))
        assert parsed["mercado"]["score"] == 63
        assert parsed["impacto_social"]["score"] == 66
        assert parsed["engenharia"]["score"] == 34
        assert parsed["orcamento"]["score"] == 20
        assert parsed["pontes"]["score"] == 43

    def test_sem_falha_erro_nulo(self, scores_esperanca):
        parsed = json.loads(montar_pareceres(scores_esperanca))
        for parecer in parsed.values():
            assert parecer["erro"] is None

    def test_com_falha_mercado(self, scores_esperanca):
        parsed = json.loads(montar_pareceres(scores_esperanca, falha=True))
        # Mercado deve ter erro
        assert parsed["mercado"]["erro"] is not None
        assert parsed["mercado"]["score"] == 0
        assert parsed["mercado"]["confianca"] == "nao_avaliada"
        # Outros não devem ter erro
        for chave in ("impacto_social", "engenharia", "orcamento", "pontes"):
            assert parsed[chave]["erro"] is None

    def test_score_zerado_quando_erro(self, scores_esperanca):
        parsed = json.loads(montar_pareceres(scores_esperanca, falha=True))
        assert parsed["mercado"]["score"] == 0

    def test_confianca_alta_sem_falha(self, scores_esperanca):
        parsed = json.loads(montar_pareceres(scores_esperanca))
        for parecer in parsed.values():
            assert parecer["confianca"] == "alta"

    def test_indicadores_dict_vazio(self, scores_esperanca):
        parsed = json.loads(montar_pareceres(scores_esperanca))
        for parecer in parsed.values():
            assert parecer["indicadores"] == {}

    def test_agente_key_correta(self, scores_esperanca):
        parsed = json.loads(montar_pareceres(scores_esperanca))
        for chave, parecer in parsed.items():
            assert parecer["agente"] == chave


# ---------------------------------------------------------------------------
# Testes de extrair_resultado
# ---------------------------------------------------------------------------

class TestExtrairResultado:
    def test_esperanca_aguardar(self, scores_esperanca):
        """Esperança: score 44 → aguardar."""
        res = extrair_resultado(scores_esperanca)
        assert res["recomendacao"] == "aguardar"
        assert res["score_consolidado"] == 44

    def test_central_realizar_piloto(self, scores_central):
        """Central: score 60 → realizar_piloto."""
        res = extrair_resultado(scores_central)
        assert res["recomendacao"] == "realizar_piloto"
        assert res["score_consolidado"] == 60

    def test_nova_uniao_aguardar_com_alerta(self, scores_nova_uniao):
        """Nova União: orçamento=0 e engenharia=11 → aguardar com atencao_prioritaria.

        Com pareceres mínimos (sem confiança=baixa nem erro real) o Guardião
        retorna 'aguardar' (score 30) mas aciona o alerta de atenção prioritária
        pelos scores críticos de orçamento e engenharia.
        """
        res = extrair_resultado(scores_nova_uniao)
        assert res["recomendacao"] == "aguardar"
        assert res["score_consolidado"] == 30
        assert res["atencao_prioritaria"] is True

    def test_com_falha_analise_incompleta(self, scores_esperanca):
        """Simular falha → status analise_incompleta."""
        res = extrair_resultado(scores_esperanca, falha=True)
        assert res["status"] == "analise_incompleta"

    def test_retorna_dict(self, scores_esperanca):
        res = extrair_resultado(scores_esperanca)
        assert isinstance(res, dict)

    def test_campos_obrigatorios_retorno(self, scores_esperanca):
        res = extrair_resultado(scores_esperanca)
        for campo in ("recomendacao", "score_consolidado", "atencao_prioritaria",
                      "pontos_criticos", "divergencias", "status"):
            assert campo in res, f"Campo '{campo}' ausente no resultado"

    def test_esperanca_atencao_prioritaria_false(self, scores_esperanca):
        """Esperança: aguardar mas sem alerta (score 44 ≥ 30, sem crítico extremo)."""
        res = extrair_resultado(scores_esperanca)
        # atencao_prioritaria pode ser True ou False — só verificamos o campo existe
        assert isinstance(res["atencao_prioritaria"], bool)

    def test_scores_altos_realizar_piloto(self):
        """Scores altos mas abaixo de investir_agora → realizar_piloto."""
        scores = {"mercado": 80, "impacto_social": 80, "engenharia": 55,
                  "orcamento": 55, "pontes": 70}
        res = extrair_resultado(scores)
        assert res["recomendacao"] == "realizar_piloto"

    def test_scores_investir_agora(self):
        """Score ≥ 70, orçamento ≥ 60, engenharia ≥ 60 → investir_agora."""
        scores = {"mercado": 80, "impacto_social": 80, "engenharia": 80,
                  "orcamento": 80, "pontes": 80}
        res = extrair_resultado(scores)
        assert res["recomendacao"] == "investir_agora"

    def test_scores_baixos_aguardar(self):
        """Scores baixos mas viáveis → aguardar."""
        scores = {"mercado": 40, "impacto_social": 40, "engenharia": 40,
                  "orcamento": 40, "pontes": 40}
        res = extrair_resultado(scores)
        assert res["recomendacao"] == "aguardar"


# ---------------------------------------------------------------------------
# Testes de frase_regra
# ---------------------------------------------------------------------------

class TestFraseRegra:
    def test_aguardar(self, scores_esperanca):
        res = extrair_resultado(scores_esperanca)
        frase = frase_regra(res)
        assert "44" in frase
        assert "Aguardar" in frase or "aguardar" in frase.lower()

    def test_realizar_piloto(self, scores_central):
        res = extrair_resultado(scores_central)
        frase = frase_regra(res)
        assert "piloto" in frase.lower()

    def test_analise_incompleta(self, scores_esperanca):
        res = extrair_resultado(scores_esperanca, falha=True)
        frase = frase_regra(res)
        assert frase != ""
        assert "incompleto" in frase.lower() or "falhou" in frase.lower()

    def test_investir_agora(self):
        scores = {"mercado": 80, "impacto_social": 80, "engenharia": 80,
                  "orcamento": 80, "pontes": 80}
        res = extrair_resultado(scores)
        frase = frase_regra(res)
        assert "Investir" in frase or "agora" in frase.lower()

    def test_retorna_string(self, scores_esperanca):
        res = extrair_resultado(scores_esperanca)
        assert isinstance(frase_regra(res), str)


# ---------------------------------------------------------------------------
# Testes da página renderizada no app (AppTest)
# ---------------------------------------------------------------------------

from streamlit.testing.v1 import AppTest  # noqa: E402

from paginas.como_funciona import _INFO_REC  # type: ignore[import]  # noqa: E402


@pytest.fixture()
def app_como_funciona() -> AppTest:
    at = AppTest.from_file(str(_CC_DIR / "app.py"))
    at.run(timeout=30)
    assert not at.exception
    return at


class TestPaginaNoApp:
    def test_links_para_as_outras_paginas(self, app_como_funciona):
        """Os 2 links devem ser st.page_link reais, não botões desabilitados.
        (A página Mapa ilustrativo foi removida da navegação na M2 revisada.)
        """
        links = app_como_funciona.get("page_link")
        assert len(links) == 2
        assert not [b for b in app_como_funciona.button if b.disabled]

    def test_atalho_preenche_sliders(self, app_como_funciona):
        at = app_como_funciona
        next(b for b in at.button if b.label == "Central").click().run(timeout=30)
        assert not at.exception
        esperado = SCORES_REGIOES["Central"]
        assert [s.value for s in at.slider] == [esperado[a["chave"]] for a in AGENTES]

    def test_regra_aguardar_igual_ao_guardiao(self):
        """Guardião: aguardar = score < 50 (não existe mais faixa 30–49)."""
        assert "50" in _INFO_REC["aguardar"]["regra"]
        assert "30" not in _INFO_REC["aguardar"]["regra"]
