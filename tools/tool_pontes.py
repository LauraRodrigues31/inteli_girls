"""
Ferramenta do Agente Pontes — Conecta Conselho.

Analisa oportunidades de parcerias estratégicas e compartilhamento de
infraestrutura para expansão de conectividade em uma região.

Agente: pontes
Integrante: Integrante 5

AVISO: Todos os dados retornados são SIMULADOS e fictícios.
Nenhum contrato ou acordo real existe.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict

from ibm_watsonx_orchestrate.agent_builder.tools import tool

# ---------------------------------------------------------------------------
# Import robusto de consultar_regiao — funciona mesmo com hífen no nome do dir
# ---------------------------------------------------------------------------
_consultar_regiao_path = (
    Path(__file__).parent.parent / "conecta-conselho" / "tools" / "consultar_regiao.py"
)
_spec = importlib.util.spec_from_file_location("consultar_regiao", _consultar_regiao_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

consultar_parcerias = _mod.consultar_parcerias
listar_ids_regioes = _mod.listar_ids_regioes

_AVISO_SIMULADO = "Dado simulado — não reflete condições reais"
_AVISO_HIPOTETICO = (
    "Parcerias são possibilidades hipotéticas simuladas. "
    "Nenhum contrato ou acordo real existe."
)


def _calcular_score_pontes(dados: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula o score de pontes e os sub-scores de 0 a 100.

    Retorna dicionário com score_final e cada sub-score individual.
    """
    publicos = dados["parceiros_publicos_possiveis"]
    privados = dados["parceiros_privados_possiveis"]
    total = len(publicos) + len(privados)

    score_quantidade_parceiros = min(100, total / 10 * 100)
    score_infraestrutura = 80 if dados["infraestrutura_compartilhavel"] else 20
    score_economia_potencial = dados["percentual_economia_potencial_pct"]
    score_maturidade = {"baixa": 20, "média": 60, "alta": 100}.get(
        dados["maturidade_parcerias"], 20
    )

    score_final = round(
        0.30 * score_quantidade_parceiros
        + 0.25 * score_infraestrutura
        + 0.25 * score_economia_potencial
        + 0.20 * score_maturidade
    )

    return {
        "score_final": score_final,
        "score_quantidade_parceiros": round(score_quantidade_parceiros),
        "score_infraestrutura": score_infraestrutura,
        "score_economia_potencial": score_economia_potencial,
        "score_maturidade": score_maturidade,
    }


def _calcular_confianca(dados: Dict[str, Any]) -> str:
    """
    Determina a confiança com base na completude dos campos obrigatórios.
    Regra objetiva — não é juízo do LLM (Seção 3.3 do padrão).
    """
    campos_criticos = [
        "parceiros_publicos_possiveis",
        "parceiros_privados_possiveis",
        "infraestrutura_compartilhavel",
        "maturidade_parcerias",
        "percentual_economia_potencial_pct",
        "quantidade_instituicoes_ancora",
        "oportunidades_reducao_custos",
    ]
    presentes = sum(1 for c in campos_criticos if dados.get(c) is not None)
    if presentes == len(campos_criticos):
        return "alta"
    elif presentes >= 5:
        return "media"
    else:
        return "baixa"


@tool
def analisar_pontes(regiao_id: str) -> dict:
    """
    Analisa o potencial de parcerias estratégicas e compartilhamento de
    infraestrutura de uma região para expansão de conectividade.

    Args:
        regiao_id: Identificador único da região (ex: 'vale_verde', 'aurora').

    Returns:
        Dicionário com score de 0 a 100, indicadores detalhados de parcerias,
        confiança, justificativa, riscos e limitações.
        Retorna erro e score 0 se a região não existir.
    """
    print(f"[INFO][agente_pontes] Consultando região: {regiao_id}")
    resultado = consultar_parcerias(regiao_id)

    # Região não encontrada
    if "erro" in resultado:
        ids_validos = ", ".join(listar_ids_regioes())
        print(f"[ERRO][agente_pontes] Região não encontrada: {regiao_id}", file=sys.stderr)
        return {
            "agente": "pontes",
            "regiao_id": regiao_id,
            "regiao_nome": None,
            "score": 0,
            "confianca": "nao_avaliada",
            "indicadores": {},
            "justificativa": (
                f"Região '{regiao_id}' não encontrada na base de dados. "
                f"IDs válidos: {ids_validos}."
            ),
            "riscos": [],
            "limitacoes": ["Região não encontrada na base simulada."],
            "simulado": True,
            "erro": resultado["erro"],
        }

    dados = resultado["dados"]
    publicos = dados["parceiros_publicos_possiveis"]
    privados = dados["parceiros_privados_possiveis"]
    total = len(publicos) + len(privados)

    scores = _calcular_score_pontes(dados)
    confianca = _calcular_confianca(dados)
    maturidade = dados["maturidade_parcerias"]
    economia_pct = dados["percentual_economia_potencial_pct"]
    infra = dados["infraestrutura_compartilhavel"]

    justificativa = (
        f"A região {resultado['nome']} possui {total} possíveis parceiros "
        f"({len(publicos)} públicos, {len(privados)} privados), "
        f"maturidade de parcerias '{maturidade}' e potencial de economia de "
        f"{economia_pct}%. Infraestrutura compartilhável: {'sim' if infra else 'não'}. "
        f"Score calculado: {scores['score_final']}/100."
    )

    riscos = [
        "Parcerias são hipotéticas — confirmação real exige negociação formal",
        "Maturidade das parcerias pode não se converter em acordos concretos",
    ]
    if not infra:
        riscos.append("Ausência de infraestrutura compartilhável eleva custo de implantação")
    if maturidade == "baixa":
        riscos.append("Baixa maturidade de parcerias aumenta risco de insucesso nas negociações")

    return {
        "agente": "pontes",
        "regiao_id": resultado["id"],
        "regiao_nome": resultado["nome"],
        "score": scores["score_final"],
        "confianca": confianca,
        "indicadores": {
            "quantidade_instituicoes_ancora": dados["quantidade_instituicoes_ancora"],
            "total_parceiros_possiveis": total,
            "parceiros_publicos_possiveis": publicos,
            "parceiros_privados_possiveis": privados,
            "infraestrutura_compartilhavel": infra,
            "oportunidades_reducao_custos": dados["oportunidades_reducao_custos"],
            "percentual_economia_potencial_pct": economia_pct,
            "maturidade_parcerias": maturidade,
            "score_quantidade_parceiros": scores["score_quantidade_parceiros"],
            "score_infraestrutura": scores["score_infraestrutura"],
            "score_economia_potencial": scores["score_economia_potencial"],
            "score_maturidade": scores["score_maturidade"],
        },
        "justificativa": justificativa,
        "riscos": riscos,
        "limitacoes": [_AVISO_SIMULADO, _AVISO_HIPOTETICO],
        "simulado": True,
        "erro": None,
    }


if __name__ == "__main__":
    regiao = sys.argv[1] if len(sys.argv) > 1 else "vale_verde"
    resultado = analisar_pontes(regiao)
    dados = resultado.content if hasattr(resultado, "content") else resultado
    print(json.dumps(dados, ensure_ascii=False, indent=2))
