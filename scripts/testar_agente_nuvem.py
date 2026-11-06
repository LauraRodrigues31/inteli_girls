"""
Testa qualquer um dos 5 agentes do Conecta Conselho pela API de runtime
do IBM watsonx Orchestrate.

AVISO: Todos os dados utilizados neste script são SIMULADOS e FICTÍCIOS.
Os scores esperados são calculados a partir de regioes.json (base simulada).

Uso:
    python scripts/testar_agente_nuvem.py <nome>

Nomes válidos: engenharia, mercado, social, orcamento, pontes

O que o script faz:
  1. Lê WXO_URL do .env e o token do cache de credenciais do orchestrate.
  2. Descobre o agent_id pelo nome do agente via 'orchestrate agents list -v'.
  3. Calcula os scores ESPERADOS rodando a ferramenta local (tools/tool_<nome>.py)
     para as 6 regiões — sem chamar a nuvem para isso.
  4. Executa 3 testes contra o endpoint de runtime:
       T1: região central   → score esperado calculado localmente
       T2: região nova_uniao → score esperado calculado localmente
       T3: região inexistente → score 0, confianca nao_avaliada, erro preenchido
  5. Imprime tabela ✅/❌ no final.

Requisitos Python: requests, pyyaml  (já disponíveis no ambiente do sistema)
Sem hardcode de agent_id ou token no código.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Optional

import requests
import yaml

# ---------------------------------------------------------------------------
# Mapa nome → nome do agente no watsonx Orchestrate
# ---------------------------------------------------------------------------

_NOMES_VALIDOS = ["engenharia", "mercado", "social", "orcamento", "pontes"]

_AGENT_NAMES = {
    "engenharia": "cc_engenharia",
    "mercado":    "cc_mercado",
    "social":     "cc_impacto_social",
    "orcamento":  "cc_orcamento",
    "pontes":     "cc_pontes",
}

# Nome da função @tool para cada agente
_TOOL_FN = {
    "engenharia": "analisar_engenharia",
    "mercado":    "analisar_mercado",
    "social":     "analisar_impacto_social",
    "orcamento":  "analisar_orcamento",
    "pontes":     "analisar_pontes",
}

TIMEOUT = 60  # segundos por chamada REST

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
_SCRIPT_DIR     = Path(__file__).resolve().parent
_ROOT           = _SCRIPT_DIR.parent
_ENV_FILE       = _ROOT / ".env"
_CREDS_FILE     = Path.home() / ".cache" / "orchestrate" / "credentials.yaml"
_ORCHESTRATE    = _ROOT / ".venv" / "Scripts" / "orchestrate.exe"

# ---------------------------------------------------------------------------
# Leitura do .env
# ---------------------------------------------------------------------------

def _ler_env() -> dict[str, str]:
    """Lê o .env e retorna um dicionário de variáveis."""
    result: dict[str, str] = {}
    if not _ENV_FILE.exists():
        return result
    for linha in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        result[chave.strip()] = valor.strip()
    return result


def _get_base_url(env_vars: dict[str, str]) -> str:
    url = env_vars.get("WXO_URL", "").rstrip("/")
    if not url:
        raise RuntimeError(
            "WXO_URL não encontrada no .env. "
            "Exemplo: WXO_URL=https://api.jp-tok.watson-orchestrate.cloud.ibm.com/instances/<ID>"
        )
    # Garante que termina em /v1
    if not url.endswith("/v1"):
        url = url + "/v1"
    return url


# ---------------------------------------------------------------------------
# Token
# ---------------------------------------------------------------------------

def _get_token() -> str:
    """
    Lê o Bearer token do cache de credenciais do orchestrate.
    Nunca imprime o token no stdout.

    ADK 2.19 não expõe 'orchestrate env get-token'; o token é armazenado em:
      ~/.cache/orchestrate/credentials.yaml → auth.<env>.wxo_mcsp_token
    """
    if not _CREDS_FILE.exists():
        raise RuntimeError(
            f"Arquivo de credenciais não encontrado: {_CREDS_FILE}\n"
            "Login expirado: rode orchestrate env activate conecta-conselho --api-key <sua key>"
        )

    data = yaml.safe_load(_CREDS_FILE.read_text(encoding="utf-8"))
    auth = data.get("auth", {}) or {}

    # Tenta 'conecta-conselho' primeiro, depois qualquer entrada com token
    token: Optional[str] = None
    for env_name in ("conecta-conselho", *auth.keys()):
        entry = auth.get(env_name) or {}
        if isinstance(entry, dict):
            token = entry.get("wxo_mcsp_token") or entry.get("token")
            if token:
                break

    if not token or len(token) < 20:
        raise RuntimeError(
            "Login expirado: rode orchestrate env activate conecta-conselho --api-key <sua key>"
        )
    return token


# ---------------------------------------------------------------------------
# Descoberta do agent_id
# ---------------------------------------------------------------------------

def _get_agent_id(agent_name: str) -> str:
    """
    Descobre o agent_id via 'orchestrate agents list -v'.
    Procura pela linha que contém o nome do agente e extrai o UUID.
    """
    cli = str(_ORCHESTRATE) if _ORCHESTRATE.exists() else "orchestrate"
    result = subprocess.run(
        [cli, "agents", "list", "-v"],
        capture_output=True, timeout=30
    )
    output = result.stdout.decode("utf-8", errors="ignore")

    # Tenta parse JSON — a saída pode ser lista ou dict {native:[...], assistant:[...], external:[...]}
    try:
        parsed = json.loads(output)
        # Normaliza para lista plana de agentes
        agent_list: list = []
        if isinstance(parsed, list):
            agent_list = parsed
        elif isinstance(parsed, dict):
            for v in parsed.values():
                if isinstance(v, list):
                    agent_list.extend(v)

        for ag in agent_list:
            if not isinstance(ag, dict):
                continue
            # O campo name pode ter \n no final — strip para comparação
            name = (ag.get("name") or ag.get("agent_name") or "").strip()
            if name == agent_name:
                aid = ag.get("id") or ag.get("agent_id")
                if aid:
                    return str(aid).strip()
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback de texto: UUID na mesma linha que contém o nome do agente
    uuid_pattern = re.compile(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        re.IGNORECASE
    )
    for line in output.splitlines():
        if agent_name in line:
            match = uuid_pattern.search(line)
            if match:
                return match.group()

    # Último recurso: UUID nas linhas próximas a uma linha com o nome
    lines = output.splitlines()
    for i, line in enumerate(lines):
        if agent_name in line:
            for j in range(i, min(i + 10, len(lines))):
                m = uuid_pattern.search(lines[j])
                if m:
                    return m.group()

    stderr = result.stderr.decode("utf-8", errors="ignore")
    raise RuntimeError(
        f"Agente '{agent_name}' não encontrado.\n"
        f"Saída de 'orchestrate agents list -v':\n{output}\n{stderr}\n"
        "Verifique se o agente está publicado e o ambiente está ativo."
    )


# ---------------------------------------------------------------------------
# Cálculo de scores esperados (local)
# ---------------------------------------------------------------------------

_VENV_PYTHON = _ROOT / ".venv" / "Scripts" / "python.exe"


def _load_tool_module(nome: str):
    """
    Carrega tools/tool_<nome>.py pelo caminho do arquivo.
    Usa o venv Python via subprocess para calcular scores — a ferramenta
    depende do ibm_watsonx_orchestrate que está no venv, não no sistema.
    """
    # Tenta importar directamente se o ADK estiver disponível neste Python
    path = _ROOT / "tools" / f"tool_{nome}.py"
    try:
        import ibm_watsonx_orchestrate  # noqa: F401 — só testa se está disponível
        spec = importlib.util.spec_from_file_location(f"tool_{nome}", path)
        assert spec is not None
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod
    except ImportError:
        pass

    # Fallback: importa via venv Python num subprocesso e devolve os resultados
    # em vez de devolver um módulo. Neste caso devolvemos um objecto-simulacro.
    return None  # sinaliza para _calcular_esperados usar o caminho de subprocess


def _unpack(result) -> dict:
    return result.content if hasattr(result, "content") else result


def _calcular_esperados(nome: str) -> dict[str, dict]:
    """
    Calcula os scores esperados rodando a ferramenta local para as 6 regiões.
    Se o ADK não estiver disponível neste Python, usa o venv Python via subprocess.
    """
    regioes = ["aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"]
    fn_name = _TOOL_FN[nome]

    mod = _load_tool_module(nome)
    if mod is not None:
        fn = getattr(mod, fn_name)
        return {rid: _unpack(fn(rid)) for rid in regioes}

    # Caminho via venv Python
    venv_py = str(_VENV_PYTHON) if _VENV_PYTHON.exists() else sys.executable
    tool_path = str(_ROOT / "tools" / f"tool_{nome}.py")

    script = f"""
import importlib.util, json, sys, os
# Redireciona stdout temporariamente para suprimir prints do @tool
import io, contextlib
tool_path = {tool_path!r}
spec = importlib.util.spec_from_file_location("tool", tool_path)
mod = importlib.util.module_from_spec(spec)
# Suprime WARNING/INFO durante o carregamento do módulo
with contextlib.redirect_stdout(open(os.devnull, "w")):
    spec.loader.exec_module(mod)
fn = getattr(mod, {fn_name!r})
regioes = {regioes!r}
result = {{}}
for rid in regioes:
    with contextlib.redirect_stdout(open(os.devnull, "w")):
        r = fn(rid)
    result[rid] = r.content if hasattr(r, "content") else r
# Escreve JSON directamente para o fd original de stdout
sys.stdout.write(json.dumps(result, ensure_ascii=False))
sys.stdout.flush()
"""
    proc = subprocess.run(
        [venv_py, "-c", script],
        capture_output=True, timeout=30
    )
    raw_out = proc.stdout.decode("utf-8", errors="ignore").strip()
    if proc.returncode != 0 or not raw_out:
        stderr_txt = proc.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(
            "Falha ao calcular scores esperados localmente.\n"
            f"stderr: {stderr_txt[:500]}"
        )
    return json.loads(raw_out)


# ---------------------------------------------------------------------------
# Chamada à API de runtime
# ---------------------------------------------------------------------------

def _chat(base_url: str, agent_id: str, token: str, content: str,
          thread_id: Optional[str] = None) -> dict:
    endpoint = f"{base_url}/orchestrate/{agent_id}/chat/completions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body: dict = {"stream": False, "messages": [{"role": "user", "content": content}]}
    if thread_id:
        body["thread_id"] = thread_id

    try:
        resp = requests.post(endpoint, headers=headers, json=body, timeout=TIMEOUT)
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Timeout ({TIMEOUT}s) ao chamar {endpoint}")

    if resp.status_code in (401, 403):
        raise RuntimeError(
            f"Erro de autenticação ({resp.status_code}): "
            "Login expirado: rode orchestrate env activate conecta-conselho --api-key <sua key>"
        )
    resp.raise_for_status()
    return resp.json()


def _extract_reply(payload: dict) -> str:
    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return json.dumps(payload, ensure_ascii=False)


def _extract_json_from_reply(reply: str) -> Optional[dict]:
    """Tenta extrair um dicionário JSON da resposta do agente."""
    # Tenta a resposta inteira
    try:
        return json.loads(reply)
    except (json.JSONDecodeError, ValueError):
        pass
    # Tenta encontrar bloco JSON em ```json ... ```
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", reply, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except (json.JSONDecodeError, ValueError):
            pass
    # Tenta encontrar o primeiro { ... } na string
    m = re.search(r"\{.*\}", reply, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except (json.JSONDecodeError, ValueError):
            pass
    return None


# ---------------------------------------------------------------------------
# Execução dos testes
# ---------------------------------------------------------------------------

def _prompt_para(nome: str, regiao_id: str) -> str:
    """Monta o prompt de acordo com o agente."""
    prompts = {
        "engenharia": f"Analise a engenharia da região {regiao_id}",
        "mercado":    f"Analise o mercado da região {regiao_id}",
        "social":     f"Analise o impacto social da região {regiao_id}",
        "orcamento":  f"Analise o orçamento da região {regiao_id}",
        "pontes":     f"Analise as pontes (parcerias) da região {regiao_id}",
    }
    return prompts[nome]


def _run_tests(nome: str) -> int:
    agent_name = _AGENT_NAMES[nome]
    sep = "=" * 72

    print(sep)
    print(f"  Testes de nuvem — agente {agent_name} ({nome})")
    print(sep)

    # Setup
    env_vars  = _ler_env()
    base_url  = _get_base_url(env_vars)
    token     = _get_token()
    print("[token obtido — não exibido]")

    agent_id  = _get_agent_id(agent_name)
    print(f"[agent_id descoberto — não exibido]")

    # Scores esperados (calculados localmente)
    print("\nCalculando scores esperados localmente ...")
    esperados = _calcular_esperados(nome)
    for rid, p in esperados.items():
        print(f"  {rid:12s} → score={p['score']:3d}  confianca={p['confianca']}")

    results: list[tuple[str, bool, str, str]] = []
    # (label, passou, esperado_str, obtido_str)

    # ------------------------------------------------------------------
    # T1: central
    # ------------------------------------------------------------------
    regiao_t1 = "central"
    score_esp_t1 = esperados[regiao_t1]["score"]
    print(f"\n[ T1 ] {_prompt_para(nome, regiao_t1)} (score esperado: {score_esp_t1}) ...")
    r1 = _chat(base_url, agent_id, token, _prompt_para(nome, regiao_t1))
    reply1 = _extract_reply(r1)
    thread1 = r1.get("thread_id")
    parsed1 = _extract_json_from_reply(reply1)
    score_got1 = parsed1["score"] if parsed1 and "score" in parsed1 else None
    ok1 = (score_got1 == score_esp_t1)
    label1 = f"T1 – {regiao_t1} (score {score_esp_t1})"
    results.append((label1, ok1, str(score_esp_t1), str(score_got1) if score_got1 is not None else "n/a"))
    print(f"  thread_id: {thread1}")
    print(f"  {'✅ PASS' if ok1 else '❌ FAIL'}  esperado={score_esp_t1}  obtido={score_got1}")
    if not ok1:
        print(f"  resposta: {reply1[:300]}")

    # ------------------------------------------------------------------
    # T2: nova_uniao
    # ------------------------------------------------------------------
    regiao_t2 = "nova_uniao"
    score_esp_t2 = esperados[regiao_t2]["score"]
    print(f"\n[ T2 ] {_prompt_para(nome, regiao_t2)} (score esperado: {score_esp_t2}) ...")
    r2 = _chat(base_url, agent_id, token, _prompt_para(nome, regiao_t2))
    reply2 = _extract_reply(r2)
    parsed2 = _extract_json_from_reply(reply2)
    score_got2 = parsed2["score"] if parsed2 and "score" in parsed2 else None
    ok2 = (score_got2 == score_esp_t2)
    label2 = f"T2 – {regiao_t2} (score {score_esp_t2})"
    results.append((label2, ok2, str(score_esp_t2), str(score_got2) if score_got2 is not None else "n/a"))
    print(f"  {'✅ PASS' if ok2 else '❌ FAIL'}  esperado={score_esp_t2}  obtido={score_got2}")
    if not ok2:
        print(f"  resposta: {reply2[:300]}")

    # ------------------------------------------------------------------
    # T3: região inexistente (atlantida)
    # ------------------------------------------------------------------
    regiao_t3 = "atlantida"
    print(f"\n[ T3 ] {_prompt_para(nome, regiao_t3)} (espera score=0, nao_avaliada, erro) ...")
    r3 = _chat(base_url, agent_id, token, _prompt_para(nome, regiao_t3))
    reply3 = _extract_reply(r3)
    parsed3 = _extract_json_from_reply(reply3)

    ok3_score     = (parsed3 is not None and parsed3.get("score") == 0)
    ok3_confianca = (parsed3 is not None and parsed3.get("confianca") == "nao_avaliada")
    ok3_erro      = (parsed3 is not None and parsed3.get("erro") is not None)

    # Fallback de texto se o JSON não foi extraído
    if not ok3_score:
        ok3_score = "\"score\": 0" in reply3 or '"score":0' in reply3
    if not ok3_confianca:
        ok3_confianca = "nao_avaliada" in reply3 or "nao avaliada" in reply3.lower()
    if not ok3_erro:
        ok3_erro = (
            "\"erro\":" in reply3 and "null" not in reply3[reply3.find('"erro"'):reply3.find('"erro"')+30]
        ) or "não encontrada" in reply3.lower() or "nao encontrada" in reply3.lower()

    ok3 = ok3_score and ok3_confianca and ok3_erro
    label3 = f"T3 – {regiao_t3} (score=0, nao_avaliada, erro)"
    results.append((label3, ok3, "0/nao_avaliada/erro", f"score={'0' if ok3_score else '?'}/confianca={'ok' if ok3_confianca else '?'}/erro={'ok' if ok3_erro else '?'}"))
    print(f"  score=0: {'✅' if ok3_score else '❌'}  nao_avaliada: {'✅' if ok3_confianca else '❌'}  erro: {'✅' if ok3_erro else '❌'}")
    print(f"  {'✅ PASS' if ok3 else '❌ FAIL'}")
    if not ok3:
        print(f"  resposta: {reply3[:300]}")

    # ------------------------------------------------------------------
    # Tabela final
    # ------------------------------------------------------------------
    print(f"\n{sep}")
    print("  RESULTADO DOS TESTES")
    print(sep)
    print(f"  {'Status':<8}  {'Teste':<44}  {'Esperado':<22}  {'Obtido'}")
    print(f"  {'-'*8}  {'-'*44}  {'-'*22}  {'-'*20}")
    all_pass = True
    for (label, ok, esp, obt) in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        if not ok:
            all_pass = False
        print(f"  {status:<8}  {label:<44}  {esp:<22}  {obt}")
    print(sep)

    if all_pass:
        print(f"\n  ✅ TODOS OS TESTES PASSARAM para o agente {agent_name}")
    else:
        print(f"\n  ⚠ ALGUM TESTE FALHOU para o agente {agent_name}")
        print("  Se der 401/403: Login expirado — rode:")
        print("    .venv\\Scripts\\orchestrate env activate conecta-conselho --api-key <sua key>")

    return 0 if all_pass else 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in _NOMES_VALIDOS:
        print(f"Uso: python scripts/testar_agente_nuvem.py <nome>")
        print(f"Nomes válidos: {', '.join(_NOMES_VALIDOS)}")
        sys.exit(1)

    nome = sys.argv[1]
    try:
        sys.exit(_run_tests(nome))
    except RuntimeError as exc:
        msg = str(exc)
        print(f"\n[ERRO] {msg}", file=sys.stderr)
        if "expirado" in msg.lower() or "401" in msg or "403" in msg or "autenticação" in msg.lower():
            print("\nLogin expirado: rode orchestrate env activate conecta-conselho --api-key <sua key>")
        sys.exit(2)


if __name__ == "__main__":
    main()
