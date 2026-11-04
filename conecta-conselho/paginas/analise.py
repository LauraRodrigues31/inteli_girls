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

_LABELS_RECOMENDACAO = {
    "investir_agora":  "✅ Investir Agora",
    "realizar_piloto": "🔬 Realizar Piloto",
    "aguardar":        "⏳ Aguardar",
}

_CORES_RECOMENDACAO = {
    "investir_agora":  "green",
    "realizar_piloto": "blue",
    "aguardar":        "orange",
}

_NOMES_AGENTES = {
    "mercado":        "🏪 Mercado",
    "impacto_social": "🫂 Impacto Social",
    "engenharia":     "⚙️ Engenharia",
    "orcamento":      "💰 Orçamento",
    "pontes":         "🤝 Pontes",
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
def _consultar_nuvem_cached(regiao_id: str, fonte: str) -> dict:
    """
    Executa chamar_guardiao no modo nuvem e armazena o resultado em cache.
    Chave de cache = (regiao_id, fonte).  TTL = 6 horas.
    Devolve sempre uma cópia com o campo "consultado_em" = time.time().
    """
    resultado = dict(chamar_guardiao(regiao_id, fonte=fonte))
    resultado["consultado_em"] = time.time()
    return resultado


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
        executar = st.button("▶ Executar Conselho", type="primary", use_container_width=True)

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
            st.dataframe(tabela, use_container_width=True, hide_index=True)


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

    score_cons = resultado.get("score_consolidado", 0)
    recomendacao = resultado.get("recomendacao", "aguardar")
    label_rec = _LABELS_RECOMENDACAO.get(recomendacao, recomendacao)
    cor_rec = _CORES_RECOMENDACAO.get(recomendacao, "gray")

    col_sc, col_rec = st.columns([1, 2])
    with col_sc:
        st.metric("Score Consolidado", f"{score_cons} / 100")
    with col_rec:
        st.markdown(f"### :{cor_rec}[{label_rec}]")

    if resultado.get("atencao_prioritaria"):
        pontos_criticos = resultado.get("pontos_criticos", [])
        aviso_linhas = ["🚨 **Atenção Prioritária** — esta região requer cuidado especial."]
        if pontos_criticos:
            aviso_linhas.append("\n**Pontos críticos identificados:**")
            for ponto in pontos_criticos:
                aviso_linhas.append(f"- {ponto}")
        st.error("\n".join(aviso_linhas))

    just_cons = resultado.get("justificativa_consolidada", "")
    if just_cons:
        st.info(just_cons)

    if recomendacao == "aguardar":
        motivos = resultado.get("motivos", [])
        caminhos = resultado.get("caminhos", [])
        if motivos:
            with st.expander("🔍 Por que aguardar", expanded=True):
                for m in motivos:
                    st.markdown(f"- {m}")
        if caminhos:
            with st.expander("🛤️ Caminhos para viabilizar", expanded=True):
                for c in caminhos:
                    st.markdown(f"- {c}")

    divergencias = resultado.get("divergencias", [])
    if divergencias:
        with st.expander(f"⚡ Divergências identificadas ({len(divergencias)})"):
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
        dados_tabela = []
        for pos, item in enumerate(ranking, start=1):
            rec = item.get("recomendacao", "—")
            dados_tabela.append({
                "Rank": pos,
                "Região": item.get("regiao_nome", item.get("regiao_id", "—")),
                "Score": item.get("score_consolidado", 0),
                "Recomendação": _LABELS_RECOMENDACAO.get(rec, rec),
            })
        st.dataframe(dados_tabela, use_container_width=True, hide_index=True)
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
# Ponto de entrada da página
# ---------------------------------------------------------------------------


def render():
    _inicializar_estado()

    fonte = _seletor_fonte()

    st.title("🔍 Análise de Região")
    st.caption("Sistema de apoio a decisões de expansão de conectividade | Trilha 3 · IBM SkillsBuild")
    st.warning(_AVISO_SIMULADO)

    aba_analise, aba_historico = st.tabs(["🔍 Análise de Região", "📚 Histórico e Ranking"])

    with aba_analise:
        regiao_id, regioes, executar = _secao_selecao()
        _secao_indicadores(regiao_id)

        veio_do_cache = False

        if executar:
            with st.spinner(f"Executando o Conselho para {regiao_id}..."):
                try:
                    if fonte == "nuvem":
                        resultado = _consultar_nuvem_cached(regiao_id, fonte)
                        veio_do_cache = (time.time() - resultado.get("consultado_em", 0)) > 2
                        if resultado.get("status") == "analise_incompleta":
                            _consultar_nuvem_cached.clear(regiao_id, fonte)
                    else:
                        resultado = chamar_guardiao(regiao_id, fonte=fonte)
                    st.session_state[f"resultado_{regiao_id}"] = resultado
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
        if resultado_atual and fonte == "nuvem":
            col_cache, _ = st.columns([2, 3])
            with col_cache:
                if st.button(
                    "🔄 Consultar a IBM novamente",
                    key=f"refetch_{regiao_id}",
                    help="Ignora o cache e busca uma nova análise na nuvem.",
                ):
                    _consultar_nuvem_cached.clear(regiao_id, fonte)
                    with st.spinner(f"Consultando a IBM para {regiao_id}..."):
                        try:
                            resultado_atual = _consultar_nuvem_cached(regiao_id, fonte)
                            st.session_state[f"resultado_{regiao_id}"] = resultado_atual
                            _registrar_historico(resultado_atual)
                            veio_do_cache = False
                            st.success("Nova consulta concluída!")
                        except Exception as e:
                            st.error(f"Erro ao reconsultar: {e}")

            # Detecta cache: resultado foi obtido há mais de 2s
            if not executar and resultado_atual:
                consultado_em = resultado_atual.get("consultado_em", 0)
                veio_do_cache = (time.time() - consultado_em) > 2

        if resultado_atual:
            _secao_resultado(resultado_atual, veio_do_cache=veio_do_cache)

    with aba_historico:
        st.caption(_AVISO_SIMULADO)
        _secao_historico()
