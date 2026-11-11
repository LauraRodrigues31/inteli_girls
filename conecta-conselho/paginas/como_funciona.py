"""
Página: Como funciona
Página inicial do Conecta Conselho — "how to play" interativo.

AVISO: Todos os dados são SIMULADOS e fictícios.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Configuração de paths — funciona de qualquer diretório de execução
# ---------------------------------------------------------------------------
_CC_DIR = Path(__file__).resolve().parent.parent   # conecta-conselho/
_ROOT   = _CC_DIR.parent                            # inteli_girls/

for _p in [str(_ROOT), str(_CC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------------
# Importa consolidar_pareceres via integracao (mantém o path canônico)
# ---------------------------------------------------------------------------
from integracao import consolidar_pareceres  # type: ignore[import]


# ---------------------------------------------------------------------------
# Constantes públicas (usadas também pelos testes)
# ---------------------------------------------------------------------------

# Scores reais das regiões (RESULTADOS_REGIOES.md — Tabela 1)
SCORES_REGIOES: dict[str, dict[str, int]] = {
    "Esperança": {
        "mercado": 63, "impacto_social": 66,
        "engenharia": 34, "orcamento": 20, "pontes": 43,
    },
    "Central": {
        "mercado": 37, "impacto_social": 30,
        "engenharia": 86, "orcamento": 76, "pontes": 66,
    },
    "Nova União": {
        "mercado": 50, "impacto_social": 78,
        "engenharia": 11, "orcamento": 0, "pontes": 21,
    },
}

# Labels amigáveis para cada agente
AGENTES: list[dict] = [
    {
        "chave": "mercado",
        "icone": "💰",
        "nome": "Mercado",
        "pergunta": "Vale a pena financeiramente?",
        "debate": "Avalia renda, crescimento, potencial de clientes e concorrência.",
    },
    {
        "chave": "impacto_social",
        "icone": "🏫",
        "nome": "Impacto Social",
        "pergunta": "Quem ganha com a conexão?",
        "debate": "Conta escolas, postos de saúde e famílias sem acesso.",
    },
    {
        "chave": "engenharia",
        "icone": "🔧",
        "nome": "Engenharia",
        "pergunta": "Dá para construir?",
        "debate": "Analisa distância do backbone, relevo e tecnologias disponíveis.",
    },
    {
        "chave": "orcamento",
        "icone": "📊",
        "nome": "Orçamento",
        "pergunta": "Cabe no custo e no prazo?",
        "debate": "Calcula CAPEX, payback e viabilidade financeira.",
    },
    {
        "chave": "pontes",
        "icone": "🤝",
        "nome": "Pontes",
        "pergunta": "Dá para tornar a região viável?",
        "debate": "Busca escolas, prefeituras e unidades de saúde como clientes âncora.",
    },
]

# Mapeamento de recomendação → cor CSS / rótulo amigável / regra
_INFO_REC: dict[str, dict] = {
    "investir_agora": {
        "cor": "#1a7f37",
        "fundo": "#d3f9d8",
        "emoji": "🟢",
        "label": "Investir agora",
        "regra": "Score ≥ 70, Orçamento ≥ 60 e Engenharia ≥ 60",
    },
    "realizar_piloto": {
        "cor": "#0969da",
        "fundo": "#dbeafe",
        "emoji": "🔵",
        "label": "Realizar piloto",
        "regra": "Score ≥ 50 (mas não atinge todos os critérios de investimento)",
    },
    "aguardar": {
        "cor": "#9a6700",
        "fundo": "#fef9c3",
        "emoji": "🟡",
        "label": "Aguardar",
        "regra": "Score abaixo de 50",
    },
    "analise_incompleta": {
        "cor": "#6e7781",
        "fundo": "#f6f8fa",
        "emoji": "⚫",
        "label": "Análise incompleta",
        "regra": "Um ou mais agentes falharam — não é possível recomendar",
    },
}


# ---------------------------------------------------------------------------
# Funções auxiliares (testáveis isoladamente)
# ---------------------------------------------------------------------------

def montar_pareceres(scores: dict[str, int], *, falha: bool = False) -> str:
    """
    Monta o JSON de pareceres mínimos para consolidar_pareceres.

    Args:
        scores: dict com chaves 'mercado', 'impacto_social', 'engenharia',
                'orcamento', 'pontes' e valores int 0–100.
        falha:  se True, insere erro no parecer de 'mercado' (simula falha).

    Returns:
        String JSON pronta para passar a consolidar_pareceres.
    """
    pareceres: dict = {}
    for agente in ("mercado", "impacto_social", "engenharia", "orcamento", "pontes"):
        score = int(scores.get(agente, 0))
        erro = f"Falha simulada no agente {agente}." if (falha and agente == "mercado") else None
        pareceres[agente] = {
            "agente": agente,
            "score": 0 if erro else score,
            "confianca": "nao_avaliada" if erro else "alta",
            "erro": erro,
            "indicadores": {},
        }
    return json.dumps(pareceres, ensure_ascii=False)


def extrair_resultado(scores: dict[str, int], *, falha: bool = False) -> dict:
    """
    Executa consolidar_pareceres e retorna o dicionário resultado.

    Returns:
        Dict com pelo menos: recomendacao, score_consolidado,
        atencao_prioritaria, pontos_criticos, divergencias, status.
    """
    pareceres_json = montar_pareceres(scores, falha=falha)
    resultado = consolidar_pareceres(pareceres_json)
    # Desempacota ToolResponse se necessário
    if hasattr(resultado, "content"):
        resultado = resultado.content
    return resultado


def frase_regra(resultado: dict) -> str:
    """Retorna uma frase curta explicando a regra que disparou a recomendação."""
    rec = resultado.get("recomendacao") or ""
    score = resultado.get("score_consolidado")
    status = resultado.get("status", "")

    if status == "analise_incompleta":
        return "Um agente falhou — resultado incompleto, revisão humana necessária."
    if rec == "investir_agora":
        return f"Score {score} ≥ 70, Orçamento ≥ 60 e Engenharia ≥ 60 → Investir agora."
    if rec == "realizar_piloto":
        return f"Score {score} ≥ 50 → Realizar piloto."
    if rec == "aguardar":
        return f"Score {score} < 50 → Aguardar."
    return ""


# ---------------------------------------------------------------------------
# Render principal
# ---------------------------------------------------------------------------

def render() -> None:  # noqa: PLR0912, PLR0915
    _AVISO = "⚠️ Dados simulados — não representam indicadores reais."

    # ── Seção 1: O problema ─────────────────────────────────────────────────
    st.title("📖 Como funciona")
    st.warning(_AVISO)

    st.header("O problema")
    col1, col2, col3 = st.columns(3)
    col1.metric(
        label="Domicílios sem internet",
        value="82%",
        help="Região Nova União — a mais desconectada da base simulada.",
    )
    col2.metric(
        label="Escolas sem conectividade",
        value="48 de 61",
        help="Região Horizonte — escolas sem conexão adequada.",
    )
    col3.metric(
        label="Unidades de saúde sem conexão",
        value="11 de 14",
        help="Região Esperança — postos de saúde sem conectividade adequada.",
    )

    st.markdown(
        """
Operadoras decidem onde expandir guiadas principalmente pelo retorno financeiro.
Regiões com muitas escolas e postos de saúde desconectados ficam para trás porque
o lucro esperado é baixo. O Conecta Conselho reúne cinco especialistas com pontos
de vista **opostos de propósito** — para que nenhuma decisão seja só pelo dinheiro.
        """
    )

    st.divider()

    # ── Seção 2: Conheça o conselho ─────────────────────────────────────────
    st.header("Conheça o conselho")

    cols = st.columns(3)
    for i, agente in enumerate(AGENTES):
        with cols[i % 3]:
            st.markdown(
                f"""
<div style="border:1px solid #e5e7eb;border-radius:8px;padding:14px;
            margin-bottom:8px;background:#f7f8fa;">
  <div style="font-size:1.6rem;margin-bottom:4px;">{agente['icone']}</div>
  <strong>{agente['nome']}</strong><br>
  <em style="color:#57606a;font-size:0.88rem;">{agente['pergunta']}</em><br>
  <span style="font-size:0.85rem;">{agente['debate']}</span>
</div>
""",
                unsafe_allow_html=True,
            )

    # Cartão do Guardião (linha própria)
    st.markdown(
        """
<div style="border:2px solid #3b82d4;border-radius:8px;padding:14px;
            background:#eff6ff;margin-top:4px;">
  <div style="font-size:1.6rem;margin-bottom:4px;">⚖️</div>
  <strong>Guardião</strong> — O que fazemos?<br>
  <span style="font-size:0.85rem;">
    Consolida os cinco pareceres com regras determinísticas e entrega uma
    recomendação: <strong>Investir agora</strong>, <strong>Realizar piloto</strong>
    ou <strong>Aguardar</strong>. Quando os dados são insuficientes, sinaliza
    <strong>Análise incompleta</strong>.
  </span>
</div>
""",
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Seção 3: Brinque com o Guardião ─────────────────────────────────────
    st.header("🎮 Brinque com o Guardião")
    st.caption(
        "Ajuste os scores dos agentes e veja a recomendação mudar em tempo real."
    )

    # Botões de atalho — preenchem session_state antes dos sliders
    # Valor inicial dos sliders vem só do session_state (Esperança na 1ª vez).
    # Passar value= junto com key= e session_state gera aviso do Streamlit.
    for k, v in SCORES_REGIOES["Esperança"].items():
        st.session_state.setdefault(f"slider_{k}", v)

    atalhos = [("Esperança", "Esperança"), ("Central", "Central"),
               ("Nova União", "Nova União"), ("Resetar", "Esperança")]
    for col, (rotulo, regiao) in zip(st.columns(4), atalhos):
        with col:
            if st.button(rotulo, use_container_width=True):
                for k, v in SCORES_REGIOES[regiao].items():
                    st.session_state[f"slider_{k}"] = v

    st.markdown("**Scores dos agentes (0–100):**")
    slider_vals: dict[str, int] = {}
    s_cols = st.columns(5)
    for i, agente in enumerate(AGENTES):
        chave = agente["chave"]
        with s_cols[i]:
            slider_vals[chave] = st.slider(
                f"{agente['icone']} {agente['nome']}",
                min_value=0,
                max_value=100,
                key=f"slider_{chave}",
            )

    # Checkbox de falha
    simular_falha = st.checkbox(
        "💥 Simular falha de um agente (Mercado)",
        value=False,
        key="cf_simular_falha",
    )

    # Executa consolidação ao vivo
    resultado = extrair_resultado(slider_vals, falha=simular_falha)
    rec   = resultado.get("recomendacao") or "analise_incompleta"
    score = resultado.get("score_consolidado")
    alerta = resultado.get("atencao_prioritaria", False)
    pontos = resultado.get("pontos_criticos", [])
    divs  = resultado.get("divergencias", [])
    status = resultado.get("status", "concluida")

    info = _INFO_REC.get(rec, _INFO_REC["analise_incompleta"])
    if status == "analise_incompleta":
        info = _INFO_REC["analise_incompleta"]

    # Exibe resultado
    st.markdown("---")
    st.markdown(
        f"""
<div style="border-left:5px solid {info['cor']};background:{info['fundo']};
            padding:14px 18px;border-radius:6px;margin-bottom:8px;">
  <div style="font-size:1.1rem;font-weight:700;color:{info['cor']};">
    {info['emoji']} {info['label']}
    {"— Score " + str(score) if score is not None else ""}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # Frase da regra
    frase = frase_regra(resultado)
    if frase:
        st.caption(f"📐 {frase}")

    # Alerta prioritário
    if alerta and pontos:
        st.error(f"⚠️ **Atenção prioritária:** {' · '.join(pontos)}")

    # Divergências
    if divs:
        with st.expander("⚖️ Conflitos entre especialistas"):
            for d in divs:
                st.write(f"- {d}")

    st.divider()

    # ── Seção 4: Como ler o resultado ───────────────────────────────────────
    st.header("📘 Como ler o resultado")

    for rec_key, info_rec in _INFO_REC.items():
        st.markdown(
            f"**{info_rec['emoji']} {info_rec['label']}** — {info_rec['regra']}",
        )

    st.markdown(
        """
**⚠️ Alerta de atenção prioritária** — aparece quando a dimensão mais crítica
(ex.: orçamento nulo ou engenharia inviável) pode impactar comunidades vulneráveis.
A decisão final é sempre de uma pessoa.
        """
    )

    st.divider()

    # ── Seção 5: Comece agora ───────────────────────────────────────────────
    st.header("🚀 Comece agora")
    # As páginas são registradas por função em paginas/rotas.py, então o link
    # precisa do objeto st.Page (um caminho "paginas/x.py" nunca é encontrado).
    from paginas.rotas import criar_paginas  # type: ignore[import]

    paginas = criar_paginas()
    _links = [
        ("analise",   "Analise uma região com os 5 agentes."),
        ("simulador", "Teste cenários hipotéticos e simule o mapa."),
    ]
    for col, (chave, help_txt) in zip(st.columns(2), _links):
        with col:
            st.page_link(paginas[chave], help=help_txt)

    # ── Rodapé ──────────────────────────────────────────────────────────────
    st.divider()
    st.caption(
        "Dados simulados · Decisão final sempre de uma pessoa "
        "· Agentes no IBM watsonx Orchestrate"
    )
