"""
Página: Como funciona
Página inicial do Conecta Conselho — explica o funcionamento do sistema.

AVISO: Todos os dados são SIMULADOS e fictícios.
"""

from __future__ import annotations

import streamlit as st

_AVISO_SIMULADO = "⚠️ Dados simulados — não representam indicadores reais."


def render():
    st.title("📖 Como funciona")
    st.warning(_AVISO_SIMULADO)
    st.info("🚧 Em construção — responsável: Thalyta")
