"""
Testes unitários para conecta-conselho/cliente_nuvem.py

Todos os testes usam unittest.mock — nenhum acessa a internet.

Casos cobertos
--------------
1. chamar_agente — resposta com JSON puro no conteúdo
2. chamar_agente — resposta com JSON em bloco markdown
3. chamar_agente — resposta com JSON rodeado de texto
4. chamar_agente — HTTP 401 devolve {"erro": ...}
5. chamar_agente — HTTP 500 devolve {"erro": ...}
6. chamar_agente — timeout devolve {"erro": ...}
7. carregar_credenciais — credenciais ausentes no .env
8. obter_token — segunda chamada reutiliza o token em cache (sem novo POST)

Execução:
    python -m pytest conecta-conselho/tests/test_cliente_nuvem.py -v
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Ajuste de sys.path para que o módulo seja importado a partir da raiz
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).resolve().parent.parent.parent   # inteli_girls/
_CC_DIR = Path(__file__).resolve().parent.parent        # inteli_girls/conecta-conselho/

for _p in [str(_ROOT), str(_CC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cliente_nuvem as cn  # noqa: E402 — import após ajuste de path

# Alias curto para tornar os patches mais legíveis
_MOD = "cliente_nuvem"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_creds():
    """Credenciais fictícias para isolar chamar_agente dos testes de credenciais."""
    return {"WXO_URL": "https://fake.example.com", "WXO_API_KEY": "FAKE_KEY"}


def _mock_token_response(token: str = "TOKEN_FALSO", expires_in: int = 3600):
    """Monta um mock de requests.Response para o endpoint IAM."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"access_token": token, "expires_in": expires_in}
    return resp


def _mock_agent_response(content: str):
    """
    Monta um mock de requests.Response para o endpoint chat/completions
    com *content* no campo choices[0].message.content.
    """
    payload = {
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "thread_id": "thread-abc123",
    }
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = payload
    resp.text = json.dumps(payload)
    return resp


def _reset_token_cache():
    """Garante que o cache de token começa limpo antes de cada teste."""
    cn._TOKEN_CACHE["token"] = None
    cn._TOKEN_CACHE["expira_em"] = 0.0


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def token_cache_limpo():
    """Reseta o cache de token antes e depois de cada teste."""
    _reset_token_cache()
    yield
    _reset_token_cache()


# ---------------------------------------------------------------------------
# Caso 1 — JSON puro na resposta do agente
# ---------------------------------------------------------------------------

def test_chamar_agente_json_puro():
    """chamar_agente devolve o payload completo; extrair_json extrai JSON puro."""
    dados = {"score": 85, "regiao": "central"}
    conteudo = json.dumps(dados)

    with patch(f"{_MOD}.carregar_credenciais", return_value=_mock_creds()), \
         patch(f"{_MOD}.requests.post") as mock_post:

        mock_post.side_effect = [
            _mock_token_response(),          # chamada ao IAM
            _mock_agent_response(conteudo),  # chamada ao agente
        ]

        payload = cn.chamar_agente("agent-uuid-001", "Analise a região central")

    assert "erro" not in payload
    texto = payload["choices"][0]["message"]["content"]
    resultado = cn.extrair_json(texto)
    assert resultado == dados


# ---------------------------------------------------------------------------
# Caso 2 — JSON em bloco markdown
# ---------------------------------------------------------------------------

def test_chamar_agente_json_em_bloco_markdown():
    """extrair_json reconhece bloco ```json … ```."""
    dados = {"score": 72, "confianca": "alta"}
    conteudo = f"Aqui está o resultado:\n```json\n{json.dumps(dados)}\n```"

    with patch(f"{_MOD}.carregar_credenciais", return_value=_mock_creds()), \
         patch(f"{_MOD}.requests.post") as mock_post:

        mock_post.side_effect = [
            _mock_token_response(),
            _mock_agent_response(conteudo),
        ]

        payload = cn.chamar_agente("agent-uuid-002", "Avalie")

    assert "erro" not in payload
    texto = payload["choices"][0]["message"]["content"]
    resultado = cn.extrair_json(texto)
    assert resultado == dados


# ---------------------------------------------------------------------------
# Caso 3 — JSON com texto antes e depois
# ---------------------------------------------------------------------------

def test_chamar_agente_json_com_texto_em_volta():
    """extrair_json encontra { … } mesmo com texto em redor."""
    dados = {"pontuacao": 60, "status": "aprovado"}
    conteudo = f"Análise concluída. {json.dumps(dados)} Fim da análise."

    with patch(f"{_MOD}.carregar_credenciais", return_value=_mock_creds()), \
         patch(f"{_MOD}.requests.post") as mock_post:

        mock_post.side_effect = [
            _mock_token_response(),
            _mock_agent_response(conteudo),
        ]

        payload = cn.chamar_agente("agent-uuid-003", "Verifique")

    assert "erro" not in payload
    texto = payload["choices"][0]["message"]["content"]
    resultado = cn.extrair_json(texto)
    assert resultado == dados


# ---------------------------------------------------------------------------
# Caso 4 — HTTP 401
# ---------------------------------------------------------------------------

def test_chamar_agente_http_401():
    """HTTP 401 do endpoint do agente devolve {"erro": ...}."""
    resp_iam = _mock_token_response()

    resp_agente = MagicMock()
    resp_agente.status_code = 401
    resp_agente.text = "Unauthorized"

    with patch(f"{_MOD}.carregar_credenciais", return_value=_mock_creds()), \
         patch(f"{_MOD}.requests.post") as mock_post:

        mock_post.side_effect = [resp_iam, resp_agente]

        resultado = cn.chamar_agente("agent-uuid-004", "Teste 401")

    assert "erro" in resultado
    assert "401" in resultado["erro"]


# ---------------------------------------------------------------------------
# Caso 5 — HTTP 500
# ---------------------------------------------------------------------------

def test_chamar_agente_http_500():
    """HTTP 500 do endpoint do agente devolve {"erro": ...}."""
    resp_iam = _mock_token_response()

    resp_agente = MagicMock()
    resp_agente.status_code = 500
    resp_agente.text = "Internal Server Error"

    with patch(f"{_MOD}.carregar_credenciais", return_value=_mock_creds()), \
         patch(f"{_MOD}.requests.post") as mock_post:

        mock_post.side_effect = [resp_iam, resp_agente]

        resultado = cn.chamar_agente("agent-uuid-005", "Teste 500")

    assert "erro" in resultado
    assert "500" in resultado["erro"]


# ---------------------------------------------------------------------------
# Caso 6 — Timeout
# ---------------------------------------------------------------------------

def test_chamar_agente_timeout():
    """Timeout na chamada ao agente devolve {"erro": ...}."""
    import requests as _req

    resp_iam = _mock_token_response()

    with patch(f"{_MOD}.carregar_credenciais", return_value=_mock_creds()), \
         patch(f"{_MOD}.requests.post") as mock_post:

        mock_post.side_effect = [resp_iam, _req.exceptions.Timeout()]

        resultado = cn.chamar_agente("agent-uuid-006", "Teste timeout", timeout=5)

    assert "erro" in resultado
    assert "Timeout" in resultado["erro"] or "timeout" in resultado["erro"].lower()


# ---------------------------------------------------------------------------
# Caso 7 — Credenciais ausentes
# ---------------------------------------------------------------------------

def test_carregar_credenciais_ausentes(tmp_path, monkeypatch):
    """Se o .env não contiver WXO_API_KEY, devolve {"erro": ...}."""
    env_file = tmp_path / ".env"
    env_file.write_text("WXO_URL=https://fake.example.com\n", encoding="utf-8")

    # Aponta _ENV_FILE para o ficheiro temporário
    monkeypatch.setattr(cn, "_ENV_FILE", env_file)

    resultado = cn.carregar_credenciais()

    assert "erro" in resultado
    assert "WXO_API_KEY" in resultado["erro"]


def test_carregar_credenciais_sem_env(tmp_path, monkeypatch):
    """Se o .env não existir, devolve {"erro": ...}."""
    monkeypatch.setattr(cn, "_ENV_FILE", tmp_path / "inexistente.env")

    resultado = cn.carregar_credenciais()

    assert "erro" in resultado


# ---------------------------------------------------------------------------
# Caso 8 — Token em cache (segunda chamada não pede novo token)
# ---------------------------------------------------------------------------

def test_obter_token_usa_cache():
    """
    A segunda chamada a obter_token deve reutilizar o token em cache e
    NÃO emitir um novo POST ao IAM.
    """
    with patch(f"{_MOD}.requests.post") as mock_post:
        mock_post.return_value = _mock_token_response(
            token="TOKEN_UNICO", expires_in=3600
        )

        token1 = cn.obter_token("FAKE_API_KEY")
        token2 = cn.obter_token("FAKE_API_KEY")

    # Apenas um POST deve ter sido feito
    assert mock_post.call_count == 1
    assert token1 == token2 == "TOKEN_UNICO"


def test_obter_token_renova_expirado():
    """
    Quando o token armazenado está dentro da margem de expiração,
    obter_token deve buscar um novo.
    """
    with patch(f"{_MOD}.requests.post") as mock_post:
        mock_post.return_value = _mock_token_response(
            token="TOKEN_NOVO", expires_in=3600
        )
        # Força cache com token quase expirado (dentro da margem de 60 s)
        cn._TOKEN_CACHE["token"] = "TOKEN_VELHO"
        cn._TOKEN_CACHE["expira_em"] = time.time() + 30   # só faltam 30 s

        token = cn.obter_token("FAKE_API_KEY")

    assert mock_post.call_count == 1   # renovou
    assert token == "TOKEN_NOVO"


# ---------------------------------------------------------------------------
# Testes adicionais de extrair_json
# ---------------------------------------------------------------------------

def test_extrair_json_json_invalido():
    """Texto sem JSON válido devolve {"erro": ...}."""
    resultado = cn.extrair_json("Isso não é JSON de forma alguma!")
    assert "erro" in resultado


def test_extrair_json_nao_string():
    """Entrada que não é string devolve {"erro": ...}."""
    resultado = cn.extrair_json(None)  # type: ignore[arg-type]
    assert "erro" in resultado
