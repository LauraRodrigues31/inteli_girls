"""
Testes do parâmetro ao_concluir_agente em integracao._consolidar_nuvem / chamar_guardiao.

Verifica:
  (a) Callback é chamado uma vez por agente (5 chamadas no total) — todos OK.
  (b) Callback recebe sucesso=False e nome amigável quando o agente retorna erro.
  (c) Callback recebe sucesso=False quando agent_id está ausente (IDs não configurados).
  (d) Callback recebe sucesso=False quando chamar_agente lança excepção.
  (e) Callback não é chamado quando ao_concluir_agente=None (comportamento padrão).
  (f) Callback recebe o nome amigável correto (não a chave interna).
  (g) Tempo passado ao callback é um float >= 0.
  (h) Callback é chamado na thread principal (threading.get_ident()), não dentro
      das threads do ThreadPoolExecutor — garantia de compatibilidade com Streamlit.

AVISO: Nenhum teste acessa a internet — todos os calls de rede são mockados.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# Configuração de paths
# ---------------------------------------------------------------------------

_CC_DIR = Path(__file__).resolve().parent.parent   # conecta-conselho/
_ROOT   = _CC_DIR.parent                            # inteli_girls/

for _p in [str(_ROOT), str(_CC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------------
# Dados de referência
# ---------------------------------------------------------------------------

_AGENTE_ENV = {
    "mercado":        "CC_AGENT_ID_MERCADO",
    "impacto_social": "CC_AGENT_ID_SOCIAL",
    "engenharia":     "CC_AGENT_ID_ENGENHARIA",
    "orcamento":      "CC_AGENT_ID_ORCAMENTO",
    "pontes":         "CC_AGENT_ID_PONTES",
}

_IDS_FAKE = {env: f"agent-fake-{env.lower().replace('_', '-')}" for env in _AGENTE_ENV.values()}

# Nomes amigáveis esperados no callback (espelha _NOMES_AMIGAVEIS_AGENTES em integracao.py)
_NOMES_AMIGAVEIS = {
    "mercado":        "Mercado",
    "impacto_social": "Impacto Social",
    "engenharia":     "Engenharia",
    "orcamento":      "Orçamento",
    "pontes":         "Pontes",
}

# Pareceres mínimos válidos para cada agente
_PARECER_MINIMO = {
    "score": 60,
    "confianca": "alta",
    "justificativa": "ok",
    "riscos": [],
}


def _resposta_api(parecer: dict) -> dict:
    return {
        "choices": [{"message": {"content": json.dumps(parecer, ensure_ascii=False)}}]
    }


def _criar_mock_cliente_nuvem(
    respostas: dict[str, dict | Exception],
) -> types.ModuleType:
    """Cria módulo cliente_nuvem simulado."""
    mod = types.ModuleType("cliente_nuvem")

    def _chamar_agente(agent_id: str, mensagem: str) -> dict:
        resp = respostas.get(agent_id)
        if isinstance(resp, Exception):
            raise resp
        if resp is None:
            raise ValueError(f"agent_id '{agent_id}' não no mock")
        return resp

    def _extrair_json(conteudo: str) -> dict:
        return json.loads(conteudo.strip())

    mod.chamar_agente = _chamar_agente
    mod.extrair_json = _extrair_json
    return mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def env_com_ids(monkeypatch):
    """Configura os 5 agent IDs falsos no ambiente."""
    monkeypatch.setenv("CC_MODO", "nuvem")
    for env_var, fake_id in _IDS_FAKE.items():
        monkeypatch.setenv(env_var, fake_id)
    yield


@pytest.fixture
def env_sem_ids(monkeypatch):
    """Remove todos os IDs de agente do ambiente."""
    monkeypatch.setenv("CC_MODO", "nuvem")
    for env_var in _AGENTE_ENV.values():
        monkeypatch.delenv(env_var, raising=False)
    yield


def _respostas_todos_ok() -> dict[str, dict]:
    return {
        fake_id: _resposta_api(_PARECER_MINIMO)
        for fake_id in _IDS_FAKE.values()
    }


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------


class TestCallbackTodosOK:
    """(a) 5 agentes OK — callback chamado 5 vezes com sucesso=True."""

    def test_callback_chamado_cinco_vezes(self, env_com_ids):
        mock_cliente = _criar_mock_cliente_nuvem(_respostas_todos_ok())
        callback = MagicMock()

        import integracao
        with patch.dict("sys.modules", {"cliente_nuvem": mock_cliente}):
            integracao._consolidar_nuvem("aurora", ao_concluir_agente=callback)

        assert callback.call_count == 5

    def test_callback_sucesso_true_para_todos(self, env_com_ids):
        mock_cliente = _criar_mock_cliente_nuvem(_respostas_todos_ok())
        callback = MagicMock()

        import integracao
        with patch.dict("sys.modules", {"cliente_nuvem": mock_cliente}):
            integracao._consolidar_nuvem("aurora", ao_concluir_agente=callback)

        for args, kwargs in callback.call_args_list:
            nome, sucesso, tempo = args
            assert sucesso is True, f"Esperava sucesso=True para '{nome}'"

    def test_callback_tempo_float_nao_negativo(self, env_com_ids):
        mock_cliente = _criar_mock_cliente_nuvem(_respostas_todos_ok())
        callback = MagicMock()

        import integracao
        with patch.dict("sys.modules", {"cliente_nuvem": mock_cliente}):
            integracao._consolidar_nuvem("aurora", ao_concluir_agente=callback)

        for args, _ in callback.call_args_list:
            nome, sucesso, tempo = args
            assert isinstance(tempo, float)
            assert tempo >= 0.0, f"Tempo negativo para '{nome}': {tempo}"

    def test_callback_nomes_amigaveis(self, env_com_ids):
        """Callback recebe nomes amigáveis, não chaves internas."""
        mock_cliente = _criar_mock_cliente_nuvem(_respostas_todos_ok())
        callback = MagicMock()

        import integracao
        with patch.dict("sys.modules", {"cliente_nuvem": mock_cliente}):
            integracao._consolidar_nuvem("aurora", ao_concluir_agente=callback)

        nomes_recebidos = {args[0] for args, _ in callback.call_args_list}
        nomes_esperados = set(_NOMES_AMIGAVEIS.values())
        assert nomes_recebidos == nomes_esperados


class TestCallbackComErro:
    """(b) Um agente retorna erro — callback com sucesso=False."""

    def test_callback_sucesso_false_quando_agente_retorna_erro(self, env_com_ids):
        respostas = _respostas_todos_ok()
        id_engenharia = _IDS_FAKE["CC_AGENT_ID_ENGENHARIA"]
        respostas[id_engenharia] = {"erro": "timeout"}

        mock_cliente = _criar_mock_cliente_nuvem(respostas)
        callback = MagicMock()

        import integracao
        with patch.dict("sys.modules", {"cliente_nuvem": mock_cliente}):
            integracao._consolidar_nuvem("aurora", ao_concluir_agente=callback)

        chamadas_engenharia = [
            args for args, _ in callback.call_args_list
            if args[0] == "Engenharia"
        ]
        assert len(chamadas_engenharia) == 1
        _, sucesso, _ = chamadas_engenharia[0]
        assert sucesso is False

    def test_callback_outros_agentes_ainda_sucesso(self, env_com_ids):
        respostas = _respostas_todos_ok()
        id_engenharia = _IDS_FAKE["CC_AGENT_ID_ENGENHARIA"]
        respostas[id_engenharia] = {"erro": "timeout"}

        mock_cliente = _criar_mock_cliente_nuvem(respostas)
        callback = MagicMock()

        import integracao
        with patch.dict("sys.modules", {"cliente_nuvem": mock_cliente}):
            integracao._consolidar_nuvem("aurora", ao_concluir_agente=callback)

        for args, _ in callback.call_args_list:
            nome, sucesso, _ = args
            if nome != "Engenharia":
                assert sucesso is True, f"Esperava sucesso=True para '{nome}'"


class TestCallbackSemIDs:
    """(c) IDs ausentes — callback com sucesso=False para todos."""

    def test_callback_sucesso_false_sem_ids(self, env_sem_ids):
        mock_cliente = _criar_mock_cliente_nuvem({})
        callback = MagicMock()

        import integracao
        with patch.dict("sys.modules", {"cliente_nuvem": mock_cliente}):
            integracao._consolidar_nuvem("aurora", ao_concluir_agente=callback)

        assert callback.call_count == 5
        for args, _ in callback.call_args_list:
            _, sucesso, _ = args
            assert sucesso is False

    def test_callback_nomes_amigaveis_sem_ids(self, env_sem_ids):
        mock_cliente = _criar_mock_cliente_nuvem({})
        callback = MagicMock()

        import integracao
        with patch.dict("sys.modules", {"cliente_nuvem": mock_cliente}):
            integracao._consolidar_nuvem("aurora", ao_concluir_agente=callback)

        nomes_recebidos = {args[0] for args, _ in callback.call_args_list}
        nomes_esperados = set(_NOMES_AMIGAVEIS.values())
        assert nomes_recebidos == nomes_esperados


class TestCallbackComExcecao:
    """(d) chamar_agente lança excepção — callback com sucesso=False."""

    def test_callback_sucesso_false_quando_excecao(self, env_com_ids):
        respostas = _respostas_todos_ok()
        id_pontes = _IDS_FAKE["CC_AGENT_ID_PONTES"]
        respostas[id_pontes] = ConnectionError("falha de rede simulada")

        mock_cliente = _criar_mock_cliente_nuvem(respostas)
        callback = MagicMock()

        import integracao
        with patch.dict("sys.modules", {"cliente_nuvem": mock_cliente}):
            integracao._consolidar_nuvem("aurora", ao_concluir_agente=callback)

        chamadas_pontes = [
            args for args, _ in callback.call_args_list
            if args[0] == "Pontes"
        ]
        assert len(chamadas_pontes) == 1
        _, sucesso, _ = chamadas_pontes[0]
        assert sucesso is False


class TestSemCallback:
    """(e) ao_concluir_agente=None — comportamento padrão sem erros."""

    def test_sem_callback_nao_levanta_excecao(self, env_com_ids):
        mock_cliente = _criar_mock_cliente_nuvem(_respostas_todos_ok())

        import integracao
        with patch.dict("sys.modules", {"cliente_nuvem": mock_cliente}):
            resultado = integracao._consolidar_nuvem("aurora")

        assert resultado.get("status") == "concluida"

    def test_sem_callback_resultado_identico_a_callback_none(self, env_com_ids):
        mock_cliente = _criar_mock_cliente_nuvem(_respostas_todos_ok())
        callback = MagicMock()

        import integracao
        with patch.dict("sys.modules", {"cliente_nuvem": mock_cliente}):
            res_sem = integracao._consolidar_nuvem("aurora")
        with patch.dict("sys.modules", {"cliente_nuvem": mock_cliente}):
            res_com = integracao._consolidar_nuvem("aurora", ao_concluir_agente=callback)

        # Status e recomendação devem ser iguais (scores são iguais)
        assert res_sem.get("status") == res_com.get("status")
        assert res_sem.get("recomendacao") == res_com.get("recomendacao")


class TestCallbackViaCharmarGuardiao:
    """Callback funciona quando passado por chamar_guardiao no modo nuvem."""

    def test_chamar_guardiao_repassa_callback(self, env_com_ids):
        mock_cliente = _criar_mock_cliente_nuvem(_respostas_todos_ok())
        callback = MagicMock()

        import integracao
        with patch.dict("sys.modules", {"cliente_nuvem": mock_cliente}):
            integracao.chamar_guardiao("aurora", fonte="nuvem", ao_concluir_agente=callback)

        assert callback.call_count == 5

    def test_chamar_guardiao_modo_local_ignora_callback(self):
        """No modo local, callback não deve ser chamado."""
        callback = MagicMock()

        import integracao
        integracao.chamar_guardiao("aurora", fonte="local", ao_concluir_agente=callback)

        callback.assert_not_called()


class TestCallbackThreadPrincipal:
    """
    Confirma que o callback é chamado na mesma thread de quem chamou
    _consolidar_nuvem / chamar_guardiao (a thread principal), não dentro
    das threads do ThreadPoolExecutor.
    """

    def test_callback_roda_na_mesma_thread(self, env_com_ids):
        import threading
        import integracao

        thread_chamadora = threading.get_ident()
        threads_do_callback: list[int] = []

        def _cb(nome: str, sucesso: bool, tempo: float):
            threads_do_callback.append(threading.get_ident())

        mock_cliente = _criar_mock_cliente_nuvem(_respostas_todos_ok())
        with patch.dict("sys.modules", {"cliente_nuvem": mock_cliente}):
            integracao._consolidar_nuvem("aurora", ao_concluir_agente=_cb)

        assert len(threads_do_callback) == 5, (
            f"Esperava 5 chamadas ao callback, recebeu {len(threads_do_callback)}"
        )
        for tid in threads_do_callback:
            assert tid == thread_chamadora, (
                f"Callback chamado em thread {tid}, "
                f"esperava thread principal {thread_chamadora}"
            )

    def test_callback_via_chamar_guardiao_thread_principal(self, env_com_ids):
        import threading
        import integracao

        thread_chamadora = threading.get_ident()
        threads_do_callback: list[int] = []

        def _cb(nome: str, sucesso: bool, tempo: float):
            threads_do_callback.append(threading.get_ident())

        mock_cliente = _criar_mock_cliente_nuvem(_respostas_todos_ok())
        with patch.dict("sys.modules", {"cliente_nuvem": mock_cliente}):
            integracao.chamar_guardiao("aurora", fonte="nuvem", ao_concluir_agente=_cb)

        assert len(threads_do_callback) == 5
        for tid in threads_do_callback:
            assert tid == thread_chamadora
