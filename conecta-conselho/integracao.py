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
_mod_guardiao   = _importar_tool("tool_guardiao",   "tool_guardiao.py")

analisar_mercado        = _mod_mercado.analisar_mercado
analisar_impacto_social = _mod_social.analisar_impacto_social
analisar_engenharia     = _mod_engenharia.analisar_engenharia
analisar_orcamento      = _mod_orcamento.analisar_orcamento
analisar_pontes         = _mod_pontes.analisar_pontes
consolidar_pareceres    = _mod_guardiao.consolidar_pareceres


# ---------------------------------------------------------------------------
# Utilitário — desempacota ToolResponse quando o ADK está ativo
# ---------------------------------------------------------------------------

def _desempacotar(resultado) -> dict:
    """Retorna o dict de conteúdo de um ToolResponse ou o próprio dict."""
    if hasattr(resultado, "content"):
        return resultado.content
    return resultado


# ---------------------------------------------------------------------------
# Aliases de compatibilidade — mantidos para testes existentes que importam
# _calcular_score_consolidado e _PESOS diretamente de integracao.py
# ---------------------------------------------------------------------------

_PESOS = _mod_guardiao._PESOS


def _calcular_score_consolidado(pareceres: dict) -> int:
    """Delega para a implementação canônica em tool_guardiao."""
    return _mod_guardiao._calcular_score_consolidado(pareceres)


# ---------------------------------------------------------------------------
# Consolidação local — fonte única: tool_guardiao.consolidar_pareceres
# ---------------------------------------------------------------------------

import json as _json


def _consolidar_local(regiao_id: str) -> dict:
    """
    Executa os 5 agentes localmente e delega toda a lógica de consolidação
    para consolidar_pareceres (tool_guardiao), que é a fonte única de verdade.
    """
    # Monta os 5 pareceres completos (desempacotados)
    pareceres_brutos = {
        "mercado":        _desempacotar(analisar_mercado(regiao_id)),
        "impacto_social": _desempacotar(analisar_impacto_social(regiao_id)),
        "engenharia":     _desempacotar(analisar_engenharia(regiao_id)),
        "orcamento":      _desempacotar(analisar_orcamento(regiao_id)),
        "pontes":         _desempacotar(analisar_pontes(regiao_id)),
    }

    # Passa para a tool do Guardião como fonte única de verdade
    resultado = _desempacotar(
        consolidar_pareceres(_json.dumps(pareceres_brutos, ensure_ascii=False))
    )

    # Garante regiao_nome preenchido (o Guardião extrai do primeiro parecer válido;
    # se a região não existe, os pareceres terão regiao_nome vazio)
    if not resultado.get("regiao_nome"):
        # Tenta pegar do primeiro parecer que tiver
        for p in pareceres_brutos.values():
            if p.get("regiao_nome"):
                resultado["regiao_nome"] = p["regiao_nome"]
                break

    # Se todos os pareceres têm erro (região inexistente), propaga o erro
    if not resultado.get("erro"):
        primeiro_erro = next(
            (p.get("erro") for p in pareceres_brutos.values() if p.get("erro")), None
        )
        # Só propaga se TODOS tiverem erro (região realmente inexistente)
        todos_com_erro = all(p.get("erro") for p in pareceres_brutos.values())
        if todos_com_erro and primeiro_erro:
            resultado["erro"] = primeiro_erro

    return resultado


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
