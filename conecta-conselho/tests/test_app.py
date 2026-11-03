"""
Testes de integração para conecta-conselho/integracao.py.

Testa:
  - Contrato da saída de chamar_guardiao (campos obrigatórios, tipos, valores válidos)
  - Todas as 6 regiões executam sem exceção
  - Campos do contrato do Guardião (Seção 11)
  - Score consolidado entre 0 e 100
  - Recomendação sempre um dos quatro valores válidos
  - Divergências é lista (pode ser vazia)
  - Região inexistente retorna erro, não levanta exceção
  - Score consolidado é calculado com os pesos corretos

AVISO: Todos os dados são SIMULADOS e fictícios.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Garante que os módulos são encontrados ao executar via pytest
_CC_DIR = Path(__file__).resolve().parent.parent          # conecta-conselho/
_ROOT   = _CC_DIR.parent                                   # inteli_girls/

for _p in [str(_ROOT), str(_CC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

from integracao import chamar_guardiao, _calcular_score_consolidado, _PESOS

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

IDS_VALIDOS = ["aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"]

RECOMENDACOES_VALIDAS = {"investir_agora", "realizar_piloto", "aguardar", "escalar"}

CAMPOS_OBRIGATORIOS = [
    "agente",
    "regiao_id",
    "regiao_nome",
    "recomendacao",
    "score_consolidado",
    "pareceres",
    "divergencias",
    "justificativa_consolidada",
    "principais_riscos",
    "principais_oportunidades",
    "limitacoes",
    "simulado",
    "erro",
]

AGENTES_ESPECIALISTAS = [
    "mercado",
    "impacto_social",
    "engenharia",
    "orcamento",
    "pontes",
]

# O Guardiao real retorna apenas score, confianca, justificativa e erro no resumo de pareceres.
# riscos e limitacoes sao opcionais (presentes na versao local legada, ausentes no Guardiao real).
CAMPOS_PARECER = ["score", "confianca", "justificativa"]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def resultados_todas_regioes():
    """Cache de resultados para evitar reexecução por teste."""
    return {rid: chamar_guardiao(rid) for rid in IDS_VALIDOS}


# ---------------------------------------------------------------------------
# Testes de contrato — campos obrigatórios
# ---------------------------------------------------------------------------


class TestContratoSaida:
    """Valida que a saída de chamar_guardiao respeita o contrato da Seção 11."""

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_todos_campos_obrigatorios_presentes(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        for campo in CAMPOS_OBRIGATORIOS:
            assert campo in resultado, (
                f"Campo obrigatório '{campo}' ausente para região '{regiao_id}'"
            )

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_agente_e_guardiao(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        assert resultado["agente"] == "guardiao"

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_regiao_id_retornada_corretamente(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        assert resultado["regiao_id"] == regiao_id

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_regiao_nome_nao_nulo(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        assert resultado["regiao_nome"] is not None
        assert isinstance(resultado["regiao_nome"], str)
        assert len(resultado["regiao_nome"]) > 0

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_simulado_sempre_true(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        assert resultado["simulado"] is True

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_erro_nulo_para_regioes_validas(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        assert resultado["erro"] is None, (
            f"Erro inesperado para região válida '{regiao_id}': {resultado['erro']}"
        )


# ---------------------------------------------------------------------------
# Testes de tipos e valores
# ---------------------------------------------------------------------------


class TestTiposValores:
    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_score_consolidado_e_inteiro(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        assert isinstance(resultado["score_consolidado"], int)

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_score_consolidado_entre_0_e_100(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        sc = resultado["score_consolidado"]
        assert 0 <= sc <= 100, f"Score {sc} fora do intervalo para '{regiao_id}'"

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_recomendacao_valor_valido(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        assert resultado["recomendacao"] in RECOMENDACOES_VALIDAS, (
            f"Recomendação inválida '{resultado['recomendacao']}' para '{regiao_id}'"
        )

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_divergencias_e_lista(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        assert isinstance(resultado["divergencias"], list)

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_principais_riscos_e_lista(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        assert isinstance(resultado["principais_riscos"], list)

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_principais_oportunidades_e_lista(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        assert isinstance(resultado["principais_oportunidades"], list)

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_limitacoes_e_lista_nao_vazia(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        assert isinstance(resultado["limitacoes"], list)
        assert len(resultado["limitacoes"]) >= 1

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_limitacoes_contem_aviso_mvp(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        texto_esperado = "dados simulados"
        assert any(
            texto_esperado in lim.lower() for lim in resultado["limitacoes"]
        ), f"Limitação de dados simulados ausente para '{regiao_id}'"

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_justificativa_consolidada_e_string(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        just = resultado["justificativa_consolidada"]
        assert isinstance(just, str)
        assert len(just) >= 100, (
            f"Justificativa muito curta ({len(just)} chars) para '{regiao_id}'"
        )


# ---------------------------------------------------------------------------
# Testes dos pareceres dos 5 agentes
# ---------------------------------------------------------------------------


class TestPareceres:
    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_pareceres_tem_5_agentes(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        pareceres = resultado["pareceres"]
        for agente in AGENTES_ESPECIALISTAS:
            assert agente in pareceres, (
                f"Parecer do agente '{agente}' ausente para região '{regiao_id}'"
            )

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    @pytest.mark.parametrize("agente", AGENTES_ESPECIALISTAS)
    def test_parecer_tem_campos_obrigatorios(self, regiao_id, agente):
        resultado = chamar_guardiao(regiao_id)
        parecer = resultado["pareceres"][agente]
        for campo in CAMPOS_PARECER:
            assert campo in parecer, (
                f"Campo '{campo}' ausente no parecer do agente '{agente}' para '{regiao_id}'"
            )

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    @pytest.mark.parametrize("agente", AGENTES_ESPECIALISTAS)
    def test_score_especialista_entre_0_e_100(self, regiao_id, agente):
        resultado = chamar_guardiao(regiao_id)
        sc = resultado["pareceres"][agente]["score"]
        assert 0 <= sc <= 100, (
            f"Score do agente '{agente}' ({sc}) fora do intervalo para '{regiao_id}'"
        )


# ---------------------------------------------------------------------------
# Testes de consistência matemática
# ---------------------------------------------------------------------------


class TestConsistenciaMath:
    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_score_consolidado_consistente_com_pesos(self, regiao_id):
        """Verifica que score_consolidado == round(média ponderada)."""
        resultado = chamar_guardiao(regiao_id)
        pareceres = resultado["pareceres"]
        score_esperado = _calcular_score_consolidado(pareceres)
        assert resultado["score_consolidado"] == score_esperado

    def test_pesos_somam_100_porcento(self):
        total = sum(_PESOS.values())
        assert abs(total - 1.0) < 1e-9, f"Pesos somam {total}, esperado 1.0"

    def test_pesos_tem_5_agentes(self):
        assert set(_PESOS.keys()) == set(AGENTES_ESPECIALISTAS)

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_recomendacao_e_score_coerentes(self, regiao_id):
        """Score >= 50 nunca deve resultar em 'aguardar' ou 'escalar'."""
        resultado = chamar_guardiao(regiao_id)
        sc = resultado["score_consolidado"]
        rec = resultado["recomendacao"]
        if sc >= 50:
            assert rec in {"investir_agora", "realizar_piloto"}, (
                f"Score {sc} deveria gerar investir_agora ou realizar_piloto, "
                f"mas retornou '{rec}' para '{regiao_id}'"
            )
        if sc < 30:
            assert rec == "escalar", (
                f"Score {sc} deveria gerar 'escalar', "
                f"mas retornou '{rec}' para '{regiao_id}'"
            )


# ---------------------------------------------------------------------------
# Testes de erro — região inexistente
# ---------------------------------------------------------------------------


class TestRegioesInexistentes:
    def test_regiao_inexistente_nao_levanta_excecao(self):
        resultado = chamar_guardiao("nao_existe")
        assert isinstance(resultado, dict)

    def test_regiao_inexistente_tem_campo_erro(self):
        resultado = chamar_guardiao("nao_existe")
        assert "erro" in resultado
        assert resultado["erro"] is not None

    def test_regiao_inexistente_score_zero(self):
        resultado = chamar_guardiao("nao_existe")
        assert resultado["score_consolidado"] == 0

    def test_regiao_inexistente_recomendacao_escalar(self):
        resultado = chamar_guardiao("nao_existe")
        assert resultado["recomendacao"] == "escalar"

    def test_regiao_id_vazia_nao_levanta_excecao(self):
        resultado = chamar_guardiao("")
        assert isinstance(resultado, dict)

    def test_regiao_id_maiuscula_aceita(self):
        """IDs em maiúscula devem funcionar (normalização de case)."""
        resultado = chamar_guardiao("AURORA")
        assert resultado.get("erro") is None, (
            "Região 'AURORA' em maiúscula deveria ser aceita"
        )
        assert resultado["score_consolidado"] > 0


# ---------------------------------------------------------------------------
# Testes de consistência das 6 regiões (execução sem exceção)
# ---------------------------------------------------------------------------


class TestTodasRegioes:
    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_regiao_executa_sem_excecao(self, regiao_id):
        """Garante que nenhuma das 6 regiões levanta exceção."""
        try:
            resultado = chamar_guardiao(regiao_id)
        except Exception as e:
            pytest.fail(f"Região '{regiao_id}' levantou exceção: {e}")
        assert isinstance(resultado, dict)

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_regiao_retorna_recomendacao(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        assert resultado.get("recomendacao") in RECOMENDACOES_VALIDAS

    def test_lista_regioes_tem_6_itens(self):
        from tools.consultar_regiao import listar_regioes  # type: ignore[import]
        regioes = listar_regioes()
        assert len(regioes) == 6, f"Esperadas 6 regiões, obtidas {len(regioes)}"

    def test_ids_retornados_sao_os_esperados(self):
        from tools.consultar_regiao import listar_ids_regioes  # type: ignore[import]
        ids = set(listar_ids_regioes())
        assert ids == set(IDS_VALIDOS)


# ---------------------------------------------------------------------------
# Testes de scores e recomendacoes exatos — fonte unica: Guardiao
# ---------------------------------------------------------------------------


class TestScoresExatos:
    """
    Verifica que chamar_guardiao devolve exatamente os mesmos scores e
    recomendacoes que a tool_guardiao calcula diretamente.
    Referencia: aurora 62 piloto | horizonte 57 piloto | esperanca 44 aguardar
                central 60 piloto | vale_verde 60 piloto | nova_uniao 30 escalar
    """

    @pytest.mark.parametrize("regiao_id,score_esp,rec_esp", [
        ("aurora",     62, "realizar_piloto"),
        ("horizonte",  57, "realizar_piloto"),
        ("esperanca",  44, "aguardar"),
        ("central",    60, "realizar_piloto"),
        ("vale_verde", 60, "realizar_piloto"),
        ("nova_uniao", 30, "escalar"),
    ])
    def test_score_e_recomendacao_exatos(self, regiao_id, score_esp, rec_esp):
        resultado = chamar_guardiao(regiao_id)
        assert resultado["score_consolidado"] == score_esp, (
            f"{regiao_id}: score esperado {score_esp}, obtido {resultado['score_consolidado']}"
        )
        assert resultado["recomendacao"] == rec_esp, (
            f"{regiao_id}: recomendacao esperada '{rec_esp}', obtida '{resultado['recomendacao']}'"
        )

    def test_nova_uniao_escalar(self):
        """Nova Uniao tem orcamento=0 < 20 -> regra extra do grupo forca 'escalar'."""
        resultado = chamar_guardiao("nova_uniao")
        assert resultado["recomendacao"] == "escalar", (
            f"Nova Uniao deve ser 'escalar', obtido '{resultado['recomendacao']}'"
        )
        assert resultado["score_consolidado"] == 30
