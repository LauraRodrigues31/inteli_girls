"""
Camada de integração entre a interface Streamlit e os agentes do Conecta Conselho.

Modo de operação controlado pela variável de ambiente CC_MODO:
  - "local" (padrão): invoca diretamente as funções Python das tools/
  - "nuvem":          stub — levanta NotImplementedError (a implementar via ADK)

AVISO: Todos os dados retornados são SIMULADOS e fictícios.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuração de paths — garante que tools/ (raiz) e conecta-conselho/ estão
# acessíveis independente do diretório de execução.
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).resolve().parent.parent          # inteli_girls/
_CC_DIR = Path(__file__).resolve().parent               # inteli_girls/conecta-conselho/

for _p in [str(_ROOT), str(_CC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------------
# Importação das ferramentas dos agentes especialistas
# ---------------------------------------------------------------------------

import importlib.util as _ilu


def _importar_tool(nome_modulo: str, nome_arquivo: str):
    """Importa uma tool da raiz via importlib para evitar colisão de pacotes."""
    caminho = _ROOT / "tools" / nome_arquivo
    spec = _ilu.spec_from_file_location(nome_modulo, caminho)
    mod = _ilu.module_from_spec(spec)   # type: ignore[arg-type]
    spec.loader.exec_module(mod)        # type: ignore[union-attr]
    return mod


_mod_mercado    = _importar_tool("tool_mercado",    "tool_mercado.py")
_mod_social     = _importar_tool("tool_social",     "tool_social.py")
_mod_engenharia = _importar_tool("tool_engenharia", "tool_engenharia.py")
_mod_orcamento  = _importar_tool("tool_orcamento",  "tool_orcamento.py")
_mod_pontes     = _importar_tool("tool_pontes",     "tool_pontes.py")

analisar_mercado       = _mod_mercado.analisar_mercado
analisar_impacto_social = _mod_social.analisar_impacto_social
analisar_engenharia    = _mod_engenharia.analisar_engenharia
analisar_orcamento     = _mod_orcamento.analisar_orcamento
analisar_pontes        = _mod_pontes.analisar_pontes


# ---------------------------------------------------------------------------
# Utilitário — desempacota ToolResponse quando o ADK está ativo
# ---------------------------------------------------------------------------

def _desempacotar(resultado) -> dict:
    """Retorna o dict de conteúdo de um ToolResponse ou o próprio dict."""
    if hasattr(resultado, "content"):
        return resultado.content
    return resultado


# ---------------------------------------------------------------------------
# Lógica local do Guardião (sem chamar a instância IBM Cloud)
# ---------------------------------------------------------------------------

_PESOS = {
    "mercado":        0.20,
    "impacto_social": 0.20,
    "engenharia":     0.25,
    "orcamento":      0.25,
    "pontes":         0.10,
}


def _calcular_score_consolidado(pareceres: dict) -> int:
    """Média ponderada dos cinco scores conforme Seção 11."""
    return round(
        _PESOS["mercado"]        * pareceres["mercado"]["score"] +
        _PESOS["impacto_social"] * pareceres["impacto_social"]["score"] +
        _PESOS["engenharia"]     * pareceres["engenharia"]["score"] +
        _PESOS["orcamento"]      * pareceres["orcamento"]["score"] +
        _PESOS["pontes"]         * pareceres["pontes"]["score"]
    )


def _determinar_recomendacao(score: int, pareceres: dict) -> str:
    """Critérios objetivos da Seção 11."""
    sc_eng = pareceres["engenharia"]["score"]
    sc_orc = pareceres["orcamento"]["score"]
    if score >= 70 and sc_orc >= 60 and sc_eng >= 60:
        return "investir_agora"
    if score >= 50:
        return "realizar_piloto"
    if score >= 30:
        return "aguardar"
    return "escalar"


def _identificar_divergencias(pareceres: dict) -> list[str]:
    """Detecta tensões conforme Seção 11."""
    divergencias = []
    sc_social = pareceres["impacto_social"]["score"]
    sc_orc    = pareceres["orcamento"]["score"]
    sc_eng    = pareceres["engenharia"]["score"]
    sc_merc   = pareceres["mercado"]["score"]
    sc_pontes = pareceres["pontes"]["score"]

    if abs(sc_social - sc_orc) > 30:
        divergencias.append(
            f"Alto impacto social (score {sc_social}) contrastado com viabilidade "
            f"financeira {'baixa' if sc_orc < sc_social else 'maior'} (score {sc_orc}). "
            "Parcerias e subsídios podem ser necessários para viabilização."
        )
    if sc_eng < 40 and sc_merc > 60:
        divergencias.append(
            f"Boa demanda de mercado (score {sc_merc}) mas viabilidade técnica baixa "
            f"(score {sc_eng}). Investimento em infraestrutura adicional pode ser necessário."
        )
    if sc_pontes > 70 and sc_orc < 40:
        divergencias.append(
            f"Parcerias estratégicas promissoras (score {sc_pontes}) podem viabilizar "
            f"o que o orçamento não suporta sozinho (score {sc_orc})."
        )
    return divergencias


def _consolidar_local(regiao_id: str) -> dict:
    """
    Executa os 5 agentes localmente e monta a saída do Guardião conforme Seção 11.
    Função provisória enquanto tool_guardiao.py não existir.
    """
    from tools.consultar_regiao import consultar_regiao  # type: ignore[import]

    # Verifica se a região existe
    dados_regiao = consultar_regiao(regiao_id)
    if "erro" in dados_regiao:
        return {
            "agente": "guardiao",
            "regiao_id": regiao_id,
            "regiao_nome": None,
            "recomendacao": "escalar",
            "score_consolidado": 0,
            "pareceres": {},
            "divergencias": [],
            "justificativa_consolidada": f"Região '{regiao_id}' não encontrada na base de dados.",
            "principais_riscos": [],
            "principais_oportunidades": [],
            "limitacoes": ["Recomendação baseada em dados simulados e pesos hipotéticos definidos para o MVP."],
            "simulado": True,
            "erro": dados_regiao["erro"],
        }

    regiao_nome = dados_regiao.get("nome", regiao_id)

    # Chama os 5 agentes e desempacota ToolResponse se necessário
    pareceres_brutos = {
        "mercado":        _desempacotar(analisar_mercado(regiao_id)),
        "impacto_social": _desempacotar(analisar_impacto_social(regiao_id)),
        "engenharia":     _desempacotar(analisar_engenharia(regiao_id)),
        "orcamento":      _desempacotar(analisar_orcamento(regiao_id)),
        "pontes":         _desempacotar(analisar_pontes(regiao_id)),
    }

    # Resumo para o campo pareceres (sem indicadores brutos)
    pareceres = {
        nome: {
            "score":       p.get("score", 0),
            "confianca":   p.get("confianca", "nao_avaliada"),
            "justificativa": p.get("justificativa", ""),
            "riscos":      p.get("riscos", []),
            "limitacoes":  p.get("limitacoes", []),
            "erro":        p.get("erro"),
        }
        for nome, p in pareceres_brutos.items()
    }

    score = _calcular_score_consolidado(pareceres)
    recomendacao = _determinar_recomendacao(score, pareceres)
    divergencias = _identificar_divergencias(pareceres)

    # Agrega riscos e oportunidades
    riscos = []
    for p in pareceres_brutos.values():
        for r in p.get("riscos", []):
            if r not in riscos:
                riscos.append(r)

    # Oportunidades: instituições âncora identificadas por Pontes
    oportunidades: list[str] = []
    ind_pontes = pareceres_brutos["pontes"].get("indicadores", {})
    publicos = ind_pontes.get("parceiros_publicos_possiveis", [])
    privados = ind_pontes.get("parceiros_privados_possiveis", [])
    if publicos or privados:
        oportunidades.append(
            f"Possíveis parceiros identificados: {', '.join(publicos + privados)}."
        )

    justificativa = (
        f"Análise consolidada de {regiao_nome}: "
        f"Mercado ({pareceres['mercado']['score']}), "
        f"Social ({pareceres['impacto_social']['score']}), "
        f"Engenharia ({pareceres['engenharia']['score']}), "
        f"Orçamento ({pareceres['orcamento']['score']}), "
        f"Pontes ({pareceres['pontes']['score']}). "
        f"Score consolidado de {score}/100 leva à recomendação: {recomendacao.replace('_', ' ')}. "
        f"{'Divergências detectadas entre perspectivas. ' if divergencias else ''}"
        "Resultado baseado em dados simulados para fins de demonstração do MVP."
    )

    return {
        "agente": "guardiao",
        "regiao_id": regiao_id,
        "regiao_nome": regiao_nome,
        "recomendacao": recomendacao,
        "score_consolidado": score,
        "pareceres": pareceres,
        "divergencias": divergencias,
        "justificativa_consolidada": justificativa,
        "principais_riscos": riscos[:5],
        "principais_oportunidades": oportunidades,
        "limitacoes": [
            "Recomendação baseada em dados simulados e pesos hipotéticos definidos para o MVP."
        ],
        "simulado": True,
        "erro": None,
    }


# ---------------------------------------------------------------------------
# Ponto de entrada público
# ---------------------------------------------------------------------------

def chamar_guardiao(regiao_id: str) -> dict:
    """
    Camada de integração com o Agente Guardião.

    Modo "local" (padrão, CC_MODO != "nuvem"):
        Chama diretamente os 5 agentes Python e consolida conforme Seção 11.

    Modo "nuvem" (CC_MODO=nuvem):
        Stub — NotImplementedError (integração IBM Cloud a implementar).

    Args:
        regiao_id: Identificador da região (ex: 'aurora', 'central').

    Returns:
        Dicionário com pareceres dos 5 agentes e recomendação do Guardião.
    """
    modo = os.environ.get("CC_MODO", "local").strip().lower()

    if modo == "nuvem":
        raise NotImplementedError(
            "Modo 'nuvem' não implementado. "
            "Substituir pelo cliente ibm_watsonx_orchestrate quando disponível."
        )

    return _consolidar_local(regiao_id)
