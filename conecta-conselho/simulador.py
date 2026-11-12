"""
Motor de cenários do Conecta Conselho.

Compara o CENÁRIO BASE (dados originais da base) com um CENÁRIO SIMULADO
onde o usuário ajusta distância do backbone, teto de investimento e/ou
parcerias — e verifica como a recomendação muda.

AVISO: Todos os cálculos usam dados SIMULADOS. Não usar para decisões reais.
Recalculado localmente com as mesmas regras dos agentes, sem consultar a IBM.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuração de paths
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).resolve().parent.parent          # inteli_girls/
_CC_DIR = Path(__file__).resolve().parent               # inteli_girls/conecta-conselho/

for _p in [str(_ROOT), str(_CC_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _importar_tool(nome_modulo: str, nome_arquivo: str):
    """Importa uma tool da raiz via importlib para evitar colisão de pacotes."""
    caminho = _ROOT / "tools" / nome_arquivo
    spec = importlib.util.spec_from_file_location(nome_modulo, caminho)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ---------------------------------------------------------------------------
# Importação das ferramentas necessárias
# ---------------------------------------------------------------------------

_mod_mercado    = _importar_tool("tool_mercado",    "tool_mercado.py")
_mod_social     = _importar_tool("tool_social",     "tool_social.py")
_mod_engenharia = _importar_tool("tool_engenharia", "tool_engenharia.py")
_mod_orcamento  = _importar_tool("tool_orcamento",  "tool_orcamento.py")
_mod_pontes     = _importar_tool("tool_pontes",     "tool_pontes.py")
_mod_guardiao   = _importar_tool("tool_guardiao",   "tool_guardiao.py")

# Importa consultar_regiao do subpacote conecta-conselho/tools/
_consultar_regiao_path = _CC_DIR / "tools" / "consultar_regiao.py"
_spec_cr = importlib.util.spec_from_file_location("cc_consultar_regiao", _consultar_regiao_path)
_mod_cr = importlib.util.module_from_spec(_spec_cr)  # type: ignore[arg-type]
_spec_cr.loader.exec_module(_mod_cr)  # type: ignore[union-attr]
consultar_regiao = _mod_cr.consultar_regiao


def _desempacotar(resultado) -> dict:
    """Retorna o dict de conteúdo de um ToolResponse ou o próprio dict."""
    if hasattr(resultado, "content"):
        return resultado.content
    return resultado


# ---------------------------------------------------------------------------
# Coleta dos pareceres base (5 agentes locais)
# ---------------------------------------------------------------------------

def _coletar_pareceres_base(regiao_id: str) -> dict:
    """Executa os 5 agentes localmente e retorna os pareceres desempacotados."""
    return {
        "mercado":        _desempacotar(_mod_mercado.analisar_mercado(regiao_id)),
        "impacto_social": _desempacotar(_mod_social.analisar_impacto_social(regiao_id)),
        "engenharia":     _desempacotar(_mod_engenharia.analisar_engenharia(regiao_id)),
        "orcamento":      _desempacotar(_mod_orcamento.analisar_orcamento(regiao_id)),
        "pontes":         _desempacotar(_mod_pontes.analisar_pontes(regiao_id)),
    }


def _consolidar(pareceres: dict) -> dict:
    """Chama consolidar_pareceres do Guardião e desempacota o resultado."""
    return _desempacotar(
        _mod_guardiao.consolidar_pareceres(
            json.dumps(pareceres, ensure_ascii=False)
        )
    )


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def simular_cenario(
    regiao_id: str,
    distancia_backbone_km: float | None = None,
    teto_investimento_reais: float | None = None,
    usar_parcerias: bool = False,
) -> dict:
    """
    Compara o cenário base de uma região com um cenário simulado.

    O cenário simulado aplica ajustes determinísticos (sem LLM) e reconsolida
    com as mesmas regras do Guardião. Mercado, Impacto Social e Pontes não mudam.

    Args:
        regiao_id: Identificador da região (ex: 'esperanca', 'nova_uniao').
        distancia_backbone_km: Nova distância ao backbone (0–200 km).
            Se None, mantém o valor original.
        teto_investimento_reais: Novo teto de investimento (> 0 em R$).
            Substitui orcamento_disponivel_reais.
            Se None, mantém o valor original.
        usar_parcerias: Se True, reduz o CAPEX pelo percentual_economia_potencial_pct
            do Agente Pontes e recalcula orçamento/payback.

    Returns:
        Dicionário com:
          regiao_id, regiao_nome,
          base (resultado do Guardião com dados originais),
          simulado (resultado do Guardião com dados ajustados),
          parametros (valores usados na simulação),
          mudancas (lista de strings descrevendo o que mudou),
          premissas (frases explicando cada regra aplicada),
          simulado_localmente (True)
        Ou {"erro": "<mensagem>"} para entradas inválidas.
    """
    # --- Validações de entrada ---
    regiao_id = regiao_id.strip().lower() if isinstance(regiao_id, str) else ""

    regiao_dados = consultar_regiao(regiao_id)
    if "erro" in regiao_dados:
        return {"erro": f"Região '{regiao_id}' não encontrada na base de dados."}

    if distancia_backbone_km is not None:
        if not (0 <= distancia_backbone_km <= 200):
            return {"erro": "distancia_backbone_km deve estar entre 0 e 200."}

    if teto_investimento_reais is not None:
        if teto_investimento_reais <= 0:
            return {"erro": "teto_investimento_reais deve ser maior que zero."}

    regiao_nome = regiao_dados["nome"]

    # --- Pareceres base ---
    pareceres_base = _coletar_pareceres_base(regiao_id)
    resultado_base = _consolidar(pareceres_base)
    resultado_base["regiao_id"] = regiao_id
    if not resultado_base.get("regiao_nome"):
        resultado_base["regiao_nome"] = regiao_nome

    # --- Pareceres simulados (cópias profundas) ---
    pareceres_sim = copy.deepcopy(pareceres_base)

    mudancas: list[str] = []
    premissas: list[str] = []
    parametros: dict = {
        "distancia_backbone_km": distancia_backbone_km,
        "teto_investimento_reais": teto_investimento_reais,
        "usar_parcerias": usar_parcerias,
    }

    # --- Ajuste de engenharia: nova distância do backbone ---
    if distancia_backbone_km is not None:
        p_eng = pareceres_sim["engenharia"]
        ind_eng = dict(p_eng.get("indicadores") or {})
        dist_original = ind_eng.get("distancia_backbone_km",
                                    regiao_dados["engenharia"]["distancia_backbone_km"])

        # Monta dados de engenharia com nova distância
        dados_eng = dict(regiao_dados["engenharia"])
        dados_eng["distancia_backbone_km"] = distancia_backbone_km

        scores_eng = _mod_engenharia.calcular_score_engenharia(dados_eng)
        score_eng_novo = scores_eng["score_final"]
        score_eng_orig = p_eng.get("score", 0)

        # Atualiza parecer de engenharia
        p_eng["score"] = score_eng_novo
        ind_eng["distancia_backbone_km"] = distancia_backbone_km
        ind_eng["score_backbone"] = scores_eng["score_backbone"]
        p_eng["indicadores"] = ind_eng
        pareceres_sim["engenharia"] = p_eng

        premissas.append(
            f"Nova distância do backbone: {distancia_backbone_km} km "
            f"(original: {dist_original} km). "
            f"Score de engenharia recalculado com calcular_score_engenharia."
        )
        mudancas.append(
            f"Engenharia: {score_eng_orig} → {score_eng_novo}"
        )

    # --- Ajuste de orçamento: parcerias e/ou teto ---
    # Obtém dados financeiros e de parcerias originais
    dados_fin = dict(regiao_dados["financeiro"])
    p_orc = pareceres_sim["orcamento"]
    ind_orc = dict(p_orc.get("indicadores") or {})
    score_orc_orig = p_orc.get("score", 0)

    capex_original = float(dados_fin["capex_reais"])
    capex_novo = capex_original
    orcamento_novo = float(dados_fin["orcamento_disponivel_reais"])

    if usar_parcerias:
        pct = float(regiao_dados["parcerias"].get("percentual_economia_potencial_pct", 0))
        capex_novo = round(capex_original * (1 - pct / 100))
        premissas.append(
            f"Parcerias ativadas: CAPEX reduzido de R$ {int(capex_original):,} "
            f"para R$ {capex_novo:,} ({pct}% de economia via percentual_economia_potencial_pct)."
            .replace(",", ".")
        )

    if teto_investimento_reais is not None:
        orcamento_novo = float(teto_investimento_reais)
        premissas.append(
            f"Teto de investimento definido: orcamento_disponivel_reais = "
            f"R$ {int(orcamento_novo):,}.".replace(",", ".")
        )

    if usar_parcerias or teto_investimento_reais is not None:
        # Recalcula payback com novo capex e orçamento
        receita = float(dados_fin["receita_mensal_reais"])
        opex = float(dados_fin["opex_mensal_reais"])
        margem = receita - opex
        if margem > 0:
            payback_novo = round(capex_novo / margem)
        else:
            payback_novo = None

        # Monta novos dados financeiros para recalcular os indicadores
        dados_fin_sim = dict(dados_fin)
        dados_fin_sim["capex_reais"] = capex_novo
        dados_fin_sim["orcamento_disponivel_reais"] = int(orcamento_novo)
        dados_fin_sim["payback_meses"] = payback_novo

        indicadores_sim = _mod_orcamento.calcular_indicadores_financeiros(dados_fin_sim)
        score_orc_novo, indicadores_sim = _mod_orcamento.calcular_score_orcamento(indicadores_sim)

        p_orc["score"] = score_orc_novo
        p_orc["indicadores"] = indicadores_sim
        pareceres_sim["orcamento"] = p_orc

        if score_orc_novo != score_orc_orig:
            mudancas.append(f"Orçamento: {score_orc_orig} → {score_orc_novo}")

    # --- Consolida simulado ---
    resultado_simulado = _consolidar(pareceres_sim)
    resultado_simulado["regiao_id"] = regiao_id
    if not resultado_simulado.get("regiao_nome"):
        resultado_simulado["regiao_nome"] = regiao_nome

    # Adiciona mudança de recomendação, se houver
    rec_base = resultado_base.get("recomendacao")
    rec_sim = resultado_simulado.get("recomendacao")
    score_base = resultado_base.get("score_consolidado")
    score_sim = resultado_simulado.get("score_consolidado")

    if score_base != score_sim:
        mudancas.append(f"Score consolidado: {score_base} → {score_sim}")
    if rec_base != rec_sim:
        mudancas.append(f"Recomendação: {rec_base} → {rec_sim}")

    return {
        "regiao_id": regiao_id,
        "regiao_nome": regiao_nome,
        "base": resultado_base,
        "simulado": resultado_simulado,
        "parametros": parametros,
        "mudancas": mudancas,
        "premissas": premissas,
        "simulado_localmente": True,
    }
