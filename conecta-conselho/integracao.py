"""
Camada de integração entre a interface Streamlit e os agentes do Conecta Conselho.

Modo de operação controlado pela variável de ambiente CC_MODO:
  - "local" (padrão): invoca diretamente as funções Python das tools/
  - "nuvem":          chama os 5 agentes IBM watsonx Orchestrate em paralelo
                      via cliente_nuvem.chamar_agente e consolida localmente

AVISO: Todos os dados retornados são SIMULADOS e fictícios.
"""

from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import dotenv_values as _dotenv_values

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

    resultado["fonte"] = "local"
    return resultado


# ---------------------------------------------------------------------------
# Consolidação via nuvem — 5 agentes IBM watsonx Orchestrate em paralelo
# ---------------------------------------------------------------------------

# Mapa de chave de parecer para variável de ambiente do agent_id
_AGENTE_ENV = {
    "mercado":        "CC_AGENT_ID_MERCADO",
    "impacto_social": "CC_AGENT_ID_SOCIAL",
    "engenharia":     "CC_AGENT_ID_ENGENHARIA",
    "orcamento":      "CC_AGENT_ID_ORCAMENTO",
    "pontes":         "CC_AGENT_ID_PONTES",
}

# Caminho do .env na raiz do projecto (mesmo padrão do cliente_nuvem.py)
_ENV_FILE = _ROOT / ".env"


def _ler_ids_agentes() -> dict[str, str]:
    """
    Lê os IDs de agente das variáveis CC_AGENT_ID_* com a seguinte prioridade:
      1. os.environ (variáveis de ambiente do processo — têm precedência)
      2. .env na raiz do projecto (via dotenv_values — nunca sobrescreve os.environ)

    Retorna um dict {chave_env: valor} com apenas as variáveis encontradas.
    """
    env_dot: dict[str, str] = {}
    if _ENV_FILE.exists():
        env_dot = {k: v for k, v in _dotenv_values(str(_ENV_FILE)).items() if v}

    resultado: dict[str, str] = {}
    for chave_env in _AGENTE_ENV.values():
        # os.environ tem prioridade
        valor = os.environ.get(chave_env, "").strip()
        if not valor:
            valor = env_dot.get(chave_env, "").strip()
        resultado[chave_env] = valor
    return resultado


def _verificar_credenciais_nuvem() -> tuple[bool, str]:
    """
    Verifica se todas as credenciais e IDs necessários estão no ambiente ou .env.
    Retorna (ok: bool, mensagem_de_aviso: str).
    Nunca imprime tokens, keys nem IDs.
    """
    ids = _ler_ids_agentes()
    ids_ausentes = [chave_env for chave_env, valor in ids.items() if not valor]
    if ids_ausentes:
        return False, f"IDs de agente ausentes (variáveis de ambiente ou .env): {', '.join(ids_ausentes)}"
    return True, ""


# Nomes amigáveis dos agentes para uso no callback (item 6)
_NOMES_AMIGAVEIS_AGENTES = {
    "mercado":        "Mercado",
    "impacto_social": "Impacto Social",
    "engenharia":     "Engenharia",
    "orcamento":      "Orçamento",
    "pontes":         "Pontes",
}


def _consolidar_nuvem(
    regiao_id: str,
    *,
    ao_concluir_agente=None,
) -> dict:
    """
    Chama os 5 agentes IBM watsonx Orchestrate em paralelo via ThreadPoolExecutor.
    De cada resposta extrai choices[0].message.content e passa para extrair_json.
    Se um agente falhar (incluindo {"erro": ...} na resposta), monta parecer com
    "erro" preenchido. Consolida com consolidar_pareceres e devolve o mesmo
    formato do modo local.

    Args:
        regiao_id: Identificador da região.
        ao_concluir_agente: Callback opcional chamado na thread principal quando
            cada agente termina.
            Assinatura: ao_concluir_agente(nome: str, sucesso: bool, tempo: float)
            onde nome é o nome amigável do agente, sucesso indica se não houve
            erro, e tempo é o tempo em segundos. Comportamento sem callback não
            muda.
    """
    import importlib as _imp
    cliente_nuvem = _imp.import_module("cliente_nuvem")

    t_inicio = time.monotonic()

    # Lê IDs do .env / os.environ uma única vez (evita re-leitura por thread)
    ids_agentes = _ler_ids_agentes()

    def _chamar_agente(chave: str) -> tuple[str, dict, bool, float]:
        """
        Chama um agente na nuvem e retorna (chave, parecer_dict, sucesso, tempo).
        O callback NÃO é chamado aqui — é responsabilidade da thread principal
        para que o Streamlit possa atualizar a tela sem conflito de threads.
        """
        t_agente = time.monotonic()
        env_var = _AGENTE_ENV[chave]
        agent_id = ids_agentes.get(env_var, "").strip()
        if not agent_id:
            return chave, {
                "score": 0,
                "confianca": "nao_avaliada",
                "justificativa": "",
                "riscos": [],
                "erro": f"ID do agente '{chave}' não configurado (variável {env_var} ausente).",
            }, False, round(time.monotonic() - t_agente, 2)
        try:
            # O LLM do agente às vezes responde com texto fora do formato JSON.
            # Nesse caso (e só nele) tenta de novo, até 3 tentativas no total.
            _MSG_SEM_JSON = "Não foi possível extrair JSON da resposta."
            for _tentativa in range(3):
                resposta = cliente_nuvem.chamar_agente(
                    agent_id, f"Analise a região {regiao_id}"
                )
                # chamar_agente devolve {"erro": ...} em vez de levantar excepção
                if "erro" in resposta:
                    return chave, {
                        "score": 0,
                        "confianca": "nao_avaliada",
                        "justificativa": "",
                        "riscos": [],
                        "erro": resposta["erro"],
                    }, False, round(time.monotonic() - t_agente, 2)
                conteudo = resposta["choices"][0]["message"]["content"]
                parecer = cliente_nuvem.extrair_json(conteudo)
                if parecer.get("erro") != _MSG_SEM_JSON:
                    break
            # extrair_json devolve {"erro": "..."} quando não consegue parsear.
            # Verificamos o valor (truthy) para não confundir com {"erro": None}
            # que é um campo legítimo nos pareceres dos agentes.
            if parecer.get("erro"):
                return chave, {
                    "score": 0,
                    "confianca": "nao_avaliada",
                    "justificativa": "",
                    "riscos": [],
                    "erro": parecer["erro"],
                }, False, round(time.monotonic() - t_agente, 2)
            return chave, parecer, True, round(time.monotonic() - t_agente, 2)
        except Exception as exc:  # noqa: BLE001
            return chave, {
                "score": 0,
                "confianca": "nao_avaliada",
                "justificativa": "",
                "riscos": [],
                "erro": f"Falha ao chamar agente '{chave}': {exc}",
            }, False, round(time.monotonic() - t_agente, 2)

    pareceres_brutos: dict = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futuros = {
            executor.submit(_chamar_agente, chave): chave
            for chave in _AGENTE_ENV
        }
        # O loop roda na thread principal — seguro para chamar o Streamlit
        for futuro in as_completed(futuros):
            chave, parecer, sucesso, tempo = futuro.result()
            pareceres_brutos[chave] = parecer
            if ao_concluir_agente is not None:
                ao_concluir_agente(
                    _NOMES_AMIGAVEIS_AGENTES.get(chave, chave),
                    sucesso,
                    tempo,
                )

    # Consolida localmente — mesma lógica do modo local
    resultado = _desempacotar(
        consolidar_pareceres(_json.dumps(pareceres_brutos, ensure_ascii=False))
    )

    # Preenche regiao_id e regiao_nome se o Guardião não conseguiu extrair
    if not resultado.get("regiao_id"):
        resultado["regiao_id"] = regiao_id
    if not resultado.get("regiao_nome"):
        for p in pareceres_brutos.values():
            if p.get("regiao_nome"):
                resultado["regiao_nome"] = p["regiao_nome"]
                break

    t_total = round(time.monotonic() - t_inicio, 2)
    resultado["fonte"] = "nuvem"
    resultado["tempo_analise_segundos"] = t_total
    return resultado


# ---------------------------------------------------------------------------
# Ponto de entrada público
# ---------------------------------------------------------------------------

def chamar_guardiao(
    regiao_id: str,
    *,
    fonte: str | None = None,
    ao_concluir_agente=None,
) -> dict:
    """
    Camada de integração com o Agente Guardião.

    Modo "local" (padrão, CC_MODO != "nuvem" e fonte != "nuvem"):
        Chama diretamente os 5 agentes Python e consolida com tool_guardiao.

    Modo "nuvem" (CC_MODO=nuvem ou fonte="nuvem"):
        Chama os 5 agentes IBM watsonx Orchestrate em paralelo via
        cliente_nuvem.chamar_agente e consolida localmente.

    Args:
        regiao_id: Identificador da região (ex: 'aurora', 'central').
        fonte:     Sobrescreve CC_MODO quando fornecido ('local' | 'nuvem').
        ao_concluir_agente: Callback opcional chamado ao fim de cada agente no
            modo nuvem. Assinatura: ao_concluir_agente(nome, sucesso, tempo).
            Ignorado no modo local. Comportamento sem callback não muda.

    Returns:
        Dicionário com pareceres dos 5 agentes e recomendação do Guardião,
        incluindo os campos "fonte" e "tempo_analise_segundos".
    """
    modo_env = os.environ.get("CC_MODO", "local").strip().lower()
    modo_efetivo = fonte if fonte in ("local", "nuvem") else modo_env

    if modo_efetivo == "nuvem":
        t_inicio = time.monotonic()
        resultado = _consolidar_nuvem(regiao_id, ao_concluir_agente=ao_concluir_agente)
        if "tempo_analise_segundos" not in resultado:
            resultado["tempo_analise_segundos"] = round(time.monotonic() - t_inicio, 2)
        return resultado

    t_inicio = time.monotonic()
    resultado = _consolidar_local(regiao_id)
    resultado["tempo_analise_segundos"] = round(time.monotonic() - t_inicio, 2)
    return resultado
