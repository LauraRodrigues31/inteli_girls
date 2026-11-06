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
from integracao import chamar_guardiao  # type: ignore[import]
from paginas.mapa_seletor import renderizar_seletor_mapa, _SESSION_KEY  # type: ignore[import]

# ---------------------------------------------------------------------------
# Constantes — mesmo padrão visual da página de Análise
# ---------------------------------------------------------------------------

_AVISO_SIMULADO = (
    "🔬 **Cenário simulado:** recalculado localmente com as mesmas regras dos agentes, "
    "sem consultar a IBM. Dados simulados."
)

_AVISO_IBM = "Simulação local com as mesmas regras dos agentes. Não consulta a IBM."

_LABELS_RECOMENDACAO = {
    "investir_agora":  "✅ Investir Agora",
    "realizar_piloto": "🔬 Realizar Piloto",
    "aguardar":        "⏳ Aguardar",
    None:              "⚠️ Análise Incompleta",
}

_CORES_RECOMENDACAO = {
    "investir_agora":  "green",
    "realizar_piloto": "green",
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
# Cache de recomendações locais para colorir o mapa (item 1)
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def _recomendacoes_mapa_local() -> dict[str, dict]:
    """
    Calcula localmente a recomendação do Guardião para todas as regiões.
    Retorna {regiao_id: {recomendacao, atencao_prioritaria}}.
    Cacheado pelo Streamlit (sem TTL — recalcula apenas quando o módulo recarrega).
    """
    regioes = listar_regioes()
    resultado: dict[str, dict] = {}
    for reg in regioes:
        rid = reg["id"]
        try:
            res = chamar_guardiao(rid, fonte="local")
            resultado[rid] = {
                "recomendacao": res.get("recomendacao"),
                "atencao_prioritaria": bool(res.get("atencao_prioritaria", False)),
            }
        except Exception:  # noqa: BLE001
            resultado[rid] = {}
    return resultado


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


def _resumo_inline(resultado: dict, dist_original: float) -> str:
    """Monta linha resumo: 'Engenharia 11 → 31 · Score 30 → 35 · Recomendação: aguardar'."""
    res_base = resultado.get("base", {})
    res_sim = resultado.get("simulado", {})

    eng_base = res_base.get("pareceres", {}).get("engenharia", {}).get("score", "–")
    eng_sim = res_sim.get("pareceres", {}).get("engenharia", {}).get("score", "–")
    score_base = res_base.get("score_consolidado", "–")
    score_sim = res_sim.get("score_consolidado", "–")
    rec = res_sim.get("recomendacao") or "–"
    rec_label = {
        "investir_agora": "investir agora",
        "realizar_piloto": "realizar piloto",
        "aguardar": "aguardar",
    }.get(rec, rec)

    return (
        f"Engenharia {eng_base} → {eng_sim} · "
        f"Score {score_base} → {score_sim} · "
        f"Recomendação: **{rec_label}**"
    )


def _camada_simulacao(resultado: dict, dist_original: float) -> dict | None:
    """
    Monta o dict de camada de simulação para o mapa.

    Retorna None se não há resultado ou se a distância simulada é a original.
    """
    if not resultado:
        return None

    params = resultado.get("parametros", {})
    dist_sim = params.get("distancia_backbone_km")
    if dist_sim is None:
        return None  # slider não foi usado para distância

    res_sim = resultado.get("simulado", {})
    rec = res_sim.get("recomendacao")

    return {
        "dist_original": dist_original,
        "dist_simulada": dist_sim,
        "recomendacao": rec,
    }


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

    # --- Inicializa session key do mapa ---
    if _SESSION_KEY not in st.session_state:
        st.session_state[_SESSION_KEY] = None

    # --- Seleção da região via mapa ---
    regioes = listar_regioes()
    opcoes_ids = [r["id"] for r in regioes]

    # Carrega dados completos para tooltips do mapa
    try:
        dados_map = {rid: consultar_regiao(rid) for rid in opcoes_ids}
    except Exception:
        dados_map = None

    # Determina camada de simulação para o mapa (resultado da última execução)
    regiao_ativa = st.session_state.get(_SESSION_KEY)
    resultado_para_mapa = st.session_state.get(f"sim_resultado_{regiao_ativa}") if regiao_ativa else None
    dist_original_para_mapa = None
    if regiao_ativa and dados_map:
        dist_original_para_mapa = (
            (dados_map.get(regiao_ativa) or {}).get("engenharia", {}).get("distancia_backbone_km", 0)
        )
    camada_sim = _camada_simulacao(resultado_para_mapa, dist_original_para_mapa or 0)

    # Renderiza mapa com camada opcional de simulação e cores por recomendação
    recomendacoes = _recomendacoes_mapa_local()
    regiao_id_mapa = renderizar_seletor_mapa(
        dados_map,
        chart_key="mapa_simulador",
        camada_simulacao=camada_sim,
        regiao_selecionada_id=regiao_ativa,
        recomendacoes=recomendacoes,
    )

    # Botão de atalho — história do one-pager
    if st.button("▶️ História do one-pager: Esperança com parcerias", key="atalho_onepager"):
        st.session_state[_SESSION_KEY] = "esperanca"
        st.session_state["sim_usar_parcerias"] = True
        st.session_state["sim_atalho_ativado"] = True
        regiao_id_mapa = "esperanca"
        st.rerun()

    # Se não há região ainda, aguarda seleção
    if regiao_id_mapa is None:
        return

    regiao_id = regiao_id_mapa

    # --- Carrega dados originais da região para preencher os defaults dos controles ---
    dados_regiao = consultar_regiao(regiao_id)
    dist_original = dados_regiao.get("engenharia", {}).get("distancia_backbone_km", 50)
    orcamento_original = dados_regiao.get("financeiro", {}).get("orcamento_disponivel_reais", 3_000_000)
    pct_economia = dados_regiao.get("parcerias", {}).get("percentual_economia_potencial_pct", 0)

    # Reseta o default dos controles numéricos quando a região muda
    # Usa um key por região para forçar reinicialização do slider ao trocar de região
    regiao_key = f"sim_defaults_{regiao_id}"
    if regiao_key not in st.session_state:
        st.session_state[regiao_key] = True
        # Reinicializa slider para a distância da nova região
        st.session_state[f"sim_dist_km_{regiao_id}"] = dist_original
        st.session_state[f"sim_teto_reais_{regiao_id}"] = orcamento_original

    # --- Seção: E se a infraestrutura chegasse mais perto? ---
    st.divider()
    st.subheader("🏗️ E se a infraestrutura chegasse mais perto?")

    distancia_km = st.slider(
        f"📡 Nova distância do backbone (km)  *(atual: {dist_original} km)*",
        min_value=0,
        max_value=200,
        key=f"sim_dist_km_{regiao_id}",
        help="Simula a chegada de nova infraestrutura de backbone mais próxima.",
    )

    # --- Seção: demais controles ---
    st.subheader("⚙️ Parâmetros da simulação")

    teto_reais = st.number_input(
        "💵 Teto de investimento (R$)",
        min_value=1,
        step=100_000,
        key=f"sim_teto_reais_{regiao_id}",
        help="Substitui o orçamento disponível para esta simulação.",
    )

    usar_parcerias = st.checkbox(
        f"🤝 Ativar parcerias do Agente Pontes "
        f"(economia de **{pct_economia}%** no CAPEX)",
        key="sim_usar_parcerias",
    )

    # --- Detecta se o usuário moveu o slider após a última simulação ---
    resultado_atual = st.session_state.get(f"sim_resultado_{regiao_id}")
    if resultado_atual:
        dist_executada = resultado_atual.get("parametros", {}).get("distancia_backbone_km")
        if dist_executada is not None and dist_executada != distancia_km:
            st.warning(
                "⚠️ O slider foi alterado após a última simulação. "
                "Clique em **Simular cenário** para atualizar o resultado."
            )

    # --- Executar simulação ---
    st.divider()
    col_run, col_reset = st.columns([2, 1])

    with col_run:
        executar = st.button("▶️ Simular cenário", type="primary", use_container_width=True)
    with col_reset:
        if st.button("🔄 Restaurar cenário base", use_container_width=True):
            # Remove resultado e marcador simulado da região
            if f"sim_resultado_{regiao_id}" in st.session_state:
                del st.session_state[f"sim_resultado_{regiao_id}"]
            # Limpa controles
            for k in [f"sim_dist_km_{regiao_id}", f"sim_teto_reais_{regiao_id}",
                      "sim_usar_parcerias", "sim_atalho_ativado"]:
                if k in st.session_state:
                    del st.session_state[k]
            # Remove defaults para forçar recarga na próxima renderização
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

        # Força rerenderização para o mapa mostrar a nova camada
        st.rerun()

    resultado_atual = st.session_state.get(f"sim_resultado_{regiao_id}")
    if not resultado_atual:
        st.caption("Configure os parâmetros acima e clique em **Simular cenário**.")
        return

    res_base = resultado_atual["base"]
    res_sim = resultado_atual["simulado"]

    # --- Resumo inline junto ao mapa (exibido logo abaixo dos botões) ---
    st.divider()
    st.subheader("📍 Resumo da simulação")

    resumo = _resumo_inline(resultado_atual, dist_original)
    st.markdown(resumo)
    st.caption(f"ℹ️ {_AVISO_IBM}")

    # Alerta prioritário do cenário simulado
    if res_sim.get("atencao_prioritaria"):
        pontos = res_sim.get("pontos_criticos", [])
        msg = "🚨 **Atenção Prioritária no cenário simulado**"
        if pontos:
            msg += "\n" + "\n".join(f"- {p}" for p in pontos)
        st.error(msg)

    # Valores antes e depois para cada agente com alteração
    mudancas = resultado_atual.get("mudancas", [])
    premissas = resultado_atual.get("premissas", [])

    with st.expander("🔍 Detalhes: antes e depois", expanded=bool(mudancas)):
        st.markdown("**Engenharia**")
        eng_base = res_base.get("pareceres", {}).get("engenharia", {}).get("score", "–")
        eng_sim = res_sim.get("pareceres", {}).get("engenharia", {}).get("score", "–")
        st.markdown(f"- Score: {eng_base} → {eng_sim}")

        st.markdown("**Score consolidado**")
        st.markdown(f"- {res_base.get('score_consolidado', '–')} → {res_sim.get('score_consolidado', '–')}")

        st.markdown("**Recomendação**")
        rec_b = _label_rec(res_base.get("recomendacao"))
        rec_s = _label_rec(res_sim.get("recomendacao"))
        st.markdown(f"- {rec_b} → {rec_s}")

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
