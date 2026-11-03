"""
Testes de integração para conecta-conselho/integracao.py.

Testa:
  - Contrato da saída de chamar_guardiao (campos obrigatórios, tipos, valores válidos)
  - Todas as 6 regiões executam sem exceção
  - Campos do contrato do Guardião (novo formato sem "escalar" e sem "principais_oportunidades")
  - Score consolidado entre 0 e 100 (ou null para analise_incompleta)
  - Recomendação sempre um dos três valores válidos (investir_agora, realizar_piloto, aguardar)
  - Divergências é lista (pode ser vazia)
  - Região inexistente retorna analise_incompleta, não levanta exceção
  - Score consolidado é calculado com os pesos corretos
  - Novos campos: status, atencao_prioritaria, pontos_criticos, motivos, caminhos, agentes_com_falha
  - Scores e recomendações exatos por região

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

# "escalar" foi removido do Guardião novo
RECOMENDACOES_VALIDAS = {"investir_agora", "realizar_piloto", "aguardar"}

CAMPOS_OBRIGATORIOS = [
    "agente",
    "regiao_id",
    "regiao_nome",
    "status",
    "recomendacao",
    "score_consolidado",
    "pareceres",
    "divergencias",
    "justificativa_consolidada",
    "principais_riscos",
    "limitacoes",
    "simulado",
    "erro",
    "atencao_prioritaria",
    "pontos_criticos",
    "motivos",
    "caminhos",
]

AGENTES_ESPECIALISTAS = [
    "mercado",
    "impacto_social",
    "engenharia",
    "orcamento",
    "pontes",
]

# O Guardiao retorna apenas score, confianca, justificativa e erro no resumo de pareceres.
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
    """Valida que a saída de chamar_guardiao respeita o contrato do Guardião novo."""

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

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_status_concluida_para_regioes_validas(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        assert resultado["status"] == "concluida", (
            f"Status esperado 'concluida' para '{regiao_id}', obtido '{resultado['status']}'"
        )

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_fonte_local_por_padrao(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        assert resultado.get("fonte") == "local", (
            f"Fonte esperada 'local' para '{regiao_id}', obtida '{resultado.get('fonte')}'"
        )

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_tempo_analise_presente(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        assert "tempo_analise_segundos" in resultado, (
            f"Campo 'tempo_analise_segundos' ausente para '{regiao_id}'"
        )
        assert isinstance(resultado["tempo_analise_segundos"], (int, float))


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
    def test_recomendacao_nunca_escalar(self, regiao_id):
        """'escalar' foi removido do Guardião novo."""
        resultado = chamar_guardiao(regiao_id)
        assert resultado["recomendacao"] != "escalar", (
            f"Recomendação 'escalar' não deve existir mais para '{regiao_id}'"
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
    def test_sem_campo_principais_oportunidades(self, regiao_id):
        """principais_oportunidades foi removido do novo formato."""
        resultado = chamar_guardiao(regiao_id)
        assert "principais_oportunidades" not in resultado, (
            f"Campo 'principais_oportunidades' não deve existir no novo formato para '{regiao_id}'"
        )

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

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_atencao_prioritaria_e_bool(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        assert isinstance(resultado["atencao_prioritaria"], bool), (
            f"atencao_prioritaria deve ser bool para '{regiao_id}'"
        )

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_pontos_criticos_e_lista(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        assert isinstance(resultado["pontos_criticos"], list)

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_motivos_e_lista(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        assert isinstance(resultado["motivos"], list)

    @pytest.mark.parametrize("regiao_id", IDS_VALIDOS)
    def test_caminhos_e_lista(self, regiao_id):
        resultado = chamar_guardiao(regiao_id)
        assert isinstance(resultado["caminhos"], list)


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
        """Score >= 50 nunca deve resultar em 'aguardar'."""
        resultado = chamar_guardiao(regiao_id)
        sc = resultado["score_consolidado"]
        rec = resultado["recomendacao"]
        if sc >= 50:
            assert rec in {"investir_agora", "realizar_piloto"}, (
                f"Score {sc} deveria gerar investir_agora ou realizar_piloto, "
                f"mas retornou '{rec}' para '{regiao_id}'"
            )
        if sc < 50:
            assert rec == "aguardar", (
                f"Score {sc} deveria gerar 'aguardar', "
                f"mas retornou '{rec}' para '{regiao_id}'"
            )


# ---------------------------------------------------------------------------
# Testes de erro — região inexistente
# ---------------------------------------------------------------------------


class TestRegioesInexistentes:
    def test_regiao_inexistente_nao_levanta_excecao(self):
        resultado = chamar_guardiao("nao_existe")
        assert isinstance(resultado, dict)

    def test_regiao_inexistente_analise_incompleta(self):
        """Região inexistente: todos os 5 agentes com erro -> analise_incompleta."""
        resultado = chamar_guardiao("nao_existe")
        assert resultado["status"] == "analise_incompleta", (
            f"Esperado status 'analise_incompleta', obtido '{resultado['status']}'"
        )

    def test_regiao_inexistente_recomendacao_null(self):
        resultado = chamar_guardiao("nao_existe")
        assert resultado["recomendacao"] is None, (
            f"Recomendação deve ser None para região inexistente, obtido '{resultado['recomendacao']}'"
        )

    def test_regiao_inexistente_score_null(self):
        resultado = chamar_guardiao("nao_existe")
        assert resultado["score_consolidado"] is None, (
            f"Score deve ser None para região inexistente, obtido '{resultado['score_consolidado']}'"
        )

    def test_regiao_inexistente_tem_agentes_com_falha(self):
        resultado = chamar_guardiao("nao_existe")
        assert "agentes_com_falha" in resultado
        assert len(resultado["agentes_com_falha"]) == 5

    def test_regiao_id_vazia_nao_levanta_excecao(self):
        resultado = chamar_guardiao("")
        assert isinstance(resultado, dict)

    def test_regiao_id_maiuscula_aceita(self):
        """IDs em maiúscula devem funcionar (normalização de case)."""
        resultado = chamar_guardiao("AURORA")
        assert resultado.get("status") == "concluida", (
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
    def test_regiao_retorna_recomendacao_valida(self, regiao_id):
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
# Testes de scores, recomendações e atenção prioritária exatos
# ---------------------------------------------------------------------------


class TestScoresExatos:
    """
    Verifica que chamar_guardiao devolve exatamente os mesmos scores,
    recomendações e atenção prioritária que a tool_guardiao calcula.

    Referência:
      aurora 62 piloto · horizonte 57 piloto · esperanca 44 aguardar
      central 60 piloto · vale_verde 60 piloto · nova_uniao 30 aguardar atencao_prioritaria=True
    """

    @pytest.mark.parametrize("regiao_id,score_esp,rec_esp", [
        ("aurora",     62, "realizar_piloto"),
        ("horizonte",  57, "realizar_piloto"),
        ("esperanca",  44, "aguardar"),
        ("central",    60, "realizar_piloto"),
        ("vale_verde", 60, "realizar_piloto"),
        ("nova_uniao", 30, "aguardar"),
    ])
    def test_score_e_recomendacao_exatos(self, regiao_id, score_esp, rec_esp):
        resultado = chamar_guardiao(regiao_id)
        assert resultado["score_consolidado"] == score_esp, (
            f"{regiao_id}: score esperado {score_esp}, obtido {resultado['score_consolidado']}"
        )
        assert resultado["recomendacao"] == rec_esp, (
            f"{regiao_id}: recomendacao esperada '{rec_esp}', obtida '{resultado['recomendacao']}'"
        )

    def test_nova_uniao_atencao_prioritaria(self):
        """Nova Uniao tem orcamento=0 < 20 -> atencao_prioritaria=True."""
        resultado = chamar_guardiao("nova_uniao")
        assert resultado["atencao_prioritaria"] is True, (
            f"Nova Uniao deve ter atencao_prioritaria=True, obtido '{resultado['atencao_prioritaria']}'"
        )
        assert resultado["score_consolidado"] == 30
        assert resultado["recomendacao"] == "aguardar"

    def test_nova_uniao_nao_escalar(self):
        """'escalar' foi removido — Nova Uniao agora é 'aguardar', não 'escalar'."""
        resultado = chamar_guardiao("nova_uniao")
        assert resultado["recomendacao"] != "escalar", (
            "Recomendação 'escalar' não deve existir no Guardião novo"
        )

    def test_aguardar_tem_motivos(self):
        """Regiões com 'aguardar' devem ter motivos preenchidos."""
        for regiao_id in ["esperanca", "nova_uniao"]:
            resultado = chamar_guardiao(regiao_id)
            assert resultado["recomendacao"] == "aguardar"
            assert len(resultado.get("motivos", [])) > 0, (
                f"'{regiao_id}' com 'aguardar' deve ter motivos preenchidos"
            )

    def test_piloto_motivos_e_caminhos_vazios(self):
        """Regiões com 'realizar_piloto' devem ter motivos e caminhos vazios."""
        resultado = chamar_guardiao("aurora")
        assert resultado["recomendacao"] == "realizar_piloto"
        assert resultado.get("motivos") == [], "aurora: motivos devem ser vazios para piloto"
        assert resultado.get("caminhos") == [], "aurora: caminhos devem ser vazios para piloto"
