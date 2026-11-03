"""
Camada de conexão com o IBM watsonx Orchestrate (modo nuvem).

Funções públicas
----------------
carregar_credenciais() -> dict
    Lê WXO_URL e WXO_API_KEY do arquivo .env na raiz do projecto.
    Devolve {"WXO_URL": ..., "WXO_API_KEY": ...} ou {"erro": "..."}.

obter_token(api_key: str) -> str | dict
    Troca a API key por um Bearer token IBM IAM.
    Mantém cache em memória; o token é reutilizado até 60 s antes de expirar.
    Devolve o token (str) ou {"erro": "..."}.

chamar_agente(agent_id, mensagem, timeout=180) -> dict
    POST {WXO_URL}/v1/orchestrate/{agent_id}/chat/completions
    Devolve o payload JSON completo ou {"erro": "..."}.

extrair_json(texto) -> dict
    Extrai o primeiro objeto JSON de uma string.
    Aceita JSON puro, bloco ```json … ``` ou texto com JSON intercalado.
    Devolve o dict ou {"erro": "..."}.

Regras gerais
-------------
- Toda falha devolve {"erro": "<mensagem clara>"} — nunca lança excepção.
- O token e a API key nunca são impressos nem registados.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Union

import requests
from dotenv import dotenv_values

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).resolve().parent.parent   # raiz do projecto (inteli_girls/)
_ENV_FILE = _ROOT / ".env"

# ---------------------------------------------------------------------------
# Cache do token IBM IAM
# ---------------------------------------------------------------------------

_TOKEN_CACHE: dict[str, object] = {
    "token": None,       # str | None
    "expira_em": 0.0,    # epoch seconds
}

_TOKEN_MARGEM_S = 60     # renova se faltar ≤ 60 s para expirar
_IAM_URL = "https://iam.cloud.ibm.com/identity/token"

# ---------------------------------------------------------------------------
# 1. carregar_credenciais
# ---------------------------------------------------------------------------


def carregar_credenciais() -> dict:
    """
    Lê WXO_URL e WXO_API_KEY do arquivo .env na raiz do projecto usando
    python-dotenv.  Não lança excepção: erros são devolvidos como
    {"erro": "..."}.

    Returns:
        {"WXO_URL": str, "WXO_API_KEY": str}  em caso de sucesso, ou
        {"erro": str}  se alguma variável estiver ausente ou o ficheiro não
        existir.
    """
    if not _ENV_FILE.exists():
        return {"erro": f"Ficheiro .env não encontrado em {_ENV_FILE}"}

    valores = dotenv_values(str(_ENV_FILE))

    ausentes = [k for k in ("WXO_URL", "WXO_API_KEY") if not valores.get(k)]
    if ausentes:
        return {
            "erro": (
                f"Variável(is) ausente(s) no .env: {', '.join(ausentes)}. "
                "Adicione WXO_URL e WXO_API_KEY ao ficheiro .env na raiz do projecto."
            )
        }

    return {
        "WXO_URL": valores["WXO_URL"].rstrip("/"),
        "WXO_API_KEY": valores["WXO_API_KEY"],
    }


# ---------------------------------------------------------------------------
# 2. obter_token
# ---------------------------------------------------------------------------


def obter_token(api_key: str) -> Union[str, dict]:
    """
    Troca a *api_key* IBM Cloud por um Bearer token IAM.

    O token é mantido em cache e reutilizado até _TOKEN_MARGEM_S segundos
    antes de expirar.  A API key nunca é exposta em logs ou prints.

    Args:
        api_key: Chave de API IBM Cloud.

    Returns:
        O token como ``str`` em caso de sucesso, ou ``{"erro": str}`` em caso
        de falha.
    """
    agora = time.time()
    if _TOKEN_CACHE["token"] and agora < float(_TOKEN_CACHE["expira_em"]) - _TOKEN_MARGEM_S:
        return str(_TOKEN_CACHE["token"])

    try:
        resp = requests.post(
            _IAM_URL,
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": api_key,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
    except requests.exceptions.Timeout:
        return {"erro": "Timeout ao obter token IBM IAM (30 s)."}
    except requests.exceptions.RequestException as exc:
        return {"erro": f"Erro de rede ao obter token IBM IAM: {type(exc).__name__}"}

    if resp.status_code != 200:
        return {
            "erro": (
                f"IBM IAM devolveu HTTP {resp.status_code} ao solicitar token. "
                "Verifique se WXO_API_KEY está correcta."
            )
        }

    try:
        payload = resp.json()
        token = payload["access_token"]
        expires_in = int(payload.get("expires_in", 3600))
    except (KeyError, ValueError, TypeError):
        return {"erro": "Resposta inesperada do IBM IAM (campo access_token ausente)."}

    _TOKEN_CACHE["token"] = token
    _TOKEN_CACHE["expira_em"] = agora + expires_in

    return token


# ---------------------------------------------------------------------------
# 3. chamar_agente
# ---------------------------------------------------------------------------


def chamar_agente(agent_id: str, mensagem: str, timeout: int = 180) -> dict:
    """
    Chama qualquer agente no watsonx Orchestrate via
    POST {WXO_URL}/v1/orchestrate/{agent_id}/chat/completions

    Args:
        agent_id:  UUID do agente (obtido via ``orchestrate agents list -v``).
        mensagem:  Texto da mensagem do utilizador.
        timeout:   Segundos para aguardar a resposta (padrão 180).

    Returns:
        Payload JSON completo da API (dict) ou {"erro": str} em caso de falha.
    """
    creds = carregar_credenciais()
    if "erro" in creds:
        return creds

    token = obter_token(creds["WXO_API_KEY"])
    if isinstance(token, dict):   # {"erro": ...}
        return token

    endpoint = f"{creds['WXO_URL']}/v1/orchestrate/{agent_id}/chat/completions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {
        "stream": False,
        "messages": [{"role": "user", "content": mensagem}],
    }

    try:
        resp = requests.post(endpoint, headers=headers, json=body, timeout=timeout)
    except requests.exceptions.Timeout:
        return {"erro": f"Timeout ({timeout} s) ao chamar o agente {agent_id}."}
    except requests.exceptions.RequestException as exc:
        return {"erro": f"Erro de rede ao chamar o agente: {type(exc).__name__}"}

    if resp.status_code != 200:
        return {
            "erro": (
                f"Agente {agent_id} devolveu HTTP {resp.status_code}. "
                f"Detalhe: {resp.text[:200]}"
            )
        }

    try:
        return resp.json()
    except ValueError:
        return {"erro": "A resposta do agente não é JSON válido."}


# ---------------------------------------------------------------------------
# 4. extrair_json
# ---------------------------------------------------------------------------


def extrair_json(texto: str) -> dict:
    """
    Extrai o primeiro objecto JSON de *texto*.

    Tenta, pela ordem:
      1. Parse directo (o texto inteiro é JSON).
      2. Primeiro bloco ```json … ``` ou ``` … ```.
      3. Primeira ocorrência de ``{ … }`` na string.

    Args:
        texto: String que contém (ou é) um objecto JSON.

    Returns:
        O dict extraído ou {"erro": "Não foi possível extrair JSON da resposta."}.
    """
    if not isinstance(texto, str):
        return {"erro": "Não foi possível extrair JSON da resposta."}

    # 1. Tentativa directa
    try:
        resultado = json.loads(texto)
        if isinstance(resultado, dict):
            return resultado
    except (json.JSONDecodeError, ValueError):
        pass

    # 2. Bloco markdown ```json … ``` ou ``` … ```
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.DOTALL)
    if m:
        try:
            resultado = json.loads(m.group(1))
            if isinstance(resultado, dict):
                return resultado
        except (json.JSONDecodeError, ValueError):
            pass

    # 3. Primeira ocorrência de { … }
    m = re.search(r"\{.*\}", texto, re.DOTALL)
    if m:
        try:
            resultado = json.loads(m.group())
            if isinstance(resultado, dict):
                return resultado
        except (json.JSONDecodeError, ValueError):
            pass

    return {"erro": "Não foi possível extrair JSON da resposta."}
