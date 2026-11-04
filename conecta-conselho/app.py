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
# Importa as funções render de cada página
# ---------------------------------------------------------------------------
from paginas import como_funciona, analise, mapa, simulador  # type: ignore[import]

# ---------------------------------------------------------------------------
# Navegação nativa do Streamlit 1.36+
# ---------------------------------------------------------------------------
paginas = st.navigation(
    [
        st.Page(como_funciona.render, title="Como funciona",         icon="📖", default=True),
        st.Page(analise.render,       title="Análise de Região",     icon="🔍"),
        st.Page(mapa.render,          title="Mapa ilustrativo",      icon="🗺️"),
        st.Page(simulador.render,     title="Simulador de cenários", icon="🧪"),
    ]
)

paginas.run()
