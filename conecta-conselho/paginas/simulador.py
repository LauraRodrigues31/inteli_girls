"""
Página: Simulador de cenários
Permite simular cenários hipotéticos de expansão de conectividade e visualizar
como parcerias, teto de investimento e distância do backbone mudam a recomendação.

AVISO: Todos os dados são SIMULADOS. Recalculado localmente com as mesmas regras
dos agentes, sem consultar a IBM.
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve imports independente do diretório de execução
# ---------------------------------------------------------------------------
_CC_DIR = Path(__file__).resolve().parent.parent
_ROOT = _CC_DIR.parent

for _p in [str(_ROOT), str(_CC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
from tools.consultar_regiao import listar_regioes, consultar_regiao  # type: ignore[import]
from simulador import simular_cenario  # type: ignore[import]

# ---------------------------------------------------------------------------
# Constantes — mesmo padrão visual da página de Análise
# ---------------------------------------------------------------------------

_AVISO_SIMULADO = (
    "🔬 **Cenário simulado:** recalculado localmente com as mesmas regras dos agentes, "
    "sem consultar a IBM. Dados simulados."
)

_LABELS_RECOMENDACAO = {
    "investir_agora":  "✅ Investir Agora",
    "realizar_piloto": "🔬 Realizar Piloto",
    "aguardar":        "⏳ Aguardar",
    None:              "⚠️ Análise Incompleta",
}

_CORES_RECOMENDACAO = {
    "investir_agora":  "green",
    "realizar_piloto": "blue",
    "aguardar":        "orange",
    None:              "gray",
}

_NOMES_AGENTES = {
    "mercado":        "🏪 Mercado",
    "impacto_social": "🫂 Impacto Social",
    "engenharia":     "⚙️ Engenharia",
    "orcamento":      "💰 Orçamento",
    "pontes":         "🤝 Pontes",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _label_rec(recomendacao: str | None) -> str:
    return _LABELS_RECOMENDACAO.get(recomendacao, str(recomendacao))


def _cor_rec(recomendacao: str | None) -> str:
    return _CORES_RECOMENDACAO.get(recomendacao, "gray")


def _card_resultado(resultado: dict, titulo: str):
    """Exibe um card compacto de resultado do Guardião."""
    rec = resultado.get("recomendacao")
    score = resultado.get("score_consolidado")
    alerta = resultado.get("atencao_prioritaria", False)
    status = resultado.get("status", "concluida")
    cor = _cor_rec(rec)

    with st.container(border=True):
        st.markdown(f"**{titulo}**")

        if status == "analise_incompleta" or score is None:
            st.markdown(":gray[⚠️ Análise Incompleta]")
        else:
            st.markdown(f"### :{cor}[{_label_rec(rec)}]")
            st.metric("Score consolidado", f"{score} / 100")

        if alerta:
            pontos = resultado.get("pontos_criticos", [])
            msg = "🚨 **Atenção Prioritária**"
            if pontos:
                msg += "\n" + "\n".join(f"- {p}" for p in pontos)
            st.error(msg)


def _grafico_barras_agentes(resultado_base: dict, resultado_simulado: dict):
    """Gráfico de barras agrupadas comparando os 5 scores (base × simulado)."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        st.info("Instale plotly para ver o gráfico: pip install plotly")
        return

    agentes_ordem = ["mercado", "impacto_social", "engenharia", "orcamento", "pontes"]
    labels = [_NOMES_AGENTES.get(a, a) for a in agentes_ordem]

    pareceres_base = resultado_base.get("pareceres", {})
    pareceres_sim = resultado_simulado.get("pareceres", {})

    scores_base = [pareceres_base.get(a, {}).get("score", 0) for a in agentes_ordem]
    scores_sim = [pareceres_sim.get(a, {}).get("score", 0) for a in agentes_ordem]

    fig = go.Figure(data=[
        go.Bar(
            name="Cenário Base",
            x=labels,
            y=scores_base,
            marker_color="#6b7280",
            opacity=0.75,
        ),
        go.Bar(
            name="Cenário Simulado",
            x=labels,
            y=scores_sim,
            marker_color="#3b82f6",
            opacity=0.9,
        ),
    ])

    fig.update_layout(
        barmode="group",
        title="Comparação dos scores por agente",
        yaxis=dict(range=[0, 100], title="Score (0–100)"),
        xaxis_title="Agente",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=320,
        margin=dict(t=60, b=40, l=40, r=20),
    )

    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Ponto de entrada da página
# ---------------------------------------------------------------------------


def render():
    st.title("🧪 Simulador de cenários")
    st.markdown(
        "**E se...?** Teste como parcerias, investimento e infraestrutura "
        "mudam a recomendação para uma região."
    )
    st.info(_AVISO_SIMULADO)

    # --- Seleção da região ---
    regioes = listar_regioes()
    opcoes_ids = [r["id"] for r in regioes]
    opcoes_labels = {r["id"]: r["nome"] for r in regioes}

    # Botão de atalho — história do one-pager
    if st.button("▶️ História do one-pager: Esperança com parcerias", key="atalho_onepager"):
        st.session_state["sim_regiao"] = "esperanca"
        st.session_state["sim_usar_parcerias"] = True
        st.session_state["sim_atalho_ativado"] = True

    regiao_id = st.selectbox(
        "Região:",
        options=opcoes_ids,
        format_func=lambda x: opcoes_labels.get(x, x),
        key="sim_regiao",
    )

    # --- Carrega dados originais da região para preencher os defaults dos controles ---
    dados_regiao = consultar_regiao(regiao_id)
    dist_original = dados_regiao.get("engenharia", {}).get("distancia_backbone_km", 50)
    capex_original = dados_regiao.get("financeiro", {}).get("capex_reais", 5_000_000)
    orcamento_original = dados_regiao.get("financeiro", {}).get("orcamento_disponivel_reais", 3_000_000)
    pct_economia = dados_regiao.get("parcerias", {}).get("percentual_economia_potencial_pct", 0)

    # Reseta o default dos controles numéricos quando a região muda
    regiao_key = f"sim_defaults_{regiao_id}"
    if regiao_key not in st.session_state:
        st.session_state[regiao_key] = True
        st.session_state["sim_dist_km"] = dist_original
        st.session_state["sim_teto_reais"] = orcamento_original

    # --- Controles ---
    st.divider()
    st.subheader("⚙️ Parâmetros da simulação")

    col_a, col_b = st.columns(2)

    with col_a:
        distancia_km = st.slider(
            f"📡 Distância do backbone (km)  *(atual: {dist_original} km)*",
            min_value=0,
            max_value=200,
            key="sim_dist_km",
            help="Simula a chegada de nova infraestrutura de backbone mais próxima.",
        )

    with col_b:
        teto_reais = st.number_input(
            "💵 Teto de investimento (R$)",
            min_value=1,
            step=100_000,
            key="sim_teto_reais",
            help="Substitui o orçamento disponível para esta simulação.",
        )

    usar_parcerias = st.checkbox(
        f"🤝 Ativar parcerias do Agente Pontes "
        f"(economia de **{pct_economia}%** no CAPEX)",
        key="sim_usar_parcerias",
    )

    # --- Executar simulação ---
    st.divider()
    col_run, col_reset = st.columns([2, 1])

    with col_run:
        executar = st.button("▶️ Simular cenário", type="primary", use_container_width=True)
    with col_reset:
        if st.button("🔄 Restaurar cenário base", use_container_width=True):
            for k in ["sim_dist_km", "sim_teto_reais", "sim_usar_parcerias", "sim_atalho_ativado"]:
                if k in st.session_state:
                    del st.session_state[k]
            # Remove defaults para forçar recarga
            if regiao_key in st.session_state:
                del st.session_state[regiao_key]
            st.rerun()

    if executar or st.session_state.get("sim_atalho_ativado"):
        # Limpa flag de atalho após uso
        st.session_state.pop("sim_atalho_ativado", None)

        with st.spinner("Calculando cenários..."):
            resultado = simular_cenario(
                regiao_id=regiao_id,
                distancia_backbone_km=distancia_km,
                teto_investimento_reais=float(teto_reais),
                usar_parcerias=usar_parcerias,
            )

        if "erro" in resultado:
            st.error(f"Erro na simulação: {resultado['erro']}")
            return

        # Salva resultado na sessão para manter na tela
        st.session_state[f"sim_resultado_{regiao_id}"] = resultado

    resultado_atual = st.session_state.get(f"sim_resultado_{regiao_id}")
    if not resultado_atual:
        st.caption("Configure os parâmetros acima e clique em **Simular cenário**.")
        return

    res_base = resultado_atual["base"]
    res_sim = resultado_atual["simulado"]

    # --- Resultado lado a lado ---
    st.divider()
    st.subheader("📊 Resultado da simulação")

    col_base, col_sim = st.columns(2)
    with col_base:
        _card_resultado(res_base, "📋 Cenário Base")
    with col_sim:
        _card_resultado(res_sim, "🔬 Cenário Simulado")

    # --- Gráfico comparativo ---
    _grafico_barras_agentes(res_base, res_sim)

    # --- O que mudou e Premissas ---
    mudancas = resultado_atual.get("mudancas", [])
    premissas = resultado_atual.get("premissas", [])

    with st.expander("🔍 O que mudou e Premissas", expanded=bool(mudancas)):
        if mudancas:
            st.markdown("**O que mudou:**")
            for m in mudancas:
                st.markdown(f"- {m}")
        else:
            st.markdown("*Nenhuma mudança — os parâmetros simulados são idênticos à base.*")

        if premissas:
            st.markdown("**Premissas aplicadas:**")
            for p in premissas:
                st.markdown(f"- {p}")
