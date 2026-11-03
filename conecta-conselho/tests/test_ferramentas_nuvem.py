"""
Testes de paridade entre as ferramentas originais (tools/tool_<nome>.py) e as
versões de nuvem geradas (gerar_ferramenta_nuvem.py → _build/tool_<nome>_nuvem.py).

Para cada um dos 5 agentes, garante que analisar_<nome>(<regiao_id>) produz
saída IDÊNTICA entre a versão original e a versão gerada, para as 6 regiões
válidas mais 1 região inexistente.

Execução:
    python -m pytest conecta-conselho/tests/test_ferramentas_nuvem.py -v
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------

_ROOT       = Path(__file__).resolve().parent.parent.parent
_TOOLS_DIR  = _ROOT / "tools"
_BUILD_DIR  = _ROOT / "_build"
_SCRIPT_GEN = _ROOT / "scripts" / "gerar_ferramenta_nuvem.py"
_VENV_PYTHON = _ROOT / ".venv" / "Scripts" / "python.exe"

# ---------------------------------------------------------------------------
# Helpers de carregamento
# ---------------------------------------------------------------------------

def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None, f"Não foi possível criar spec para {path}"
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _unpack(result) -> dict:
    """Desempacota ToolResponse (se necessário) para obter o dict de dados."""
    return result.content if hasattr(result, "content") else result


def _gerar_nuvem(nome: str) -> Path:
    """Chama o gerador e retorna o caminho do arquivo gerado."""
    python = str(_VENV_PYTHON) if _VENV_PYTHON.exists() else sys.executable
    result = subprocess.run(
        [python, str(_SCRIPT_GEN), nome],
        capture_output=True, text=True, timeout=30,
        cwd=str(_ROOT),
    )
    assert result.returncode == 0, (
        f"Gerador falhou para '{nome}':\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    saida = _BUILD_DIR / f"tool_{nome}_nuvem.py"
    assert saida.exists(), f"Arquivo gerado não encontrado: {saida}"
    return saida


# ---------------------------------------------------------------------------
# Parametrização dos casos de teste
# ---------------------------------------------------------------------------

_AGENTES = [
    ("engenharia", "analisar_engenharia"),
    ("mercado",    "analisar_mercado"),
    ("social",     "analisar_impacto_social"),
    ("orcamento",  "analisar_orcamento"),
    ("pontes",     "analisar_pontes"),
]

_REGIOES_VALIDAS = ["aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"]
_REGIAO_INVALIDA = "atlantida"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module", params=[a[0] for a in _AGENTES], ids=[a[0] for a in _AGENTES])
def agente_mods(request):
    """
    Fixture que, para cada agente, carrega o módulo original e o módulo nuvem.
    Retorna (nome, fn_name, mod_original, mod_nuvem).
    """
    nome = request.param
    fn_name = dict(_AGENTES)[nome]

    # Garante que a versão nuvem está gerada e actualizada
    nuvem_path = _gerar_nuvem(nome)

    # Carrega original (via .venv python — tem o ADK)
    original_path = _TOOLS_DIR / f"tool_{nome}.py"
    mod_orig = _load_module(original_path, f"orig_{nome}")

    # Carrega nuvem
    mod_nuvem = _load_module(nuvem_path, f"nuvem_{nome}")

    return nome, fn_name, mod_orig, mod_nuvem


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("regiao_id", _REGIOES_VALIDAS)
def test_saida_identica_regioes_validas(agente_mods, regiao_id):
    """
    Para cada agente e cada região válida, a saída do @tool nuvem deve ser
    idêntica à do @tool original após desempacotar ToolResponse.
    """
    nome, fn_name, mod_orig, mod_nuvem = agente_mods
    fn_orig  = getattr(mod_orig,  fn_name)
    fn_nuvem = getattr(mod_nuvem, fn_name)

    orig  = _unpack(fn_orig(regiao_id))
    nuvem = _unpack(fn_nuvem(regiao_id))

    assert orig == nuvem, (
        f"[{nome}][{regiao_id}] Divergência entre original e nuvem.\n"
        f"Original: {orig}\nNuvem: {nuvem}"
    )


def test_saida_identica_regiao_invalida(agente_mods):
    """
    Para regiões não encontradas, o contrato de erro deve ser idêntico
    entre original e nuvem (score=0, confianca=nao_avaliada, erro preenchido).
    """
    nome, fn_name, mod_orig, mod_nuvem = agente_mods
    fn_orig  = getattr(mod_orig,  fn_name)
    fn_nuvem = getattr(mod_nuvem, fn_name)

    orig  = _unpack(fn_orig(_REGIAO_INVALIDA))
    nuvem = _unpack(fn_nuvem(_REGIAO_INVALIDA))

    # Campos críticos do contrato
    assert nuvem["score"]     == 0,            f"[{nome}] score esperado 0, obtido {nuvem['score']}"
    assert nuvem["confianca"] == "nao_avaliada", f"[{nome}] confianca esperada nao_avaliada"
    assert nuvem["erro"]      is not None,      f"[{nome}] campo 'erro' deve estar preenchido"

    # Compara com original campo a campo (ignorando mensagens que podem variar
    # levemente por diferenças no listar_ids_regioes — ordem alfabética vs original)
    assert nuvem["score"]     == orig["score"]
    assert nuvem["confianca"] == orig["confianca"]
    assert nuvem["agente"]    == orig["agente"]
    assert nuvem["simulado"]  == orig["simulado"]
