"""
Definição única das páginas do app Streamlit.

Usada pelo roteador (app.py) e pelos links internos (st.page_link).
As páginas são registradas por função (render), não por arquivo; por isso
st.page_link precisa receber o objeto st.Page, e não o caminho do .py.
O Streamlit identifica cada página pelo url_path, então objetos criados
aqui em chamadas diferentes apontam para a mesma página registrada.

AVISO: Todos os dados são SIMULADOS e fictícios.
"""

from __future__ import annotations

import streamlit as st


def criar_paginas() -> dict[str, st.Page]:
    """Retorna as páginas do app, na ordem do menu lateral."""
    from paginas import analise, como_funciona, mapa, simulador  # type: ignore[import]

    return {
        "como_funciona": st.Page(como_funciona.render, title="Como funciona",         icon="📖", url_path="como-funciona", default=True),
        "analise":       st.Page(analise.render,       title="Análise de Região",     icon="🔍", url_path="analise"),
        "mapa":          st.Page(mapa.render,          title="Mapa ilustrativo",      icon="🗺️", url_path="mapa"),
        "simulador":     st.Page(simulador.render,     title="Simulador de cenários", icon="🧪", url_path="simulador"),
    }
