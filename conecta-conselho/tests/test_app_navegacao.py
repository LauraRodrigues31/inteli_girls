"""
Testes de navegação do app Streamlit multi-página.

Verifica que:
  - O roteador (app.py) executa sem exceção via AppTest
  - Cada página individual (como_funciona, analise, mapa, simulador)
    executa sem exceção quando chamada isoladamente via AppTest.from_string

AVISO: Todos os dados são SIMULADOS e fictícios.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Garante que conecta-conselho/ está no sys.path para importar paginas.*
_CC_DIR = Path(__file__).resolve().parent.parent   # conecta-conselho/
_ROOT   = _CC_DIR.parent                            # inteli_girls/

for _p in [str(_ROOT), str(_CC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from streamlit.testing.v1 import AppTest  # noqa: E402

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
_APP_PATH = _CC_DIR / "app.py"


# ---------------------------------------------------------------------------
# Teste do roteador principal
# ---------------------------------------------------------------------------


class TestAppRoteador:
    def test_app_executa_sem_excecao(self):
        """app.py deve carregar e executar sem levantar exceção."""
        at = AppTest.from_file(str(_APP_PATH))
        at.run(timeout=15)
        assert not at.exception, f"app.py levantou exceção: {at.exception}"


# ---------------------------------------------------------------------------
# Testes por página isolada
# ---------------------------------------------------------------------------

def _script_pagina(modulo: str) -> str:
    """Gera o código fonte mínimo para rodar render() de uma página isolada."""
    cc_dir = str(_CC_DIR).replace("\\", "/")
    root_dir = str(_ROOT).replace("\\", "/")
    return (
        f"import sys\n"
        f"sys.path.insert(0, '{root_dir}')\n"
        f"sys.path.insert(0, '{cc_dir}')\n"
        f"from {modulo} import render\n"
        f"render()\n"
    )


@pytest.mark.parametrize("modulo,titulo", [
    ("paginas.como_funciona", "Como funciona"),
    ("paginas.analise",       "Análise de Região"),
    ("paginas.mapa",          "Mapa ilustrativo"),
    ("paginas.simulador",     "Simulador de cenários"),
])
class TestPaginasIsoladas:
    def test_pagina_executa_sem_excecao(self, modulo: str, titulo: str):
        """Cada página deve renderizar sem levantar exceção."""
        at = AppTest.from_string(_script_pagina(modulo))
        at.run(timeout=15)
        assert not at.exception, (
            f"Página '{titulo}' ({modulo}) levantou exceção: {at.exception}"
        )
