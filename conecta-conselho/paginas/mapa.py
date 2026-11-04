"""
Página: Mapa ilustrativo
Visualização geográfica das regiões analisadas.

AVISO: Todos os dados são SIMULADOS e fictícios.
"""

from __future__ import annotations

import streamlit as st

_AVISO_SIMULADO = "⚠️ Dados simulados — não representam indicadores reais."


def render():
    st.title("🗺️ Mapa ilustrativo")
    st.warning(_AVISO_SIMULADO)
    st.info("🚧 Em construção — responsável: Milena")
