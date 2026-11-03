"""
conftest.py raiz — garante que o diretório inteli_girls/ esteja no PYTHONPATH
para todos os testes do projeto.
"""
import sys
from pathlib import Path

# Adiciona a raiz do workspace ao sys.path antes de qualquer import de teste
_workspace = Path(__file__).parent
if str(_workspace) not in sys.path:
    sys.path.insert(0, str(_workspace))
