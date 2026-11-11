"""
Conecta Conselho — Roteador principal (st.navigation / st.Page)

Este arquivo configura o app Streamlit com navegação nativa multi-página.
Todo o conteúdo de análise está em paginas/analise.py.
As demais páginas são responsabilidade de cada integrante do time.

AVISO: Todos os dados são SIMULADOS e fictícios.
Nenhuma API externa é chamada; nenhum mapa é exibido.
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve imports independente do diretório de execução
# ---------------------------------------------------------------------------
_CC_DIR = Path(__file__).resolve().parent
_ROOT   = _CC_DIR.parent

for _p in [str(_ROOT), str(_CC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st

# ---------------------------------------------------------------------------
# Configuração global da página (deve ser chamada antes de qualquer st.*)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Conecta Conselho",
    page_icon="🌐",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Aviso fixo de dados simulados (sidebar, sempre visível)
# ---------------------------------------------------------------------------
st.sidebar.warning("⚠️ Dados simulados — não representam indicadores reais.")

# ---------------------------------------------------------------------------
# Importa a definição das páginas
# ---------------------------------------------------------------------------
from paginas.rotas import criar_paginas  # type: ignore[import]

# ---------------------------------------------------------------------------
# Navegação nativa do Streamlit 1.36+ (páginas definidas em paginas/rotas.py)
# ---------------------------------------------------------------------------
paginas = st.navigation(list(criar_paginas().values()))

paginas.run()
