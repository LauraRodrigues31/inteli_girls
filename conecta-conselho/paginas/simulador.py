"""
Página: Simulador de cenários
Permite simular cenários hipotéticos de expansão de conectividade.

AVISO: Todos os dados são SIMULADOS e fictícios.
"""

from __future__ import annotations

import streamlit as st

_AVISO_SIMULADO = "⚠️ Dados simulados — não representam indicadores reais."


def render():
    st.title("🧪 Simulador de cenários")
    st.warning(_AVISO_SIMULADO)
    st.info("🚧 Em construção — responsável: Gabi")
