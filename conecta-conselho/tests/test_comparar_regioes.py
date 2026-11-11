"""
Testes para a seção "Comparar regiões" de paginas/analise.py.

Cobre:
  (a) _analisar_para_comparar — modo local devolve resultado real para regiões válidas.
  (b) _analisar_para_comparar — região inexistente devolve dict com campo "erro".
  (c) _analisar_para_comparar — excepção interna é capturada e devolvida como {"erro": ...}.
  (d) _mini_card_comparar — chama st.markdown + st.dataframe para resultado válido.
  (e) _mini_card_comparar — exibe st.error quando resultado tem "erro".
  (f) _mini_card_comparar — exibe st.warning quando status = analise_incompleta.
  (g) _mini_card_comparar — exibe st.error quando atencao_prioritaria=True.
  (h) _mini_card_comparar — sem alerta quando atencao_prioritaria=False/ausente.
  (i) _radar_duplo — constrói figura Plotly com duas traces e chama st.plotly_chart.
  (j) Constantes _CORES_HEX e _LABELS_RECOMENDACAO mapeiam recomendações de piloto, invest e aguardar.
  (k) _analisar_para_comparar — modo nuvem delega para _consultar_nuvem (mockado).
  (l) Valores do exemplo da especificação: Central score≥55, nova_uniao score≤40.

AVISO: Nenhum teste acessa a internet — todos os calls de rede são mockados.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Configuração de paths
# ---------------------------------------------------------------------------

_CC_DIR = Path(__file__).resolve().parent.parent   # conecta-conselho/
_ROOT   = _CC_DIR.parent                            # inteli_girls/

for _p in [str(_ROOT), str(_CC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import unittest.mock as _mock

# ---------------------------------------------------------------------------
# Fixture: mock streamlit antes de importar paginas.analise
# (mesmo padrão de test_analise_cache.py)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _mock_streamlit():
    """Evita que paginas.analise tente inicializar o Streamlit durante os testes."""
    st_mock = MagicMock()

    def _cache_data_decorator(ttl=None, show_spinner=True):
        def _decorator(fn):
            import functools
            _store: dict = {}

            def _cache_key(args, kwargs):
                kwargs_cacheaveis = tuple(
                    sorted((k, v) for k, v in kwargs.items() if not k.startswith("_"))
                )
                return (args, kwargs_cacheaveis)

            @functools.wraps(fn)
            def _wrapper(*args, **kwargs):
                key = _cache_key(args, kwargs)
                if key not in _store:
                    _store[key] = fn(*args, **kwargs)
                return _store[key]

            def _clear(*args, **kwargs):
                if not args and not kwargs:
                    _store.clear()
                else:
                    _store.pop(_cache_key(args, kwargs), None)

            _wrapper.clear = _clear
            return _wrapper
        return _decorator

    st_mock.cache_data = _cache_data_decorator
    st_mock.session_state = {}
    with _mock.patch.dict("sys.modules", {"streamlit": st_mock}):
        yield st_mock


# ---------------------------------------------------------------------------
# Importação do módulo sob teste (depois do mock do streamlit)
# ---------------------------------------------------------------------------


def _mod():
    """Importa paginas.analise com cache limpo para isolamento de testes."""
    for key in list(sys.modules.keys()):
        if "paginas" in key and "analise" in key:
            del sys.modules[key]
    import paginas.analise as m
    return m


# ---------------------------------------------------------------------------
# Resultados de exemplo
# ---------------------------------------------------------------------------


def _resultado_central():
    return {
        "regiao_id": "central",
        "regiao_nome": "Região Central",
        "status": "concluida",
        "score_consolidado": 60,
        "recomendacao": "realizar_piloto",
        "atencao_prioritaria": False,
        "pontos_criticos": [],
        "fonte": "local",
        "pareceres": {
            "mercado":        {"score": 55},
            "impacto_social": {"score": 30},
            "engenharia":     {"score": 70},
            "orcamento":      {"score": 76},
            "pontes":         {"score": 60},
        },
    }


def _resultado_nova_uniao():
    return {
        "regiao_id": "nova_uniao",
        "regiao_nome": "Região Nova União",
        "status": "concluida",
        "score_consolidado": 30,
        "recomendacao": "aguardar",
        "atencao_prioritaria": True,
        "pontos_criticos": ["Orçamento zero", "Alta exclusão social"],
        "fonte": "local",
        "pareceres": {
            "mercado":        {"score": 20},
            "impacto_social": {"score": 78},
            "engenharia":     {"score": 35},
            "orcamento":      {"score": 0},
            "pontes":         {"score": 25},
        },
    }


# ---------------------------------------------------------------------------
# (a) _analisar_para_comparar — modo local, resultado real
# ---------------------------------------------------------------------------


class TestAnalisarParaComparar:
    def test_local_retorna_dict_com_score(self):
        mod = _mod()
        res = mod._analisar_para_comparar("central", "local")
        assert isinstance(res, dict)
        assert "score_consolidado" in res
        assert res.get("score_consolidado") is not None

    def test_local_retorna_status_concluida_para_regiao_valida(self):
        mod = _mod()
        res = mod._analisar_para_comparar("aurora", "local")
        assert res.get("status") == "concluida"

    # (b) Região inexistente → erro propagado no resultado
    def test_regiao_inexistente_retorna_erro_ou_incompleta(self):
        mod = _mod()
        res = mod._analisar_para_comparar("nao_existe_xyzxyz", "local")
        # Ou tem campo "erro" ou status analise_incompleta
        tem_erro = bool(res.get("erro")) or res.get("status") == "analise_incompleta"
        assert tem_erro, f"Esperava erro ou analise_incompleta, recebeu: {res}"

    # (c) Excepção interna capturada
    def test_excecao_interna_devolvida_como_erro(self):
        mod = _mod()

        def _falha(regiao_id, *, fonte=None, ao_concluir_agente=None):
            raise RuntimeError("falha simulada")

        with patch.object(mod, "chamar_guardiao", _falha):
            res = mod._analisar_para_comparar("central", "local")

        assert "erro" in res
        assert "falha simulada" in res["erro"]

    # (k) Modo nuvem delega para _consultar_nuvem
    def test_nuvem_delega_para_consultar_nuvem(self):
        mod = _mod()
        esperado = _resultado_central()

        with patch.object(mod, "_consultar_nuvem", return_value=(esperado, False)) as mock_cn:
            res = mod._analisar_para_comparar("central", "nuvem")

        mock_cn.assert_called_once_with("central", "nuvem")
        assert res == esperado


# ---------------------------------------------------------------------------
# (d)-(h) _mini_card_comparar
# ---------------------------------------------------------------------------


class TestMiniCardComparar:
    def test_chama_markdown_para_resultado_valido(self, _mock_streamlit):
        mod = _mod()
        mod._mini_card_comparar(_resultado_central())
        assert _mock_streamlit.markdown.called

    def test_chama_dataframe_para_resultado_com_pareceres(self, _mock_streamlit):
        mod = _mod()
        mod._mini_card_comparar(_resultado_central())
        assert _mock_streamlit.dataframe.called

    # (e) erro no resultado
    def test_exibe_error_quando_resultado_tem_erro(self, _mock_streamlit):
        mod = _mod()
        mod._mini_card_comparar({"erro": "timeout na nuvem", "regiao_id": "x"})
        assert _mock_streamlit.error.called
        # Não deve chamar markdown do cartão
        assert not _mock_streamlit.markdown.called

    # (f) analise_incompleta → warning
    def test_exibe_warning_para_analise_incompleta(self, _mock_streamlit):
        mod = _mod()
        res = {
            "status": "analise_incompleta",
            "score_consolidado": None,
            "recomendacao": None,
            "pareceres": {},
        }
        mod._mini_card_comparar(res)
        assert _mock_streamlit.warning.called

    # (g) atencao_prioritaria → st.error com pontos_criticos
    def test_alerta_atencao_prioritaria_chama_error(self, _mock_streamlit):
        mod = _mod()
        mod._mini_card_comparar(_resultado_nova_uniao())
        assert _mock_streamlit.error.called
        # Verifica que o conteúdo menciona pontos críticos
        args_error = _mock_streamlit.error.call_args[0][0]
        assert "Atenção Prioritária" in args_error

    # (h) sem atencao_prioritaria → sem error
    def test_sem_alerta_quando_atencao_false(self, _mock_streamlit):
        mod = _mod()
        mod._mini_card_comparar(_resultado_central())
        assert not _mock_streamlit.error.called

    def test_tabela_contem_cinco_agentes(self, _mock_streamlit):
        mod = _mod()
        mod._mini_card_comparar(_resultado_central())
        # st.dataframe deve ter sido chamado com uma lista de 5 linhas
        chamada = _mock_streamlit.dataframe.call_args
        rows = chamada[0][0]
        assert len(rows) == 5

    def test_tabela_scores_corretos(self, _mock_streamlit):
        mod = _mod()
        mod._mini_card_comparar(_resultado_central())
        rows = _mock_streamlit.dataframe.call_args[0][0]
        scores = {r["Agente"]: r["Score"] for r in rows}
        assert scores["Orçamento"] == 76
        assert scores["Impacto Social"] == 30


# ---------------------------------------------------------------------------
# (i) _radar_duplo
# ---------------------------------------------------------------------------


class TestRadarDuplo:
    def test_plotly_chart_chamado(self, _mock_streamlit):
        mod = _mod()
        mod._radar_duplo(
            _resultado_central()["pareceres"],
            _resultado_nova_uniao()["pareceres"],
            "Central",
            "Nova União",
        )
        assert _mock_streamlit.plotly_chart.called

    def test_figura_tem_duas_traces(self, _mock_streamlit):
        """A figura Plotly passada para st.plotly_chart deve ter 2 traces."""
        mod = _mod()
        mod._radar_duplo(
            _resultado_central()["pareceres"],
            _resultado_nova_uniao()["pareceres"],
            "Central",
            "Nova União",
        )
        fig = _mock_streamlit.plotly_chart.call_args[0][0]
        assert len(fig.data) == 2

    def test_nomes_nas_traces(self, _mock_streamlit):
        mod = _mod()
        mod._radar_duplo(
            _resultado_central()["pareceres"],
            _resultado_nova_uniao()["pareceres"],
            "Central",
            "Nova União",
        )
        fig = _mock_streamlit.plotly_chart.call_args[0][0]
        nomes = [t.name for t in fig.data]
        assert "Central" in nomes
        assert "Nova União" in nomes

    def test_escala_radial_0_100(self, _mock_streamlit):
        mod = _mod()
        mod._radar_duplo(
            _resultado_central()["pareceres"],
            _resultado_nova_uniao()["pareceres"],
            "A",
            "B",
        )
        fig = _mock_streamlit.plotly_chart.call_args[0][0]
        assert list(fig.layout.polar.radialaxis.range) == [0, 100]

    def test_valores_corretos_serie_a(self, _mock_streamlit):
        """Série A (Central) deve ter orcamento=76 e impacto_social=30."""
        mod = _mod()
        mod._radar_duplo(
            _resultado_central()["pareceres"],
            _resultado_nova_uniao()["pareceres"],
            "Central",
            "Nova União",
        )
        fig = _mock_streamlit.plotly_chart.call_args[0][0]
        trace_central = next(t for t in fig.data if t.name == "Central")
        # Ordem: mercado, impacto_social, engenharia, orcamento, pontes, mercado(fechado)
        # índices:  0          1            2           3          4       5
        assert trace_central.r[3] == 76   # orcamento
        assert trace_central.r[1] == 30   # impacto_social

    def test_valores_corretos_serie_b(self, _mock_streamlit):
        """Série B (Nova União) deve ter orcamento=0 e impacto_social=78."""
        mod = _mod()
        mod._radar_duplo(
            _resultado_central()["pareceres"],
            _resultado_nova_uniao()["pareceres"],
            "Central",
            "Nova União",
        )
        fig = _mock_streamlit.plotly_chart.call_args[0][0]
        trace_nu = next(t for t in fig.data if t.name == "Nova União")
        assert trace_nu.r[3] == 0    # orcamento
        assert trace_nu.r[1] == 78   # impacto_social


# ---------------------------------------------------------------------------
# (j) Constantes
# ---------------------------------------------------------------------------


class TestConstantes:
    def test_cores_hex_cobre_tres_recomendacoes(self):
        mod = _mod()
        assert "realizar_piloto" in mod._CORES_HEX
        assert "investir_agora" in mod._CORES_HEX
        assert "aguardar" in mod._CORES_HEX
        assert "analise_incompleta" in mod._CORES_HEX

    def test_labels_recomendacao_strings_amigaveis(self):
        mod = _mod()
        assert mod._LABELS_RECOMENDACAO["realizar_piloto"] == "Começar com piloto"
        assert mod._LABELS_RECOMENDACAO["investir_agora"]  == "Investir agora"
        assert mod._LABELS_RECOMENDACAO["aguardar"]        == "Aguardar"


# ---------------------------------------------------------------------------
# (l) Exemplo da especificação: Central × Nova União
# ---------------------------------------------------------------------------


class TestExemploEspecificacao:
    """
    Verifica os valores do exemplo indicado na especificação:
    Central (60, piloto, orçamento 76 / social 30) × Nova União (30, aguardar ⚠️, orçamento 0 / social 78).
    """

    def test_central_score_range(self):
        mod = _mod()
        res = mod._analisar_para_comparar("central", "local")
        score = res.get("score_consolidado", 0)
        assert 55 <= score <= 70, f"Score de Central fora do esperado: {score}"

    def test_central_recomendacao_piloto(self):
        mod = _mod()
        res = mod._analisar_para_comparar("central", "local")
        assert res.get("recomendacao") in ("realizar_piloto", "investir_agora"), (
            f"Recomendação de Central inesperada: {res.get('recomendacao')}"
        )

    def test_central_orcamento_score(self):
        mod = _mod()
        res = mod._analisar_para_comparar("central", "local")
        orcamento = res.get("pareceres", {}).get("orcamento", {}).get("score")
        assert orcamento is not None
        assert 70 <= orcamento <= 82, f"Score de orçamento de Central fora do esperado: {orcamento}"

    def test_central_social_score_menor_que_orcamento(self):
        mod = _mod()
        res = mod._analisar_para_comparar("central", "local")
        pareceres = res.get("pareceres", {})
        social   = pareceres.get("impacto_social", {}).get("score", 100)
        orcamento = pareceres.get("orcamento", {}).get("score", 0)
        assert social < orcamento, (
            f"Central: esperava social ({social}) < orcamento ({orcamento})"
        )

    def test_nova_uniao_score_range(self):
        mod = _mod()
        res = mod._analisar_para_comparar("nova_uniao", "local")
        score = res.get("score_consolidado", 100)
        assert score <= 45, f"Score de Nova União fora do esperado: {score}"

    def test_nova_uniao_recomendacao_aguardar(self):
        mod = _mod()
        res = mod._analisar_para_comparar("nova_uniao", "local")
        assert res.get("recomendacao") == "aguardar", (
            f"Recomendação de Nova União: {res.get('recomendacao')}"
        )

    def test_nova_uniao_atencao_prioritaria(self):
        mod = _mod()
        res = mod._analisar_para_comparar("nova_uniao", "local")
        assert res.get("atencao_prioritaria") is True, (
            "Nova União deveria ter atencao_prioritaria=True"
        )

    def test_nova_uniao_social_score_maior_que_orcamento(self):
        mod = _mod()
        res = mod._analisar_para_comparar("nova_uniao", "local")
        pareceres = res.get("pareceres", {})
        social   = pareceres.get("impacto_social", {}).get("score", 0)
        orcamento = pareceres.get("orcamento", {}).get("score", 100)
        assert social > orcamento, (
            f"Nova União: esperava social ({social}) > orcamento ({orcamento})"
        )
