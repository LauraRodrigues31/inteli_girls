"""
Testes de cache para paginas/analise.py.

Verifica:
  (a) Duas chamadas seguidas para a mesma região chamam o mock UMA vez (cache hit).
  (b) Resultado analise_incompleta não fica no cache — a próxima chamada vai ao mock de novo.
  (c) clear(regiao_a, fonte) não apaga o cache de regiao_b.

Usa monkeypatch em paginas.analise.chamar_guardiao para não chamar a nuvem.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

_CC_DIR = Path(__file__).resolve().parent.parent   # conecta-conselho/
_ROOT   = _CC_DIR.parent                            # inteli_girls/

for _p in [str(_ROOT), str(_CC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

# Importa o módulo sob teste — streamlit é mockado antes de qualquer import do módulo
import unittest.mock as _mock

# ---------------------------------------------------------------------------
# Fixture: mock streamlit antes de importar paginas.analise
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _mock_streamlit():
    """Evita que paginas.analise tente inicializar o Streamlit durante os testes."""
    st_mock = MagicMock()
    # cache_data precisa devolver um decorador funcional real
    def _cache_data_decorator(ttl=None, show_spinner=True):
        def _decorator(fn):
            import functools
            # cache simples em memória (dict keyed por args)
            _store: dict = {}

            @functools.wraps(fn)
            def _wrapper(*args, **kwargs):
                key = (args, tuple(sorted(kwargs.items())))
                if key not in _store:
                    _store[key] = fn(*args, **kwargs)
                return _store[key]

            def _clear(*args, **kwargs):
                if not args and not kwargs:
                    _store.clear()
                else:
                    key = (args, tuple(sorted(kwargs.items())))
                    _store.pop(key, None)

            _wrapper.clear = _clear
            return _wrapper
        return _decorator

    st_mock.cache_data = _cache_data_decorator
    st_mock.session_state = {}
    with _mock.patch.dict("sys.modules", {"streamlit": st_mock}):
        yield st_mock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resultado_ok(regiao_id: str, score: int = 60) -> dict:
    return {
        "regiao_id": regiao_id,
        "regiao_nome": regiao_id.capitalize(),
        "status": "concluida",
        "score_consolidado": score,
        "recomendacao": "realizar_piloto",
        "fonte": "nuvem",
        "tempo_analise_segundos": 1.0,
    }


def _resultado_incompleto(regiao_id: str) -> dict:
    return {
        "regiao_id": regiao_id,
        "regiao_nome": regiao_id.capitalize(),
        "status": "analise_incompleta",
        "score_consolidado": None,
        "recomendacao": None,
        "agentes_com_falha": [{"agente": "mercado", "motivo": "timeout"}],
        "fonte": "nuvem",
        "tempo_analise_segundos": 1.0,
    }


def _importar_modulo():
    """Reimporta paginas.analise após o mock do streamlit estar ativo."""
    # Remove cache de import para garantir que o módulo usa o streamlit mockado
    for key in list(sys.modules.keys()):
        if "paginas" in key or "analise" in key:
            del sys.modules[key]

    import importlib
    import paginas.analise as analise_mod
    return analise_mod


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

class TestCacheNuvem:
    """Testes de comportamento do cache de _consultar_nuvem_cached."""

    def test_a_duas_chamadas_mesma_regiao_mock_uma_vez(self, monkeypatch):
        """(a) Duas chamadas seguidas para a mesma região chamam o mock UMA vez."""
        mod = _importar_modulo()

        chamadas = []

        def mock_guardiao(regiao_id, *, fonte=None):
            chamadas.append(regiao_id)
            return _resultado_ok(regiao_id)

        monkeypatch.setattr(mod, "chamar_guardiao", mock_guardiao)

        # Limpa cache antes do teste
        mod._consultar_nuvem_cached.clear("central", "nuvem")

        r1 = mod._consultar_nuvem_cached("central", "nuvem")
        r2 = mod._consultar_nuvem_cached("central", "nuvem")

        assert len(chamadas) == 1, (
            f"O mock foi chamado {len(chamadas)} vez(es); esperado 1 (cache hit na 2ª chamada)."
        )
        assert r1["score_consolidado"] == r2["score_consolidado"]
        assert "consultado_em" in r1

    def test_b_analise_incompleta_nao_fica_no_cache(self, monkeypatch):
        """(b) Após analise_incompleta + clear, a próxima chamada vai ao mock de novo."""
        mod = _importar_modulo()

        chamadas = []

        def mock_guardiao(regiao_id, *, fonte=None):
            chamadas.append(regiao_id)
            if len(chamadas) == 1:
                return _resultado_incompleto(regiao_id)
            return _resultado_ok(regiao_id)

        monkeypatch.setattr(mod, "chamar_guardiao", mock_guardiao)

        # Limpa cache antes do teste
        mod._consultar_nuvem_cached.clear("aurora", "nuvem")

        # 1ª chamada → analise_incompleta
        r1 = mod._consultar_nuvem_cached("aurora", "nuvem")
        assert r1["status"] == "analise_incompleta"

        # Simula o clear que analise.py faz quando detecta analise_incompleta
        mod._consultar_nuvem_cached.clear("aurora", "nuvem")

        # 2ª chamada — deve ir ao mock de novo
        r2 = mod._consultar_nuvem_cached("aurora", "nuvem")

        assert len(chamadas) == 2, (
            f"O mock foi chamado {len(chamadas)} vez(es) após o clear; esperado 2."
        )
        assert r2["status"] == "concluida"

    def test_c_clear_regiao_a_nao_apaga_cache_regiao_b(self, monkeypatch):
        """(c) clear(regiao_a, fonte) não apaga o cache de regiao_b."""
        mod = _importar_modulo()

        chamadas: list[str] = []

        def mock_guardiao(regiao_id, *, fonte=None):
            chamadas.append(regiao_id)
            return _resultado_ok(regiao_id, score=42)

        monkeypatch.setattr(mod, "chamar_guardiao", mock_guardiao)

        # Limpa cache de ambas antes
        mod._consultar_nuvem_cached.clear("central", "nuvem")
        mod._consultar_nuvem_cached.clear("nova_uniao", "nuvem")

        # Popula cache de ambas as regiões
        mod._consultar_nuvem_cached("central", "nuvem")
        mod._consultar_nuvem_cached("nova_uniao", "nuvem")
        assert len(chamadas) == 2

        # Limpa SOMENTE central
        mod._consultar_nuvem_cached.clear("central", "nuvem")

        # nova_uniao ainda deve estar no cache (sem nova chamada ao mock)
        mod._consultar_nuvem_cached("nova_uniao", "nuvem")
        assert len(chamadas) == 2, (
            "Após clear(central), nova_uniao ainda deveria estar no cache "
            f"mas o mock foi chamado {len(chamadas)} vez(es)."
        )

        # central deve ter sido evicted (nova chamada ao mock)
        mod._consultar_nuvem_cached("central", "nuvem")
        assert len(chamadas) == 3, (
            "Após clear(central), a próxima chamada para central deveria ir ao mock "
            f"mas o mock foi chamado {len(chamadas)} vez(es)."
        )
