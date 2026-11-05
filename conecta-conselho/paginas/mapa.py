"""
Página: Mapa ilustrativo
Visualização esquemática das regiões em coordenadas polares, centradas no backbone.

AVISO: Posições são ILUSTRATIVAS — regiões fictícias sem coordenadas geográficas reais.
Distâncias ao backbone são as da base de dados simulada.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve imports
# ---------------------------------------------------------------------------
_CC_DIR = Path(__file__).resolve().parent.parent
_ROOT   = _CC_DIR.parent

for _p in [str(_ROOT), str(_CC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import plotly.graph_objects as go
import streamlit as st

from tools.consultar_regiao import listar_regioes, consultar_regiao  # type: ignore[import]
from integracao import chamar_guardiao                                # type: ignore[import]

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_AVISO_SIMULADO = (
    "⚠️ Mapa ilustrativo: posições fictícias; distâncias do backbone são as da base simulada."
)

_DATA_DIR  = _CC_DIR / "data"
_MAPA_JSON = _DATA_DIR / "mapa_ilustrativo.json"

# Cores das recomendações (consistent com analise.py)
_CORES_RECOMENDACAO: dict[str, str] = {
    "investir_agora":  "#2563eb",   # azul  — investir
    "realizar_piloto": "#16a34a",   # verde — piloto
    "aguardar":        "#d97706",   # amarelo/âmbar — aguardar
}

_LABELS_RECOMENDACAO: dict[str, str] = {
    "investir_agora":  "Investir Agora",
    "realizar_piloto": "Realizar Piloto",
    "aguardar":        "Aguardar",
}


# ---------------------------------------------------------------------------
# Funções puras — testáveis sem Streamlit
# ---------------------------------------------------------------------------

def carregar_angulos(caminho: str | Path = _MAPA_JSON) -> dict[str, float]:
    """
    Lê mapa_ilustrativo.json e retorna {regiao_id: angulo_graus}.

    Args:
        caminho: Caminho para o arquivo JSON.

    Returns:
        Dicionário com os ângulos em graus de cada região.
    """
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)
    return {k: float(v) for k, v in dados["angulos"].items()}


def calcular_coordenadas(distancia_km: float, angulo_graus: float) -> tuple[float, float]:
    """
    Converte (distância, ângulo) em coordenadas cartesianas (x, y).

    O ângulo segue a convenção trigonométrica padrão:
    0° aponta para a direita (leste), cresce no sentido anti-horário.

    Args:
        distancia_km:  Raio em quilômetros.
        angulo_graus:  Ângulo em graus (0–360).

    Returns:
        Tupla (x, y) em quilômetros.
    """
    rad = math.radians(angulo_graus)
    x = distancia_km * math.cos(rad)
    y = distancia_km * math.sin(rad)
    return x, y


# ---------------------------------------------------------------------------
# Cache — carrega recomendações localmente (sem chamar a IBM)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _obter_recomendacoes() -> dict[str, dict]:
    """
    Chama chamar_guardiao em modo local para cada região e devolve
    {regiao_id: resultado_guardiao}.  Cacheado pelo Streamlit.
    """
    ids = [r["id"] for r in listar_regioes()]
    resultados: dict[str, dict] = {}
    for rid in ids:
        try:
            resultado = chamar_guardiao(rid, fonte="local")
            resultados[rid] = resultado
        except Exception:  # noqa: BLE001
            resultados[rid] = {}
    return resultados


@st.cache_data(show_spinner=False)
def _obter_regioes_completas() -> list[dict]:
    """
    Retorna a lista de regiões com dados completos (via consultar_regiao).
    Cacheado pelo Streamlit.
    """
    resumos = listar_regioes()
    completas = []
    for r in resumos:
        dados = consultar_regiao(r["id"])
        if "erro" not in dados:
            completas.append(dados)
    return completas


# ---------------------------------------------------------------------------
# Construção do gráfico Plotly
# ---------------------------------------------------------------------------

def _construir_figura(
    regioes: list[dict],
    angulos: dict[str, float],
    recomendacoes: dict[str, dict],
    regiao_selecionada: str | None,
) -> go.Figure:
    """Monta a figura Plotly do mapa esquemático."""
    fig = go.Figure()

    # ---- Anéis de referência -------------------------------------------------
    for km in (25, 50, 75, 100):
        thetas = [i * math.pi / 180 for i in range(361)]
        xs = [km * math.cos(t) for t in thetas]
        ys = [km * math.sin(t) for t in thetas]
        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode="lines",
            line=dict(color="lightgray", width=1, dash="dot"),
            showlegend=False,
            hoverinfo="skip",
        ))
        # Rótulo do anel
        fig.add_annotation(
            x=0, y=km,
            text=f"{km} km",
            showarrow=False,
            font=dict(color="gray", size=10),
            yanchor="bottom",
        )

    # ---- Backbone central ----------------------------------------------------
    fig.add_trace(go.Scatter(
        x=[0], y=[0],
        mode="markers+text",
        marker=dict(symbol="star", size=20, color="#1e293b"),
        text=["Backbone"],
        textposition="bottom center",
        textfont=dict(size=12, color="#1e293b"),
        name="Backbone",
        hovertemplate="<b>Backbone</b><br>Ponto central de referência<extra></extra>",
    ))

    # ---- Linhas tracejadas: backbone → região --------------------------------
    for r in regioes:
        rid  = r["id"]
        dist = r["engenharia"]["distancia_backbone_km"]
        ang  = angulos.get(rid, 0.0)
        rx, ry = calcular_coordenadas(dist, ang)
        fig.add_trace(go.Scatter(
            x=[0, rx], y=[0, ry],
            mode="lines",
            line=dict(color="#94a3b8", width=1, dash="dash"),
            showlegend=False,
            hoverinfo="skip",
        ))

    # ---- Bolhas das regiões --------------------------------------------------
    max_pop = max(r["mercado"]["populacao_estimada"] for r in regioes)

    for r in regioes:
        rid   = r["id"]
        nome  = r["nome"]
        dist  = r["engenharia"]["distancia_backbone_km"]
        ang   = angulos.get(rid, 0.0)
        rx, ry = calcular_coordenadas(dist, ang)

        pop     = r["mercado"]["populacao_estimada"]
        fibra   = r["engenharia"]["percentual_cobertura_fibra"]
        techs   = ", ".join(r["engenharia"]["tecnologias_viaveis"])

        resultado = recomendacoes.get(rid, {})
        rec       = resultado.get("recomendacao", "aguardar")
        score     = resultado.get("score_consolidado", "—")
        prio      = resultado.get("atencao_prioritaria", False)

        cor       = _CORES_RECOMENDACAO.get(rec, "#94a3b8")
        label_rec = _LABELS_RECOMENDACAO.get(rec, rec)

        # Tamanho da bolha proporcional à população (entre 20 e 60 px)
        bubble_size = 20 + int(40 * pop / max_pop)

        # Destaque visual para região selecionada
        opacity = 1.0 if (regiao_selecionada is None or regiao_selecionada == rid) else 0.4

        # Borda vermelha se atencao_prioritaria
        border_color = "red" if prio else cor
        border_width = 3 if prio else 1.5

        hover = (
            f"<b>{nome}</b><br>"
            f"Distância backbone: <b>{dist} km</b><br>"
            f"Cobertura fibra: <b>{fibra}%</b><br>"
            f"Tecnologias: {techs}<br>"
            f"Score: <b>{score}</b><br>"
            f"Recomendação: <b>{label_rec}</b>"
            + ("<br>🚨 <b>Atenção prioritária</b>" if prio else "")
            + "<extra></extra>"
        )

        fig.add_trace(go.Scatter(
            x=[rx], y=[ry],
            mode="markers+text",
            marker=dict(
                size=bubble_size,
                color=cor,
                opacity=opacity,
                line=dict(color=border_color, width=border_width),
            ),
            text=[nome.replace("Região ", "")],
            textposition="top center",
            textfont=dict(size=11),
            name=nome,
            customdata=[[rid]],
            hovertemplate=hover,
        ))

    # ---- Layout --------------------------------------------------------------
    limite = 120
    fig.update_layout(
        height=620,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(range=[-limite, limite], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[-limite, limite], showgrid=False, zeroline=False,
                   scaleanchor="x", scaleratio=1, visible=False),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(
            title="Regiões",
            orientation="v",
            x=1.01, y=1,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#e2e8f0",
            borderwidth=1,
        ),
        hovermode="closest",
    )
    return fig


# ---------------------------------------------------------------------------
# Cartão de resumo da região
# ---------------------------------------------------------------------------

def _card_regiao(r: dict, resultado: dict):
    """Exibe um card com o resumo da região e link para Análise."""
    rec       = resultado.get("recomendacao", "aguardar")
    score     = resultado.get("score_consolidado", "—")
    prio      = resultado.get("atencao_prioritaria", False)
    label_rec = _LABELS_RECOMENDACAO.get(rec, rec)

    with st.container(border=True):
        st.markdown(f"### {r['nome']}")
        st.caption(r.get("descricao_perfil", ""))

        c1, c2, c3 = st.columns(3)
        c1.metric("Score Guardião", score)
        c2.metric("Recomendação", label_rec)
        c3.metric("Distância backbone", f"{r['engenharia']['distancia_backbone_km']} km")

        if prio:
            st.error("🚨 Atenção prioritária")

        st.markdown(
            f"**Cobertura de fibra:** {r['engenharia']['percentual_cobertura_fibra']}% · "
            f"**Pop. estimada:** {r['mercado']['populacao_estimada']:,}".replace(",", ".")
        )
        st.markdown(
            f"**Tecnologias viáveis:** {', '.join(r['engenharia']['tecnologias_viaveis'])}"
        )

        st.page_link("paginas/analise.py", label="🔍 Abrir na página de Análise", icon="🔍")


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------


def render():
    st.title("🗺️ Mapa ilustrativo")
    st.warning(_AVISO_SIMULADO)
    st.caption("⚠️ Dados simulados — não representam indicadores reais.")

    # Carrega dados
    angulos      = carregar_angulos()
    regioes      = _obter_regioes_completas()
    regioes_dict = {r["id"]: r for r in regioes}

    with st.spinner("Calculando recomendações locais…"):
        recomendacoes = _obter_recomendacoes()

    # Selectbox para região (permite selecionar via widget)
    ids   = [r["id"] for r in regioes]
    nomes = {r["id"]: r["nome"] for r in regioes}

    regiao_sel = st.selectbox(
        "Selecionar região no mapa:",
        options=["(nenhuma)"] + ids,
        format_func=lambda x: "(nenhuma)" if x == "(nenhuma)" else nomes[x],
        key="mapa_regiao_selecionada",
    )
    sel = None if regiao_sel == "(nenhuma)" else regiao_sel

    # Constrói e exibe o gráfico
    fig = _construir_figura(regioes, angulos, recomendacoes, sel)
    st.plotly_chart(fig, use_container_width=True, key="mapa_plotly")

    # Legenda
    with st.expander("ℹ️ Legenda do mapa", expanded=False):
        st.markdown(
            "**Tamanho da bolha** → proporção da população estimada da região  \n"
            "**Cor da bolha**:  \n"
            "- 🔵 Azul → Investir Agora  \n"
            "- 🟢 Verde → Realizar Piloto  \n"
            "- 🟡 Amarelo → Aguardar  \n"
            "**Borda vermelha** → região com atenção prioritária  \n"
            "**Anéis** → distâncias de 25, 50, 75 e 100 km ao backbone  \n"
            "**Linhas tracejadas** → distância real da região ao backbone (base simulada)  \n\n"
            "_Mapa ilustrativo: posições fictícias; distâncias do backbone são as da base simulada._"
        )

    # Cartão da região selecionada
    if sel and sel in regioes_dict:
        st.divider()
        st.subheader(f"📋 Resumo: {nomes[sel]}")
        _card_regiao(regioes_dict[sel], recomendacoes.get(sel, {}))
