"""
Conecta Conselho — Interface Streamlit (MVP)

Jornada obrigatória (Seção 5.3 CONTEXTO_PROJETO.md):
  1. Seleção de região (6 regiões simuladas)
  2. Visualização de indicadores por perspectiva
  3. Execução do Conselho
  4. Pareceres dos 5 agentes especialistas
  5. Recomendação do Guardião com divergências
  6. Histórico e ranking em st.session_state
  7. Download de relatório JSON (trilha de auditoria)

AVISO: Todos os dados são SIMULADOS e fictícios.
Nenhuma API externa é chamada; nenhum mapa é exibido.
"""

from __future__ import annotations

import json
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

from tools.consultar_regiao import listar_regioes, consultar_regiao  # type: ignore[import]
from integracao import chamar_guardiao

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_AVISO_SIMULADO = "⚠️ Dados simulados — não representam indicadores reais."

_LABELS_RECOMENDACAO = {
    "investir_agora":  "✅ Investir Agora",
    "realizar_piloto": "🔬 Realizar Piloto",
    "aguardar":        "⏳ Aguardar",
    "escalar":         "👤 Escalar a Humano",
}

_CORES_RECOMENDACAO = {
    "investir_agora":  "green",
    "realizar_piloto": "blue",
    "aguardar":        "orange",
    "escalar":         "red",
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


def _inicializar_estado():
    if "historico" not in st.session_state:
        st.session_state.historico = []   # lista de dicts do Guardião


def _registrar_historico(resultado_guardiao: dict):
    """Adiciona resultado ao histórico, evitando duplicatas de região."""
    historico = st.session_state.historico
    regiao_id = resultado_guardiao["regiao_id"]
    # Atualiza se já existir
    for i, item in enumerate(historico):
        if item["regiao_id"] == regiao_id:
            historico[i] = resultado_guardiao
            return
    historico.append(resultado_guardiao)


def _ranking() -> list[dict]:
    return sorted(
        st.session_state.historico,
        key=lambda x: x.get("score_consolidado", 0),
        reverse=True,
    )


# ---------------------------------------------------------------------------
# Seções da interface
# ---------------------------------------------------------------------------


def _secao_selecao() -> tuple[str, list[dict]]:
    """Renderiza a seleção de região e retorna (regiao_id_selecionada, lista_regioes)."""
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
        st.write("")  # alinha verticalmente
        st.write("")
        executar = st.button("▶ Executar Conselho", type="primary", use_container_width=True)

    return selecionado, regioes, executar


def _secao_indicadores(regiao_id: str):
    """Exibe os indicadores da região em abas por perspectiva."""
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
    """Exibe o card de um agente especialista."""
    score     = parecer.get("score", 0)
    confianca = parecer.get("confianca", "—")
    just      = parecer.get("justificativa", "")
    riscos    = parecer.get("riscos", [])
    limitacoes = parecer.get("limitacoes", [])
    erro      = parecer.get("erro")
    label     = _NOMES_AGENTES.get(nome_chave, nome_chave)

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
            with st.expander("📋 Justificativa, Riscos e Limitações"):
                st.markdown(f"**Justificativa:** {just}")
                if riscos:
                    st.markdown("**Riscos:**")
                    for r in riscos:
                        st.markdown(f"- {r}")
                if limitacoes:
                    st.markdown("**Limitações:**")
                    for lim in limitacoes:
                        st.markdown(f"- {lim}")


def _secao_resultado(resultado: dict):
    """Exibe o resultado completo do Guardião."""
    if not resultado:
        return

    st.divider()
    st.subheader("🤖 Análise dos Agentes Especialistas")
    st.caption(_AVISO_SIMULADO)

    pareceres = resultado.get("pareceres", {})
    for nome_chave in ["mercado", "impacto_social", "engenharia", "orcamento", "pontes"]:
        parecer = pareceres.get(nome_chave, {})
        _card_agente(nome_chave, parecer)

    st.divider()
    st.subheader("🛡️ Recomendação do Guardião")

    score_cons = resultado.get("score_consolidado", 0)
    recomendacao = resultado.get("recomendacao", "escalar")
    label_rec = _LABELS_RECOMENDACAO.get(recomendacao, recomendacao)
    cor_rec = _CORES_RECOMENDACAO.get(recomendacao, "gray")

    col_sc, col_rec = st.columns([1, 2])
    with col_sc:
        st.metric("Score Consolidado", f"{score_cons} / 100")
    with col_rec:
        st.markdown(f"### :{cor_rec}[{label_rec}]")

    just_cons = resultado.get("justificativa_consolidada", "")
    if just_cons:
        st.info(just_cons)

    divergencias = resultado.get("divergencias", [])
    if divergencias:
        with st.expander(f"⚡ Divergências identificadas ({len(divergencias)})"):
            for d in divergencias:
                st.warning(d)

    riscos_princ = resultado.get("principais_riscos", [])
    oportunidades = resultado.get("principais_oportunidades", [])

    if riscos_princ or oportunidades:
        col_r, col_o = st.columns(2)
        with col_r:
            if riscos_princ:
                st.markdown("**⚠️ Principais Riscos**")
                for r in riscos_princ:
                    st.markdown(f"- {r}")
        with col_o:
            if oportunidades:
                st.markdown("**💡 Oportunidades**")
                for o in oportunidades:
                    st.markdown(f"- {o}")

    limitacoes_g = resultado.get("limitacoes", [])
    if limitacoes_g:
        with st.expander("📌 Limitações da análise"):
            for lim in limitacoes_g:
                st.caption(f"— {lim}")

    # Download do relatório JSON (trilha de auditoria)
    st.divider()
    json_bytes = json.dumps(resultado, ensure_ascii=False, indent=2).encode("utf-8")
    st.download_button(
        label="⬇️ Baixar relatório JSON (trilha de auditoria)",
        data=json_bytes,
        file_name=f"relatorio_{resultado.get('regiao_id', 'regiao')}.json",
        mime="application/json",
    )


def _secao_historico():
    """Exibe o histórico e ranking de regiões analisadas."""
    historico = st.session_state.historico
    if not historico:
        st.info("Nenhuma região analisada nesta sessão. Execute o Conselho para uma região.")
        return

    ranking = _ranking()

    st.subheader("🏆 Ranking desta Sessão")
    st.caption(_AVISO_SIMULADO)

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

    st.subheader("📋 Histórico Detalhado")
    for item in historico:
        regiao_nome = item.get("regiao_nome", item.get("regiao_id", "—"))
        score = item.get("score_consolidado", 0)
        rec   = item.get("recomendacao", "—")
        label = _LABELS_RECOMENDACAO.get(rec, rec)
        with st.expander(f"{regiao_nome} — Score {score} — {label}"):
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
# Aplicação principal
# ---------------------------------------------------------------------------


def main():
    st.set_page_config(
        page_title="Conecta Conselho",
        page_icon="🌐",
        layout="wide",
    )

    _inicializar_estado()

    # Cabeçalho
    st.title("🌐 Conecta Conselho")
    st.caption("Sistema de apoio a decisões de expansão de conectividade | Trilha 3 · IBM SkillsBuild")
    st.warning(_AVISO_SIMULADO)

    # Abas principais
    aba_analise, aba_historico = st.tabs(["🔍 Análise de Região", "📚 Histórico e Ranking"])

    with aba_analise:
        regiao_id, regioes, executar = _secao_selecao()
        _secao_indicadores(regiao_id)

        if executar:
            with st.spinner(f"Executando o Conselho para {regiao_id}..."):
                try:
                    resultado = chamar_guardiao(regiao_id)
                    st.session_state[f"resultado_{regiao_id}"] = resultado
                    _registrar_historico(resultado)
                    if resultado.get("erro"):
                        st.error(f"Erro ao analisar região: {resultado['erro']}")
                    else:
                        st.success(f"Análise concluída para {resultado.get('regiao_nome', regiao_id)}!")
                except Exception as e:
                    st.error(f"Erro inesperado: {e}")

        # Exibe resultado se já tiver sido executado para esta região
        resultado_atual = st.session_state.get(f"resultado_{regiao_id}")
        if resultado_atual:
            _secao_resultado(resultado_atual)

    with aba_historico:
        st.caption(_AVISO_SIMULADO)
        _secao_historico()


if __name__ == "__main__":
    main()
