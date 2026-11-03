"""
Testes do modo nuvem em conecta-conselho/integracao.py.

Usa mocks de cliente_nuvem.chamar_agente para simular o IBM watsonx Orchestrate
sem fazer nenhuma chamada de rede. Todos os testes são offline.

Cenários cobertos:
  1. 5 agentes OK — resultado idêntico ao modo local para aurora
  2. 1 agente com erro HTTP — analise_incompleta
  3. IDs de agente ausentes no .env — analise_incompleta
  4. Resposta em bloco markdown — parseada corretamente

AVISO: Nenhum teste acessa a internet.
"""

from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Configuração de paths
# ---------------------------------------------------------------------------

_CC_DIR = Path(__file__).resolve().parent.parent          # conecta-conselho/
_ROOT   = _CC_DIR.parent                                   # inteli_girls/

for _p in [str(_ROOT), str(_CC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------------
# Dados de referência — aurora local (scores reais das tools)
# Os scores abaixo são os valores deterministicos das tools locais para aurora.
# mercado=52, impacto_social=38, engenharia=74, orcamento=78, pontes=64
# score_consolidado = round(52*0.20 + 38*0.20 + 74*0.25 + 78*0.25 + 64*0.10) = 62
# ---------------------------------------------------------------------------

_AURORA_PARECERES = {
    "mercado": {
        "score": 52,
        "confianca": "alta",
        "agente": "mercado",
        "regiao_id": "aurora",
        "regiao_nome": "Região Aurora",
        "justificativa": "Mercado com demanda moderada.",
        "riscos": [],
        "erro": None,
    },
    "impacto_social": {
        "score": 38,
        "confianca": "alta",
        "agente": "impacto_social",
        "regiao_id": "aurora",
        "regiao_nome": "Região Aurora",
        "justificativa": "Impacto social moderado.",
        "riscos": [],
        "erro": None,
    },
    "engenharia": {
        "score": 74,
        "confianca": "alta",
        "agente": "engenharia",
        "regiao_id": "aurora",
        "regiao_nome": "Região Aurora",
        "justificativa": "Viabilidade técnica boa.",
        "riscos": [],
        "erro": None,
    },
    "orcamento": {
        "score": 78,
        "confianca": "alta",
        "agente": "orcamento",
        "regiao_id": "aurora",
        "regiao_nome": "Região Aurora",
        "justificativa": "Orçamento adequado.",
        "riscos": [],
        "erro": None,
    },
    "pontes": {
        "score": 64,
        "confianca": "alta",
        "agente": "pontes",
        "regiao_id": "aurora",
        "regiao_nome": "Região Aurora",
        "justificativa": "Boas parcerias identificadas.",
        "riscos": [],
        "erro": None,
    },
}

# Mapa de chave de parecer -> variável de ambiente do agent_id (igual ao integracao.py)
_AGENTE_ENV = {
    "mercado":        "CC_AGENT_ID_MERCADO",
    "impacto_social": "CC_AGENT_ID_SOCIAL",
    "engenharia":     "CC_AGENT_ID_ENGENHARIA",
    "orcamento":      "CC_AGENT_ID_ORCAMENTO",
    "pontes":         "CC_AGENT_ID_PONTES",
}

_IDS_FAKE = {env: f"agent-fake-{env.lower().replace('_','-')}" for env in _AGENTE_ENV.values()}


# ---------------------------------------------------------------------------
# Helpers para montar módulo cliente_nuvem falso
# ---------------------------------------------------------------------------

def _fazer_resposta_api(parecer_dict: dict) -> dict:
    """Monta a estrutura choices[0].message.content com o JSON do parecer."""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(parecer_dict, ensure_ascii=False)
                }
            }
        ]
    }


def _fazer_resposta_markdown(parecer_dict: dict) -> dict:
    """Monta resposta com o JSON embrulhado em bloco markdown."""
    conteudo_md = "```json\n" + json.dumps(parecer_dict, ensure_ascii=False) + "\n```"
    return {
        "choices": [
            {
                "message": {
                    "content": conteudo_md
                }
            }
        ]
    }


def _criar_cliente_nuvem_mock(respostas: dict[str, dict | Exception]) -> types.ModuleType:
    """
    Cria um módulo cliente_nuvem falso.
    respostas: mapa de agent_id_fake -> dict de resposta API ou Exception a levantar.
    extrair_json: usa json.loads básico (sem ADK).
    """
    mod = types.ModuleType("cliente_nuvem")

    def _chamar_agente(agent_id: str, mensagem: str) -> dict:
        resp = respostas.get(agent_id)
        if isinstance(resp, Exception):
            raise resp
        if resp is None:
            raise ValueError(f"agent_id '{agent_id}' não configurado no mock")
        return resp

    def _extrair_json(conteudo: str) -> dict:
        """Extrai JSON de conteúdo (aceita bloco markdown)."""
        s = conteudo.strip()
        if s.startswith("```"):
            linhas = s.splitlines()
            linhas = linhas[1:]
            if linhas and linhas[-1].strip() == "```":
                linhas = linhas[:-1]
            s = "\n".join(linhas).strip()
        if not s.startswith("{"):
            inicio = s.find("{")
            fim = s.rfind("}")
            if inicio != -1 and fim != -1 and fim > inicio:
                s = s[inicio:fim + 1]
        return json.loads(s)

    mod.chamar_agente = _chamar_agente
    mod.extrair_json = _extrair_json
    return mod


# ---------------------------------------------------------------------------
# Fixture de ambiente com IDs configurados
# ---------------------------------------------------------------------------

@pytest.fixture
def env_com_ids(monkeypatch):
    """Configura os 5 agent IDs falsos no ambiente e ativa modo nuvem."""
    monkeypatch.setenv("CC_MODO", "nuvem")
    for env_var, fake_id in _IDS_FAKE.items():
        monkeypatch.setenv(env_var, fake_id)
    yield


@pytest.fixture
def env_sem_ids(monkeypatch):
    """Remove todos os IDs de agente do ambiente; CC_MODO=nuvem."""
    monkeypatch.setenv("CC_MODO", "nuvem")
    for env_var in _AGENTE_ENV.values():
        monkeypatch.delenv(env_var, raising=False)
    yield


# ---------------------------------------------------------------------------
# Cenário 1 — 5 agentes OK — resultado igual ao local
# ---------------------------------------------------------------------------

class TestNuvem5AgentesOK:
    """Todos os 5 agentes respondem corretamente; resultado deve ser idêntico ao local."""

    def test_status_concluida(self, env_com_ids):
        respostas = {
            _IDS_FAKE[env]: _fazer_resposta_api(_AURORA_PARECERES[chave])
            for chave, env in _AGENTE_ENV.items()
        }
        mod_mock = _criar_cliente_nuvem_mock(respostas)

        with patch.dict(sys.modules, {"cliente_nuvem": mod_mock}):
            from integracao import chamar_guardiao
            resultado = chamar_guardiao("aurora", fonte="nuvem")

        assert resultado["status"] == "concluida"

    def test_score_igual_ao_local(self, env_com_ids):
        respostas = {
            _IDS_FAKE[env]: _fazer_resposta_api(_AURORA_PARECERES[chave])
            for chave, env in _AGENTE_ENV.items()
        }
        mod_mock = _criar_cliente_nuvem_mock(respostas)

        with patch.dict(sys.modules, {"cliente_nuvem": mod_mock}):
            from integracao import chamar_guardiao
            resultado_nuvem = chamar_guardiao("aurora", fonte="nuvem")

        from integracao import chamar_guardiao as cg_local
        resultado_local = cg_local("aurora", fonte="local")

        assert resultado_nuvem["score_consolidado"] == resultado_local["score_consolidado"], (
            f"Score nuvem {resultado_nuvem['score_consolidado']} != local {resultado_local['score_consolidado']}"
        )

    def test_recomendacao_igual_ao_local(self, env_com_ids):
        respostas = {
            _IDS_FAKE[env]: _fazer_resposta_api(_AURORA_PARECERES[chave])
            for chave, env in _AGENTE_ENV.items()
        }
        mod_mock = _criar_cliente_nuvem_mock(respostas)

        with patch.dict(sys.modules, {"cliente_nuvem": mod_mock}):
            from integracao import chamar_guardiao
            resultado = chamar_guardiao("aurora", fonte="nuvem")

        assert resultado["recomendacao"] == "realizar_piloto"

    def test_fonte_e_nuvem(self, env_com_ids):
        respostas = {
            _IDS_FAKE[env]: _fazer_resposta_api(_AURORA_PARECERES[chave])
            for chave, env in _AGENTE_ENV.items()
        }
        mod_mock = _criar_cliente_nuvem_mock(respostas)

        with patch.dict(sys.modules, {"cliente_nuvem": mod_mock}):
            from integracao import chamar_guardiao
            resultado = chamar_guardiao("aurora", fonte="nuvem")

        assert resultado.get("fonte") == "nuvem"

    def test_tempo_analise_presente(self, env_com_ids):
        respostas = {
            _IDS_FAKE[env]: _fazer_resposta_api(_AURORA_PARECERES[chave])
            for chave, env in _AGENTE_ENV.items()
        }
        mod_mock = _criar_cliente_nuvem_mock(respostas)

        with patch.dict(sys.modules, {"cliente_nuvem": mod_mock}):
            from integracao import chamar_guardiao
            resultado = chamar_guardiao("aurora", fonte="nuvem")

        assert "tempo_analise_segundos" in resultado
        assert isinstance(resultado["tempo_analise_segundos"], (int, float))

    def test_nenhum_token_ou_id_nos_campos(self, env_com_ids):
        """Garante que agent IDs falsos não aparecem nos campos do resultado."""
        respostas = {
            _IDS_FAKE[env]: _fazer_resposta_api(_AURORA_PARECERES[chave])
            for chave, env in _AGENTE_ENV.items()
        }
        mod_mock = _criar_cliente_nuvem_mock(respostas)

        with patch.dict(sys.modules, {"cliente_nuvem": mod_mock}):
            from integracao import chamar_guardiao
            resultado = chamar_guardiao("aurora", fonte="nuvem")

        resultado_str = json.dumps(resultado, ensure_ascii=False)
        for fake_id in _IDS_FAKE.values():
            assert fake_id not in resultado_str, (
                f"Agent ID '{fake_id}' não deve aparecer no resultado"
            )


# ---------------------------------------------------------------------------
# Cenário 2 — 1 agente com erro — analise_incompleta
# ---------------------------------------------------------------------------

class TestNuvem1AgenteFalhando:
    """Um dos agentes levanta exceção; resultado deve ser analise_incompleta."""

    def _montar_respostas_com_falha(self, agente_com_falha: str) -> dict:
        """Monta respostas com um agente levantando exceção HTTP."""
        respostas = {}
        for chave, env in _AGENTE_ENV.items():
            fake_id = _IDS_FAKE[env]
            if chave == agente_com_falha:
                respostas[fake_id] = ConnectionError(
                    f"HTTP 500 — agente '{chave}' indisponível"
                )
            else:
                respostas[fake_id] = _fazer_resposta_api(_AURORA_PARECERES[chave])
        return respostas

    @pytest.mark.parametrize("agente_falho", list(_AGENTE_ENV.keys()))
    def test_analise_incompleta_quando_agente_falha(self, env_com_ids, agente_falho):
        respostas = self._montar_respostas_com_falha(agente_falho)
        mod_mock = _criar_cliente_nuvem_mock(respostas)

        with patch.dict(sys.modules, {"cliente_nuvem": mod_mock}):
            from integracao import chamar_guardiao
            resultado = chamar_guardiao("aurora", fonte="nuvem")

        assert resultado["status"] == "analise_incompleta", (
            f"Esperado analise_incompleta com agente '{agente_falho}' falhando, "
            f"obtido '{resultado['status']}'"
        )

    @pytest.mark.parametrize("agente_falho", list(_AGENTE_ENV.keys()))
    def test_recomendacao_null_quando_agente_falha(self, env_com_ids, agente_falho):
        respostas = self._montar_respostas_com_falha(agente_falho)
        mod_mock = _criar_cliente_nuvem_mock(respostas)

        with patch.dict(sys.modules, {"cliente_nuvem": mod_mock}):
            from integracao import chamar_guardiao
            resultado = chamar_guardiao("aurora", fonte="nuvem")

        assert resultado["recomendacao"] is None

    @pytest.mark.parametrize("agente_falho", list(_AGENTE_ENV.keys()))
    def test_agentes_com_falha_preenchido(self, env_com_ids, agente_falho):
        respostas = self._montar_respostas_com_falha(agente_falho)
        mod_mock = _criar_cliente_nuvem_mock(respostas)

        with patch.dict(sys.modules, {"cliente_nuvem": mod_mock}):
            from integracao import chamar_guardiao
            resultado = chamar_guardiao("aurora", fonte="nuvem")

        assert "agentes_com_falha" in resultado
        nomes_falhos = [af["agente"] for af in resultado["agentes_com_falha"]]
        assert agente_falho in nomes_falhos, (
            f"Agente '{agente_falho}' deve aparecer em agentes_com_falha: {nomes_falhos}"
        )

    def test_sem_excecao_mesmo_com_falha(self, env_com_ids):
        """Falha de agente não deve propagar exceção — deve retornar dict."""
        respostas = self._montar_respostas_com_falha("orcamento")
        mod_mock = _criar_cliente_nuvem_mock(respostas)

        with patch.dict(sys.modules, {"cliente_nuvem": mod_mock}):
            from integracao import chamar_guardiao
            try:
                resultado = chamar_guardiao("aurora", fonte="nuvem")
            except Exception as exc:
                pytest.fail(f"Não deveria levantar exceção, mas levantou: {exc}")

        assert isinstance(resultado, dict)


# ---------------------------------------------------------------------------
# Cenário 3 — IDs ausentes no .env — analise_incompleta
# ---------------------------------------------------------------------------

class TestNuvemIDsAusentes:
    """Sem agent IDs no .env, todos os agentes falham e resultado é analise_incompleta."""

    def test_todos_agentes_falham_sem_ids(self, env_sem_ids):
        # O módulo cliente_nuvem não é invocado com IDs reais; usamos um mock simples
        mod_mock = _criar_cliente_nuvem_mock({})  # sem respostas configuradas

        with patch.dict(sys.modules, {"cliente_nuvem": mod_mock}):
            from integracao import chamar_guardiao
            resultado = chamar_guardiao("aurora", fonte="nuvem")

        assert resultado["status"] == "analise_incompleta"

    def test_recomendacao_null_sem_ids(self, env_sem_ids):
        mod_mock = _criar_cliente_nuvem_mock({})

        with patch.dict(sys.modules, {"cliente_nuvem": mod_mock}):
            from integracao import chamar_guardiao
            resultado = chamar_guardiao("aurora", fonte="nuvem")

        assert resultado["recomendacao"] is None

    def test_cinco_agentes_com_falha_sem_ids(self, env_sem_ids):
        mod_mock = _criar_cliente_nuvem_mock({})

        with patch.dict(sys.modules, {"cliente_nuvem": mod_mock}):
            from integracao import chamar_guardiao
            resultado = chamar_guardiao("aurora", fonte="nuvem")

        assert "agentes_com_falha" in resultado
        assert len(resultado["agentes_com_falha"]) == 5

    def test_verificar_credenciais_nuvem_detecta_ids_ausentes(self, env_sem_ids):
        from integracao import _verificar_credenciais_nuvem
        ok, aviso = _verificar_credenciais_nuvem()
        assert ok is False
        assert aviso, "Aviso deve descrever quais IDs estão ausentes"

    def test_verificar_credenciais_nuvem_ok_com_ids(self, env_com_ids):
        from integracao import _verificar_credenciais_nuvem
        ok, aviso = _verificar_credenciais_nuvem()
        assert ok is True
        assert aviso == ""

    def test_sem_excecao_sem_ids(self, env_sem_ids):
        """Ausência de IDs não deve levantar exceção."""
        mod_mock = _criar_cliente_nuvem_mock({})

        with patch.dict(sys.modules, {"cliente_nuvem": mod_mock}):
            from integracao import chamar_guardiao
            try:
                resultado = chamar_guardiao("aurora", fonte="nuvem")
            except Exception as exc:
                pytest.fail(f"Não deveria levantar exceção, mas levantou: {exc}")
        assert isinstance(resultado, dict)


# ---------------------------------------------------------------------------
# Cenário 4 — Resposta em bloco markdown — parseada corretamente
# ---------------------------------------------------------------------------

class TestNuvemMarkdownResponse:
    """Agente responde com JSON embrulhado em bloco markdown; deve ser parseado corretamente."""

    def test_markdown_nao_quebra_parse(self, env_com_ids):
        """JSON em bloco markdown deve ser extraído e consolidado normalmente."""
        respostas = {}
        for chave, env in _AGENTE_ENV.items():
            fake_id = _IDS_FAKE[env]
            # Metade em markdown, metade em JSON puro
            if chave in ("mercado", "orcamento"):
                respostas[fake_id] = _fazer_resposta_markdown(_AURORA_PARECERES[chave])
            else:
                respostas[fake_id] = _fazer_resposta_api(_AURORA_PARECERES[chave])

        mod_mock = _criar_cliente_nuvem_mock(respostas)

        with patch.dict(sys.modules, {"cliente_nuvem": mod_mock}):
            from integracao import chamar_guardiao
            resultado = chamar_guardiao("aurora", fonte="nuvem")

        assert resultado["status"] == "concluida", (
            f"Resposta markdown deve ser parsedada corretamente, obtido '{resultado['status']}'"
        )
        assert resultado["score_consolidado"] == 62

    def test_markdown_com_bloco_json_explicitamente_rotulado(self, env_com_ids):
        """Bloco ```json deve ser reconhecido e extraído."""
        parecer = _AURORA_PARECERES["mercado"].copy()
        conteudo = "```json\n" + json.dumps(parecer) + "\n```"
        respostas_api = {
            _IDS_FAKE[env]: (
                {"choices": [{"message": {"content": conteudo}}]}
                if chave == "mercado"
                else _fazer_resposta_api(_AURORA_PARECERES[chave])
            )
            for chave, env in _AGENTE_ENV.items()
        }
        mod_mock = _criar_cliente_nuvem_mock(respostas_api)

        with patch.dict(sys.modules, {"cliente_nuvem": mod_mock}):
            from integracao import chamar_guardiao
            resultado = chamar_guardiao("aurora", fonte="nuvem")

        assert resultado["status"] == "concluida"

    def test_todos_markdown_resultado_igual_todos_json(self, env_com_ids):
        """Resultado deve ser idêntico independente de markdown ou JSON puro."""
        respostas_md = {
            _IDS_FAKE[env]: _fazer_resposta_markdown(_AURORA_PARECERES[chave])
            for chave, env in _AGENTE_ENV.items()
        }
        respostas_json = {
            _IDS_FAKE[env]: _fazer_resposta_api(_AURORA_PARECERES[chave])
            for chave, env in _AGENTE_ENV.items()
        }
        mod_md   = _criar_cliente_nuvem_mock(respostas_md)
        mod_json = _criar_cliente_nuvem_mock(respostas_json)

        with patch.dict(sys.modules, {"cliente_nuvem": mod_md}):
            from integracao import chamar_guardiao
            r_md = chamar_guardiao("aurora", fonte="nuvem")

        with patch.dict(sys.modules, {"cliente_nuvem": mod_json}):
            from integracao import chamar_guardiao as cg2
            r_json = cg2("aurora", fonte="nuvem")

        assert r_md["score_consolidado"] == r_json["score_consolidado"]
        assert r_md["recomendacao"] == r_json["recomendacao"]
        assert r_md["status"] == r_json["status"]


# ---------------------------------------------------------------------------
# Cenário 5 — Ambiente CC_MODO controla o modo padrão
# ---------------------------------------------------------------------------

class TestControleModoPorEnv:
    """Testa que CC_MODO=nuvem ativa o modo nuvem e CC_MODO=local usa local."""

    def test_cc_modo_nuvem_usa_cliente_nuvem(self, env_com_ids):
        """CC_MODO=nuvem deve invocar cliente_nuvem (fonte='nuvem' no resultado)."""
        respostas = {
            _IDS_FAKE[env]: _fazer_resposta_api(_AURORA_PARECERES[chave])
            for chave, env in _AGENTE_ENV.items()
        }
        mod_mock = _criar_cliente_nuvem_mock(respostas)

        with patch.dict(sys.modules, {"cliente_nuvem": mod_mock}):
            from integracao import chamar_guardiao
            # env_com_ids já setou CC_MODO=nuvem; não passa fonte explícita
            resultado = chamar_guardiao("aurora")

        assert resultado.get("fonte") == "nuvem"

    def test_fonte_parametro_sobrepoe_cc_modo(self, env_com_ids, monkeypatch):
        """Parâmetro fonte='local' deve sobrescrever CC_MODO=nuvem."""
        monkeypatch.setenv("CC_MODO", "nuvem")

        from integracao import chamar_guardiao
        resultado = chamar_guardiao("aurora", fonte="local")
        assert resultado.get("fonte") == "local"
