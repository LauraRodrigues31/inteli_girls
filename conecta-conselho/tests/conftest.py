"""
conftest.py para os testes do Conecta Conselho.

Configura o sys.path antes que o pytest colete os módulos de teste,
garantindo que as importações de tools/ (raiz do repositório) funcionem.
"""
import sys
from pathlib import Path

# Raiz do repositório (inteli_girls/)
_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# conecta-conselho/ — para resolver 'from tools.consultar_regiao import ...'
# que é usado por tool_social.py
_CONECTA_CONSELHO = _REPO_ROOT / "conecta-conselho"
if str(_CONECTA_CONSELHO) not in sys.path:
    sys.path.insert(0, str(_CONECTA_CONSELHO))
