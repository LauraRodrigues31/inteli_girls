"""
Página: Análise de Região
Conteúdo principal do Conecta Conselho — seleção de região, indicadores,
execução do Conselho, pareceres dos agentes, recomendação e histórico/ranking.

AVISO: Todos os dados são SIMULADOS e fictícios.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve imports independente do diretório de execução (Linux-safe, sem \)
# ---------------------------------------------------------------------------
_CC_DIR = Path(__file__).resolve().parent.parent
_ROOT   = _CC_DIR.parent

for _p in [str(_ROOT), str(_CC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st

from tools.consultar_regiao import listar_regioes, consultar_regiao  # type: ignore[import]
from integracao import chamar_guardiao, _verificar_credenciais_nuvem  # type: ignore[import]

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_AVISO_SIMULADO = "⚠️ Dados simulados — não representam indicadores reais."

# Rótulos amigáveis e curtos para exibição no cartão
_LABELS_RECOMENDACAO = {
    "investir_agora":  "Investir agora",
    "realizar_piloto": "Começar com piloto",
    "aguardar":        "Aguardar",
}

# Cores CSS/Streamlit por recomendação (itens 1 e 7)
_CORES_RECOMENDACAO = {
    "investir_agora":  "blue",
    "realizar_piloto": "green",
    "aguardar":        "orange",
}

# Cores hex para o gráfico de barras (item 7)
_CORES_HEX = {
    "investir_agora":  "#3b82f6",   # azul
    "realizar_piloto": "#22c55e",   # verde
    "aguardar":        "#f59e0b",   # amarelo
    "analise_incompleta": "#9ca3af", # cinza
}

# Nomes amigáveis com pergunta de cada agente (item 8)
_NOMES_AGENTES = {
    "mercado":        "🏪 Mercado — Tem demanda?",
    "impacto_social": "🫂 Impacto Social — Quem se beneficia?",
    "engenharia":     "⚙️ Engenharia — Dá para construir?",
    "orcamento":      "💰 Orçamento — Cabe no budget?",
    "pontes":         "🤝 Pontes — Há parceiros?",
}

# Rótulos curtos para o gráfico radar (sem emoji nem pergunta)
_NOMES_RADAR = {
    "mercado":        "Mercado",
    "impacto_social": "Impacto Social",
    "engenharia":     "Engenharia",
    "orcamento":      "Orçamento",
    "pontes":         "Pontes",
}

_SECOES_INDICADORES = {
    "Mercado":     "mercado",
    "Social":      "social",
    "Engenharia":  "engenharia",
    "Financeiro":  "financeiro",
    "Parcerias":   "parcerias",
}

# TTL do cache de resultados da nuvem (em segundos)
_CACHE_TTL_SEGUNDOS = 6 * 60 * 60  # 6 horas

# ---------------------------------------------------------------------------
# Cache de resultados da nuvem (st.cache_data com TTL de 6 horas)
# ---------------------------------------------------------------------------


@st.cache_data(ttl=_CACHE_TTL_SEGUNDOS, show_spinner=False)
def _consultar_nuvem_cached(
    regiao_id: str,
    fonte: str,
    _ao_concluir_agente=None,  # prefixo "_" faz st.cache_data ignorar na chave
) -> dict:
    """
    Executa chamar_guardiao no modo nuvem e armazena o resultado em cache.
    Chave de cache = (regiao_id, fonte).  TTL = 6 horas.
    _ao_concluir_agente é ignorado na chave de cache (prefixo "_") mas
    repassado para chamar_guardiao para disparar o st.status em tempo real.
    Devolve sempre uma cópia com os campos:
      - "consultado_em"  = time.time()        (usado na exibição)
      - "_consulta_ns"   = time.perf_counter_ns()  (usado na detecção de cache)
    """
    resultado = dict(
        chamar_guardiao(
            regiao_id,
            fonte=fonte,
            ao_concluir_agente=_ao_concluir_agente,
        )
    )
    resultado["consultado_em"] = time.time()
    resultado["_consulta_ns"] = time.perf_counter_ns()
    return resultado


def _consultar_nuvem(
    regiao_id: str,
    fonte: str,
    *,
    ignorar_cache: bool = False,
    ao_concluir_agente=None,
) -> tuple[dict, bool]:
    """
    Consulta a nuvem passando pelo cache.  Falhas (analise_incompleta) nunca
    ficam guardadas.  Devolve (resultado, veio_do_cache).
    ao_concluir_agente é repassado para _consultar_nuvem_cached e de lá para
    chamar_guardiao, mas não entra na chave de cache.
    """
    if ignorar_cache:
        _consultar_nuvem_cached.clear(regiao_id, fonte)
    inicio_ns = time.perf_counter_ns()
    resultado = _consultar_nuvem_cached(
        regiao_id, fonte, _ao_concluir_agente=ao_concluir_agente
    )
    if resultado.get("status") == "analise_incompleta":
        _consultar_nuvem_cached.clear(regiao_id, fonte)
    return resultado, resultado.get("_consulta_ns", inicio_ns) < inicio_ns


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _barra_score(score: int) -> str:
    """Retorna uma barra de progresso textual para o score 0-100."""
    preenchido = round(score / 10)
    vazio = 10 - preenchido
    return "█" * preenchido + "░" * vazio


def _cor_score(score: int) -> str:
    if score >= 70:
        return "green"
    if score >= 50:
        return "orange"
    return "red"


def _formatar_valor(v) -> str:
    """Formata qualquer valor de indicador de forma legível."""
    if isinstance(v, list):
        return ", ".join(str(i) for i in v) if v else "—"
    if isinstance(v, bool):
        return "Sim" if v else "Não"
    if isinstance(v, float):
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if isinstance(v, int):
        return f"{v:,}".replace(",", ".")
    if v is None:
        return "—"
    return str(v)


def _credenciais_e_ids_disponiveis() -> bool:
    """
    Retorna True se as credenciais WXO e os 5 IDs de agente estiverem
    disponíveis (em os.environ ou .env).  Usado para definir a fonte padrão.
    """
    from cliente_nuvem import carregar_credenciais  # type: ignore[import]
    creds_ok = "erro" not in carregar_credenciais()
    ids_ok, _ = _verificar_credenciais_nuvem()
    return creds_ok and ids_ok


def _inicializar_estado():
    if "historico" not in st.session_state:
        st.session_state.historico = []
    if "fonte_pareceres" not in st.session_state:
        st.session_state.fonte_pareceres = "local"


def _registrar_historico(resultado_guardiao: dict):
    """Adiciona resultado ao histórico, evitando duplicatas de região."""
    historico = st.session_state.historico
    regiao_id = resultado_guardiao["regiao_id"]
    for i, item in enumerate(historico):
        if item["regiao_id"] == regiao_id:
            historico[i] = resultado_guardiao
            return
    historico.append(resultado_guardiao)


def _ranking() -> list[dict]:
    """Retorna ranking excluindo análises incompletas (score null)."""
    return sorted(
        [
            item for item in st.session_state.historico
            if item.get("score_consolidado") is not None
        ],
        key=lambda x: x.get("score_consolidado", 0),
        reverse=True,
    )


# ---------------------------------------------------------------------------
# Seletor de fonte na barra lateral
# ---------------------------------------------------------------------------


def _seletor_fonte() -> str:
    """
    Exibe o seletor de fonte na barra lateral.

    Fonte padrão:
    - "IBM watsonx Orchestrate" se as credenciais e os 5 IDs estiverem disponíveis.
    - "Local" caso contrário, com um aviso discreto.
    """
    with st.sidebar:
        st.header("⚙️ Configurações")

        nuvem_disponivel = _credenciais_e_ids_disponiveis()
        indice_padrao = 1 if nuvem_disponivel else 0  # 0=Local, 1=IBM watsonx

        if not nuvem_disponivel:
            st.caption(
                "ℹ️ Credenciais ou IDs de agente não configurados — "
                "fonte padrão: Local."
            )

        opcao = st.radio(
            "Fonte dos pareceres:",
            options=["Local", "IBM watsonx Orchestrate"],
            index=indice_padrao,
            key="seletor_fonte",
        )
        fonte_escolhida = "nuvem" if opcao == "IBM watsonx Orchestrate" else "local"

        if fonte_escolhida == "nuvem":
            ok, aviso = _verificar_credenciais_nuvem()
            if not ok:
                st.warning(
                    f"⚠️ Credenciais insuficientes para modo nuvem. "
                    f"Usando fonte local.\n\n{aviso}"
                )
                return "local"

        return fonte_escolhida


# ---------------------------------------------------------------------------
# Seções da interface
# ---------------------------------------------------------------------------


def _secao_selecao():
    regioes = listar_regioes()
    opcoes = {r["id"]: f"{r['nome']} — {r['descricao_perfil']}" for r in regioes}
    ids = list(opcoes.keys())

    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        selecionado = st.selectbox(
            "Selecione uma região:",
            options=ids,
            format_func=lambda x: opcoes[x],
            key="regiao_selecionada",
        )
    with col_btn:
        st.write("")
        st.write("")
        executar = st.button("▶ Executar Conselho", type="primary", width="stretch")

    return selecionado, regioes, executar


def _secao_indicadores(regiao_id: str):
    dados = consultar_regiao(regiao_id)
    if "erro" in dados:
        st.error(f"Região não encontrada: {regiao_id}")
        return

    st.divider()
    st.subheader("📊 Dados da Região")
    st.caption(_AVISO_SIMULADO)

    abas = st.tabs(list(_SECOES_INDICADORES.keys()))
    for aba, (label, chave) in zip(abas, _SECOES_INDICADORES.items()):
        with aba:
            secao = dados.get(chave, {})
            if not secao:
                st.info(f"Sem dados de {label} para esta região.")
                continue
            tabela = [
                {"Indicador": k, "Valor": _formatar_valor(v)}
                for k, v in secao.items()
            ]
            st.dataframe(tabela, width="stretch", hide_index=True)


def _card_agente(nome_chave: str, parecer: dict):
    score      = parecer.get("score", 0)
    confianca  = parecer.get("confianca", "—")
    just       = parecer.get("justificativa", "")
    riscos     = parecer.get("riscos") or []
    limitacoes = parecer.get("limitacoes") or []
    erro       = parecer.get("erro")
    label      = _NOMES_AGENTES.get(nome_chave, nome_chave)

    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            st.markdown(f"**{label}**")
            st.markdown(
                f"`{_barra_score(score)}` "
                f":{_cor_score(score)}[**{score}**/100]"
            )
        with c2:
            st.metric("Score", score)
        with c3:
            st.metric("Confiança", confianca)

        if erro:
            st.error(f"Erro: {erro}")
        else:
            with st.expander("📋 Justificativa" + (", Riscos e Limitações" if riscos or limitacoes else "")):
                st.markdown(f"**Justificativa:** {just}")
                if riscos:
                    st.markdown("**Riscos:**")
                    for r in riscos:
                        st.markdown(f"- {r}")
                if limitacoes:
                    st.markdown("**Limitações:**")
                    for lim in limitacoes:
                        st.markdown(f"- {lim}")


# ---------------------------------------------------------------------------
# Gráfico radar — item 3
# ---------------------------------------------------------------------------


def _grafico_radar(pareceres: dict):
    """Renderiza gráfico Scatterpolar Plotly com os 5 scores (0-100)."""
    try:
        import plotly.graph_objects as go  # type: ignore[import]
    except ImportError:
        st.caption("plotly não disponível — gráfico radar omitido.")
        return

    ordem = ["mercado", "impacto_social", "engenharia", "orcamento", "pontes"]
    categorias = [_NOMES_RADAR.get(k, k) for k in ordem]
    valores = [pareceres.get(k, {}).get("score", 0) for k in ordem]
    # Fecha o polígono repetindo o primeiro ponto
    categorias_fechadas = categorias + [categorias[0]]
    valores_fechados = valores + [valores[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=valores_fechados,
        theta=categorias_fechadas,
        fill="toself",
        fillcolor="rgba(59, 130, 246, 0.15)",
        line=dict(color="#3b82f6", width=2),
        name="Scores",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10)),
        ),
        showlegend=False,
        margin=dict(t=20, b=20, l=20, r=20),
        height=320,
    )
    st.plotly_chart(fig, width="stretch")


# ---------------------------------------------------------------------------
# Cartão de resultado (item 1) + alerta (item 2)
# ---------------------------------------------------------------------------


def _cartao_recomendacao(resultado: dict):
    """
    Exibe o cartão visual de resultado:
    - Cor de fundo por recomendação (verde/azul/amarelo/cinza)
    - Score grande
    - Rótulo amigável
    - Alerta de atenção prioritária (item 2)
    """
    score_cons   = resultado.get("score_consolidado", 0)
    recomendacao = resultado.get("recomendacao", "aguardar")
    label_rec    = _LABELS_RECOMENDACAO.get(recomendacao, recomendacao)
    cor_rec      = _CORES_RECOMENDACAO.get(recomendacao, "gray")
    hex_rec      = _CORES_HEX.get(recomendacao, "#9ca3af")

    # Cartão colorido com score grande e recomendação
    st.markdown(
        f"""
        <div style="
            background:{hex_rec}1a;
            border-left: 6px solid {hex_rec};
            border-radius: 8px;
            padding: 20px 24px;
            margin-bottom: 12px;
        ">
            <div style="font-size:48px; font-weight:800; color:{hex_rec}; line-height:1;">
                {score_cons}<span style="font-size:22px; font-weight:400;">/100</span>
            </div>
            <div style="font-size:20px; font-weight:600; color:{hex_rec}; margin-top:4px;">
                {label_rec}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Item 2 — alerta de atenção prioritária
    if resultado.get("atencao_prioritaria"):
        pontos_criticos = resultado.get("pontos_criticos", [])
        linhas = ["⚠️ **Atenção Prioritária** — esta região requer cuidado especial."]
        if pontos_criticos:
            linhas.append("\n**Pontos críticos identificados:**")
            for ponto in pontos_criticos:
                linhas.append(f"- {ponto}")
        st.error("\n".join(linhas))


# ---------------------------------------------------------------------------
# Seção de resultado completa (item 1-6)
# ---------------------------------------------------------------------------


def _secao_resultado(resultado: dict, *, veio_do_cache: bool = False):
    if not resultado:
        return

    status = resultado.get("status", "concluida")
    fonte  = resultado.get("fonte", "local")

    st.divider()
    st.subheader("🤖 Análise dos Agentes Especialistas")
    st.caption(_AVISO_SIMULADO)

    # Indicador de cache — exibido discretamente quando o resultado vem do cache
    if veio_do_cache and fonte == "nuvem":
        st.caption("📦 resultado em cache (IBM watsonx Orchestrate)")

    pareceres = resultado.get("pareceres", {})
    for nome_chave in ["mercado", "impacto_social", "engenharia", "orcamento", "pontes"]:
        parecer = pareceres.get(nome_chave, {})
        _card_agente(nome_chave, parecer)

    st.divider()
    st.subheader("🛡️ Recomendação do Guardião")

    if status == "analise_incompleta":
        # Cartão cinza para análise incompleta
        st.markdown(
            """
            <div style="
                background:#9ca3af1a;
                border-left: 6px solid #9ca3af;
                border-radius: 8px;
                padding: 20px 24px;
                margin-bottom: 12px;
            ">
                <div style="font-size:20px; font-weight:600; color:#6b7280;">
                    Análise incompleta
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.error("⚠️ Análise incompleta — não é possível emitir recomendação.")
        agentes_com_falha = resultado.get("agentes_com_falha", [])
        if agentes_com_falha:
            st.markdown("**Agentes com falha:**")
            for af in agentes_com_falha:
                nome = af.get("agente", "—")
                motivo = af.get("motivo", "erro desconhecido")
                st.markdown(f"- **{_NOMES_AGENTES.get(nome, nome)}**: {motivo}")

        # Botão "Analisar no modo Local" quando a nuvem falhou
        if fonte == "nuvem":
            st.info(
                "💡 A análise na nuvem terminou incompleta. "
                "Você pode analisar esta região no modo Local."
            )
            regiao_id = resultado.get("regiao_id", "")
            if st.button(
                "🖥️ Analisar no modo Local",
                key=f"fallback_local_{regiao_id}",
            ):
                with st.spinner(f"Analisando {regiao_id} no modo local..."):
                    try:
                        resultado_local = chamar_guardiao(regiao_id, fonte="local")
                        st.session_state[f"resultado_{regiao_id}"] = resultado_local
                        st.session_state[f"cache_{regiao_id}"] = False
                        _registrar_historico(resultado_local)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Erro no modo local: {exc}")

        st.divider()
        json_bytes = json.dumps(resultado, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button(
            label="⬇️ Baixar relatório JSON (trilha de auditoria)",
            data=json_bytes,
            file_name=f"relatorio_{resultado.get('regiao_id', 'regiao')}.json",
            mime="application/json",
        )
        return

    # Item 1 — cartão colorido com score e recomendação + item 2 alerta
    _cartao_recomendacao(resultado)

    # Item 3 — gráfico radar
    if pareceres:
        st.markdown("#### 📡 Visão Geral dos Scores")
        _grafico_radar(pareceres)

    just_cons = resultado.get("justificativa_consolidada", "")
    if just_cons:
        st.info(just_cons)

    # Item 4 — Por que aguardar / Caminhos para viabilizar
    recomendacao = resultado.get("recomendacao", "aguardar")
    if recomendacao == "aguardar":
        motivos  = resultado.get("motivos", [])
        caminhos = resultado.get("caminhos", [])
        if motivos:
            with st.expander("🔍 Por que aguardar", expanded=True):
                for m in motivos:
                    st.markdown(f"- {m}")
        if caminhos:
            with st.expander("🛤️ Caminhos para viabilizar", expanded=True):
                for c in caminhos:
                    st.markdown(f"- {c}")

    # Item 5 — Divergências como conflitos entre especialistas
    divergencias = resultado.get("divergencias", [])
    if divergencias:
        with st.expander(f"⚖️ Conflitos entre especialistas ({len(divergencias)})"):
            for d in divergencias:
                st.warning(d)

    riscos_princ = resultado.get("principais_riscos", [])
    if riscos_princ:
        st.markdown("**⚠️ Principais Riscos**")
        for r in riscos_princ:
            st.markdown(f"- {r}")

    limitacoes_g = resultado.get("limitacoes", [])
    if limitacoes_g:
        with st.expander("📌 Limitações da análise"):
            for lim in limitacoes_g:
                st.caption(f"— {lim}")

    tempo = resultado.get("tempo_analise_segundos")
    fonte_label = "☁️ IBM watsonx Orchestrate" if fonte == "nuvem" else "💻 Local"
    if tempo is not None:
        st.caption(f"Fonte: {fonte_label} | Tempo de análise: {tempo}s")
    else:
        st.caption(f"Fonte: {fonte_label}")

    st.divider()
    json_bytes = json.dumps(resultado, ensure_ascii=False, indent=2).encode("utf-8")
    st.download_button(
        label="⬇️ Baixar relatório JSON (trilha de auditoria)",
        data=json_bytes,
        file_name=f"relatorio_{resultado.get('regiao_id', 'regiao')}.json",
        mime="application/json",
    )


# ---------------------------------------------------------------------------
# Histórico com gráfico de barras horizontal (item 7)
# ---------------------------------------------------------------------------


def _grafico_ranking(ranking: list[dict]):
    """Gráfico de barras horizontal com cor por recomendação (item 7)."""
    try:
        import plotly.graph_objects as go  # type: ignore[import]
    except ImportError:
        return

    if not ranking:
        return

    nomes  = [item.get("regiao_nome", item.get("regiao_id", "—")) for item in ranking]
    scores = [item.get("score_consolidado", 0) for item in ranking]
    cores  = [_CORES_HEX.get(item.get("recomendacao", ""), "#9ca3af") for item in ranking]
    labels = [_LABELS_RECOMENDACAO.get(item.get("recomendacao", ""), "—") for item in ranking]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=scores,
        y=nomes,
        orientation="h",
        marker=dict(color=cores),
        text=[f"{s} — {l}" for s, l in zip(scores, labels)],
        textposition="inside",
        insidetextanchor="start",
        hovertemplate="%{y}: %{x}/100<extra></extra>",
    ))
    fig.update_layout(
        xaxis=dict(range=[0, 100], title="Score Consolidado"),
        yaxis=dict(autorange="reversed"),
        margin=dict(t=10, b=30, l=10, r=10),
        height=max(180, 50 * len(ranking)),
        showlegend=False,
    )
    st.plotly_chart(fig, width="stretch")


def _secao_historico():
    historico = st.session_state.historico
    if not historico:
        st.info("Nenhuma região analisada nesta sessão. Execute o Conselho para uma região.")
        return

    ranking = _ranking()

    st.subheader("🏆 Ranking desta Sessão")
    st.caption(_AVISO_SIMULADO)
    st.caption("Regiões com análise incompleta não entram no ranking.")

    if ranking:
        # Item 7 — gráfico de barras horizontal com cor por recomendação
        _grafico_ranking(ranking)

        dados_tabela = []
        for pos, item in enumerate(ranking, start=1):
            rec = item.get("recomendacao", "—")
            dados_tabela.append({
                "Rank": pos,
                "Região": item.get("regiao_nome", item.get("regiao_id", "—")),
                "Score": item.get("score_consolidado", 0),
                "Recomendação": _LABELS_RECOMENDACAO.get(rec, rec),
            })
        st.dataframe(dados_tabela, width="stretch", hide_index=True)
    else:
        st.info("Nenhuma análise concluída com recomendação disponível no ranking.")

    st.subheader("📋 Histórico Detalhado")
    for item in historico:
        regiao_nome = item.get("regiao_nome", item.get("regiao_id", "—"))
        score = item.get("score_consolidado")
        rec   = item.get("recomendacao")
        status = item.get("status", "concluida")

        if status == "analise_incompleta":
            expander_label = f"{regiao_nome} — ⚠️ Análise Incompleta"
        else:
            score_str = f"Score {score}" if score is not None else "—"
            label = _LABELS_RECOMENDACAO.get(rec, rec) if rec else "—"
            expander_label = f"{regiao_nome} — {score_str} — {label}"

        with st.expander(expander_label):
            json_bytes = json.dumps(item, ensure_ascii=False, indent=2).encode("utf-8")
            st.download_button(
                label=f"⬇️ Baixar relatório {regiao_nome}",
                data=json_bytes,
                file_name=f"relatorio_{item.get('regiao_id', 'regiao')}.json",
                mime="application/json",
                key=f"dl_{item.get('regiao_id', 'x')}",
            )
            st.json(item)


# ---------------------------------------------------------------------------
# Comparar regiões — helpers e seção principal
# ---------------------------------------------------------------------------

_ORDEM_RADAR = ["mercado", "impacto_social", "engenharia", "orcamento", "pontes"]

# Cores distintas para as duas séries do radar duplo
_COR_SERIE_A = "#3b82f6"   # azul
_COR_SERIE_B = "#f59e0b"   # amarelo-âmbar


def _analisar_para_comparar(regiao_id: str, fonte: str) -> dict:
    """
    Executa chamar_guardiao para a região no modo correto (local ou nuvem com cache).
    Usado pela seção de comparação — sem spinner, sem registro no histórico.
    Retorna o dict de resultado ou {"erro": ...} em caso de falha.
    """
    try:
        if fonte == "nuvem":
            resultado, _ = _consultar_nuvem(regiao_id, fonte)
        else:
            resultado = chamar_guardiao(regiao_id, fonte=fonte)
        return resultado
    except Exception as exc:  # noqa: BLE001
        return {"erro": str(exc), "regiao_id": regiao_id}


def _mini_card_comparar(resultado: dict):
    """
    Exibe um mini-cartão colorido para a seção de comparação:
    - Score grande + recomendação amigável
    - Alerta ⚠️ com pontos_criticos quando atencao_prioritaria
    - Tabela de scores por agente
    """
    if resultado.get("erro"):
        st.error(f"Erro ao analisar região: {resultado['erro']}")
        return
    if resultado.get("status") == "analise_incompleta":
        st.warning("⚠️ Análise incompleta — resultado parcial.")

    score_cons   = resultado.get("score_consolidado") or 0
    recomendacao = resultado.get("recomendacao", "aguardar")
    label_rec    = _LABELS_RECOMENDACAO.get(recomendacao, recomendacao)
    hex_rec      = _CORES_HEX.get(recomendacao, "#9ca3af")

    st.markdown(
        f"""
        <div style="
            background:{hex_rec}1a;
            border-left:5px solid {hex_rec};
            border-radius:8px;
            padding:14px 18px;
            margin-bottom:10px;
        ">
            <div style="font-size:40px;font-weight:800;color:{hex_rec};line-height:1;">
                {score_cons}<span style="font-size:18px;font-weight:400;">/100</span>
            </div>
            <div style="font-size:16px;font-weight:600;color:{hex_rec};margin-top:4px;">
                {label_rec}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if resultado.get("atencao_prioritaria"):
        pontos = resultado.get("pontos_criticos", [])
        linhas = ["⚠️ **Atenção Prioritária**"]
        for p in pontos:
            linhas.append(f"- {p}")
        st.error("\n".join(linhas))

    # Tabela compacta de scores por agente
    pareceres = resultado.get("pareceres", {})
    if pareceres:
        rows = []
        for chave in _ORDEM_RADAR:
            score_ag = pareceres.get(chave, {}).get("score", "—")
            nome_ag  = _NOMES_RADAR.get(chave, chave)
            rows.append({"Agente": nome_ag, "Score": score_ag})
        st.dataframe(rows, hide_index=True, width="stretch")


def _radar_duplo(
    pareceres_a: dict,
    pareceres_b: dict,
    nome_a: str,
    nome_b: str,
):
    """
    Gráfico Scatterpolar com duas séries sobrepostas (região A e região B).
    """
    try:
        import plotly.graph_objects as go  # type: ignore[import]
    except ImportError:
        st.caption("plotly não disponível — gráfico radar omitido.")
        return

    categorias = [_NOMES_RADAR.get(k, k) for k in _ORDEM_RADAR]
    cat_fechadas = categorias + [categorias[0]]

    def _valores(pareceres: dict) -> list[int]:
        vals = [pareceres.get(k, {}).get("score", 0) for k in _ORDEM_RADAR]
        return vals + [vals[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=_valores(pareceres_a),
        theta=cat_fechadas,
        fill="toself",
        fillcolor=f"{_COR_SERIE_A}26",
        line=dict(color=_COR_SERIE_A, width=2),
        name=nome_a,
    ))
    fig.add_trace(go.Scatterpolar(
        r=_valores(pareceres_b),
        theta=cat_fechadas,
        fill="toself",
        fillcolor=f"{_COR_SERIE_B}26",
        line=dict(color=_COR_SERIE_B, width=2),
        name=nome_b,
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10))),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        margin=dict(t=20, b=60, l=20, r=20),
        height=360,
    )
    st.plotly_chart(fig, width="stretch")


def _secao_comparar(fonte: str):
    """
    Seção "Comparar regiões": dois selectboxes + botão "Comparar".
    Mostra lado a lado: mini-card (score, recomendação, alerta, scores por agente)
    e um radar duplo sobreposto.
    Fonte padrão: "local" (rápido, sem gastar IBM); aceita "nuvem" com cache.
    """
    regioes   = listar_regioes()
    ids       = [r["id"] for r in regioes]
    opcoes    = {r["id"]: r["nome"] for r in regioes}

    # Garante seleção padrão diferente entre A e B
    idx_b_padrao = 1 if len(ids) > 1 else 0

    col_a, col_b, col_btn = st.columns([2, 2, 1])
    with col_a:
        id_a = st.selectbox(
            "Região A:",
            options=ids,
            format_func=lambda x: opcoes[x],
            index=0,
            key="comparar_regiao_a",
        )
    with col_b:
        id_b = st.selectbox(
            "Região B:",
            options=ids,
            format_func=lambda x: opcoes[x],
            index=idx_b_padrao,
            key="comparar_regiao_b",
        )
    with col_btn:
        st.write("")
        st.write("")
        comparar = st.button("⚖️ Comparar", type="primary", width="stretch", key="btn_comparar")

    if id_a == id_b:
        st.info("ℹ️ Selecione duas regiões diferentes para comparar.")

    if comparar:
        fonte_comp = "local"  # comparação usa Local por padrão — rápido
        with st.spinner("Analisando as duas regiões..."):
            res_a = _analisar_para_comparar(id_a, fonte_comp)
            res_b = _analisar_para_comparar(id_b, fonte_comp)
        st.session_state["comparar_res_a"] = res_a
        st.session_state["comparar_res_b"] = res_b
        st.session_state["comparar_id_a"]  = id_a
        st.session_state["comparar_id_b"]  = id_b

    res_a = st.session_state.get("comparar_res_a")
    res_b = st.session_state.get("comparar_res_b")
    id_a_exib = st.session_state.get("comparar_id_a", id_a)
    id_b_exib = st.session_state.get("comparar_id_b", id_b)

    if not res_a or not res_b:
        return

    nome_a = res_a.get("regiao_nome") or opcoes.get(id_a_exib, id_a_exib)
    nome_b = res_b.get("regiao_nome") or opcoes.get(id_b_exib, id_b_exib)

    st.divider()

    # Lado a lado
    col_esq, col_dir = st.columns(2)
    with col_esq:
        st.markdown(f"### {nome_a}")
        _mini_card_comparar(res_a)
    with col_dir:
        st.markdown(f"### {nome_b}")
        _mini_card_comparar(res_b)

    # Radar duplo sobreposto
    st.markdown("#### 📡 Radar Comparativo")
    pareceres_a = res_a.get("pareceres", {})
    pareceres_b = res_b.get("pareceres", {})
    if pareceres_a or pareceres_b:
        _radar_duplo(pareceres_a, pareceres_b, nome_a, nome_b)


# ---------------------------------------------------------------------------
# Ponto de entrada da página
# ---------------------------------------------------------------------------


def render():
    _inicializar_estado()

    fonte = _seletor_fonte()

    st.title("🔍 Análise de Região")
    st.caption("Sistema de apoio a decisões de expansão de conectividade | Trilha 3 · IBM SkillsBuild")
    st.warning(_AVISO_SIMULADO)

    aba_analise, aba_comparar, aba_historico = st.tabs([
        "🔍 Análise de Região",
        "⚖️ Comparar Regiões",
        "📚 Histórico e Ranking",
    ])

    with aba_analise:
        regiao_id, regioes, executar = _secao_selecao()
        _secao_indicadores(regiao_id)

        if executar:
            if fonte == "nuvem":
                # Item 6 — st.status mostrando cada agente ao terminar
                agentes_status: dict[str, tuple[bool, float]] = {}
                status_container = st.status("Executando Conselho na nuvem...", expanded=True)

                def _ao_concluir_agente(nome: str, sucesso: bool, tempo: float):
                    icone = "✅" if sucesso else "❌"
                    status_container.write(f"{icone} {nome} — {tempo:.1f} s")
                    agentes_status[nome] = (sucesso, tempo)

                try:
                    resultado, veio_do_cache = _consultar_nuvem(
                        regiao_id, fonte, ao_concluir_agente=_ao_concluir_agente
                    )
                    # Se veio do cache o callback não dispara — mostra mensagem adequada
                    if veio_do_cache:
                        status_container.write("📦 Resultado carregado do cache.")
                    status_container.update(label="Conselho concluído!", state="complete")
                    st.session_state[f"resultado_{regiao_id}"] = resultado
                    st.session_state[f"cache_{regiao_id}"] = veio_do_cache
                    _registrar_historico(resultado)
                    if resultado.get("status") == "analise_incompleta":
                        st.warning("Análise incompleta — verifique os agentes com falha.")
                    elif resultado.get("erro"):
                        st.error(f"Erro ao analisar região: {resultado['erro']}")
                    else:
                        st.success(f"Análise concluída para {resultado.get('regiao_nome', regiao_id)}!")
                except Exception as e:
                    status_container.update(label="Erro no Conselho", state="error")
                    st.error(f"Erro inesperado: {e}")
            else:
                with st.spinner(f"Executando o Conselho para {regiao_id}..."):
                    try:
                        resultado = chamar_guardiao(regiao_id, fonte=fonte)
                        veio_do_cache = False
                        st.session_state[f"resultado_{regiao_id}"] = resultado
                        st.session_state[f"cache_{regiao_id}"] = veio_do_cache
                        _registrar_historico(resultado)
                        if resultado.get("status") == "analise_incompleta":
                            st.warning("Análise incompleta — verifique os agentes com falha.")
                        elif resultado.get("erro"):
                            st.error(f"Erro ao analisar região: {resultado['erro']}")
                        else:
                            st.success(f"Análise concluída para {resultado.get('regiao_nome', regiao_id)}!")
                    except Exception as e:
                        st.error(f"Erro inesperado: {e}")

        resultado_atual = st.session_state.get(f"resultado_{regiao_id}")

        # Botão "Consultar a IBM novamente" — limpa cache só desta região e re-executa
        if resultado_atual and resultado_atual.get("fonte") == "nuvem":
            col_cache, _ = st.columns([2, 3])
            with col_cache:
                if st.button(
                    "🔄 Consultar a IBM novamente",
                    key=f"refetch_{regiao_id}",
                    help="Ignora o cache e busca uma nova análise na nuvem.",
                ):
                    with st.spinner(f"Consultando a IBM para {regiao_id}..."):
                        try:
                            resultado_atual, veio_do_cache = _consultar_nuvem(
                                regiao_id, "nuvem", ignorar_cache=True
                            )
                            st.session_state[f"resultado_{regiao_id}"] = resultado_atual
                            st.session_state[f"cache_{regiao_id}"] = veio_do_cache
                            _registrar_historico(resultado_atual)
                            st.success("Nova consulta concluída!")
                        except Exception as e:
                            st.error(f"Erro ao reconsultar: {e}")

        if resultado_atual:
            _secao_resultado(
                resultado_atual,
                veio_do_cache=st.session_state.get(f"cache_{regiao_id}", False),
            )

    with aba_comparar:
        st.caption(_AVISO_SIMULADO)
        _secao_comparar(fonte)

    with aba_historico:
        st.caption(_AVISO_SIMULADO)
        _secao_historico()
