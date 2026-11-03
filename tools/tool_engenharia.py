"""
Ferramenta de análise de engenharia para o Conecta Conselho.
Agente: Engenharia
Integrante: Laura

Analisa a viabilidade técnica de implantação de infraestrutura de conectividade
em regiões fictícias, calculando um score de 0 a 100 de forma determinística.
Todos os dados são SIMULADOS.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Adiciona o diretório pai ao path para importar ferramentas compartilhadas
sys.path.insert(0, str(Path(__file__).parent.parent / "conecta-conselho"))

from tools.consultar_regiao import consultar_engenharia

from ibm_watsonx_orchestrate.agent_builder.tools import tool


# ---------------------------------------------------------------------------
# Lógica pura — testável sem o ADK
# ---------------------------------------------------------------------------

_CAMPOS_SCORE = {
    "distancia_backbone_km",
    "percentual_cobertura_fibra",
    "prazo_implantacao_meses",
    "indice_viabilidade_tecnica",
}

_CAMPOS_OBRIGATORIOS = {
    "tipo_infraestrutura_disponivel",
    "distancia_backbone_km",
    "percentual_cobertura_fibra",
    "capacidade_infraestrutura_existente",
    "dificuldades_tecnicas",
    "prazo_implantacao_meses",
    "tecnologias_viaveis",
    "indice_viabilidade_tecnica",
}


def calcular_score_engenharia(dados: dict) -> dict:
    """
    Calcula os sub-scores e o score final de engenharia de 0 a 100.

    Sub-scores (todos de 0 a 100):
      - score_backbone (peso 25%):
          Penaliza distância do backbone. 0 km → 100; 100+ km → 0.
          formula: min(100, max(0, 100 - distancia_backbone_km))

      - score_cobertura_fibra (peso 25%):
          = percentual_cobertura_fibra  (já em 0-100)

      - score_prazo (peso 20%):
          Penaliza prazos longos. 6 meses → 100; 36+ meses → 0.
          formula: min(100, max(0, 100 - ((prazo_meses - 6) / 30) * 100))

      - score_base_viabilidade (peso 30%):
          = indice_viabilidade_tecnica  (dado da base, NÃO recalculado)

    Score final = round(0.25*backbone + 0.25*fibra + 0.20*prazo + 0.30*viabilidade)

    Args:
        dados: Dicionário com os campos da seção engenharia da base.
    Returns:
        Dicionário com os quatro sub-scores e o score final (inteiro 0-100).
    """
    distancia = dados["distancia_backbone_km"]
    fibra = dados["percentual_cobertura_fibra"]
    prazo = dados["prazo_implantacao_meses"]
    viabilidade = dados["indice_viabilidade_tecnica"]

    score_backbone = min(100, max(0, 100 - distancia))
    score_cobertura_fibra = min(100, max(0, fibra))
    score_prazo = min(100, max(0, 100 - ((prazo - 6) / 30) * 100))
    score_base_viabilidade = min(100, max(0, viabilidade))

    score_final = round(
        0.25 * score_backbone
        + 0.25 * score_cobertura_fibra
        + 0.20 * score_prazo
        + 0.30 * score_base_viabilidade
    )

    return {
        "score_backbone": round(score_backbone),
        "score_cobertura_fibra": round(score_cobertura_fibra),
        "score_prazo": round(score_prazo),
        "score_base_viabilidade": round(score_base_viabilidade),
        "score_final": score_final,
    }


def calcular_confianca(dados: dict) -> str:
    """
    Determina o nível de confiança com base na completude dos dados.

    Regras (Seção 3.3 do padrão):
      alta       = todos os 8 campos obrigatórios presentes e válidos
      media      = pelo menos 6 de 8 campos presentes e nenhum campo crítico ausente
      baixa      = menos de 6 campos presentes ou campo crítico ausente
      nao_avaliada = usado apenas em caso de erro (não aqui)

    Args:
        dados: Dicionário com os campos da seção engenharia da base.
    Returns:
        String "alta", "media" ou "baixa".
    """
    presentes = sum(
        1 for campo in _CAMPOS_OBRIGATORIOS
        if campo in dados and dados[campo] is not None
    )
    criticos_ausentes = any(
        campo not in dados or dados[campo] is None
        for campo in _CAMPOS_SCORE
    )

    if presentes == 8 and not criticos_ausentes:
        return "alta"
    if presentes >= 6 and not criticos_ausentes:
        return "media"
    return "baixa"


def _montar_justificativa(dados: dict, scores: dict) -> str:
    """Monta a justificativa em português citando os números que mais pesaram."""
    tecnologias = dados.get("tecnologias_viaveis", [])
    tech_principal = tecnologias[0] if tecnologias else "tecnologia não especificada"

    distancia = dados["distancia_backbone_km"]
    fibra = dados["percentual_cobertura_fibra"]
    prazo = dados["prazo_implantacao_meses"]
    viabilidade = dados["indice_viabilidade_tecnica"]
    score = scores["score_final"]

    return (
        f"Score de viabilidade técnica: {score}/100. "
        f"Distância do backbone: {distancia} km (score {scores['score_backbone']}/100); "
        f"cobertura de fibra atual: {fibra}% (score {scores['score_cobertura_fibra']}/100); "
        f"prazo estimado de implantação: {prazo} meses (score {scores['score_prazo']}/100); "
        f"índice de viabilidade da base: {viabilidade}/100 (score {scores['score_base_viabilidade']}/100). "
        f"Tecnologia mais adequada indicada: {tech_principal}. "
        f"Todos os dados são simulados."
    )


def _montar_riscos(dados: dict, scores: dict) -> list:
    """Deriva lista de riscos a partir das dificuldades técnicas e sub-scores baixos."""
    riscos = list(dados.get("dificuldades_tecnicas", []))

    if scores["score_backbone"] < 50:
        riscos.append(
            f"Distância elevada do backbone ({dados['distancia_backbone_km']} km) "
            "encarece significativamente o backhaul."
        )
    if scores["score_cobertura_fibra"] < 30:
        riscos.append(
            "Baixa cobertura de fibra existente exige implantação extensiva do zero."
        )
    if scores["score_prazo"] < 50:
        riscos.append(
            f"Prazo de implantação longo ({dados['prazo_implantacao_meses']} meses) "
            "aumenta exposição a riscos de execução e obsolescência."
        )

    # Garante lista não vazia
    if not riscos:
        riscos.append("Monitorar capacidade da infraestrutura existente conforme expansão.")

    return riscos


def montar_parecer(regiao_id: str) -> dict:
    """
    Monta o parecer completo do Agente Engenharia para uma região.

    Args:
        regiao_id: Identificador da região (ex: "central").
    Returns:
        Dicionário com o parecer estruturado conforme o contrato do projeto.
    """
    print(f"[INFO][agente_engenharia] Consultando região: {regiao_id}")

    resultado = consultar_engenharia(regiao_id)

    if "erro" in resultado:
        print(
            f"[ERRO][agente_engenharia] Região não encontrada: {regiao_id}",
            file=sys.stderr,
        )
        return {
            "agente": "engenharia",
            "regiao_id": regiao_id,
            "regiao_nome": None,
            "score": 0,
            "confianca": "nao_avaliada",
            "indicadores": {},
            "justificativa": (
                f"Região '{regiao_id}' não encontrada na base de dados. "
                "IDs válidos: aurora, horizonte, esperanca, central, vale_verde, nova_uniao."
            ),
            "riscos": [],
            "limitacoes": ["Região não encontrada na base simulada."],
            "simulado": True,
            "erro": resultado["mensagem"],
        }

    dados = resultado["dados"]
    nome = resultado["nome"]

    scores = calcular_score_engenharia(dados)
    confianca = calcular_confianca(dados)
    justificativa = _montar_justificativa(dados, scores)
    riscos = _montar_riscos(dados, scores)

    indicadores = {
        "tipo_infraestrutura_disponivel":     dados["tipo_infraestrutura_disponivel"],
        "distancia_backbone_km":              dados["distancia_backbone_km"],
        "percentual_cobertura_fibra":         dados["percentual_cobertura_fibra"],
        "capacidade_infraestrutura_existente": dados["capacidade_infraestrutura_existente"],
        "dificuldades_tecnicas":              dados["dificuldades_tecnicas"],
        "prazo_implantacao_meses":            dados["prazo_implantacao_meses"],
        "tecnologias_viaveis":               dados["tecnologias_viaveis"],
        "indice_viabilidade_tecnica":         dados["indice_viabilidade_tecnica"],
        "score_backbone":                     scores["score_backbone"],
        "score_cobertura_fibra":              scores["score_cobertura_fibra"],
        "score_prazo":                        scores["score_prazo"],
        "score_base_viabilidade":             scores["score_base_viabilidade"],
    }

    return {
        "agente": "engenharia",
        "regiao_id": regiao_id,
        "regiao_nome": nome,
        "score": scores["score_final"],
        "confianca": confianca,
        "indicadores": indicadores,
        "justificativa": justificativa,
        "riscos": riscos,
        "limitacoes": [
            "Dado simulado — não reflete condições reais",
            "Índice de viabilidade técnica é estimativa simulada",
        ],
        "simulado": True,
        "erro": None,
    }


# ---------------------------------------------------------------------------
# Ferramenta ADK — wrapper fino sobre montar_parecer
# ---------------------------------------------------------------------------


@tool
def analisar_engenharia(regiao_id: str) -> dict:
    """
    Analisa a viabilidade técnica de infraestrutura de conectividade de uma região.

    Consulta os indicadores de engenharia da base simulada do Conecta Conselho e
    calcula um score de viabilidade técnica de 0 a 100 usando fórmulas determinísticas.
    Deve ser chamada SEMPRE que o usuário perguntar sobre engenharia, infraestrutura,
    viabilidade técnica ou prazo de implantação de uma região.

    Args:
        regiao_id: Identificador da região. Valores válidos:
                   aurora, horizonte, esperanca, central, vale_verde, nova_uniao
    Returns:
        Parecer estruturado com score (0-100), sub-scores de backbone, cobertura de
        fibra, prazo e viabilidade de base, justificativa em português, riscos técnicos
        identificados e limitações dos dados simulados.
    """
    return montar_parecer(regiao_id)


# ---------------------------------------------------------------------------
# Execução direta — imprime pareceres das 6 regiões + inexistente
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    regioes = ["central", "aurora", "vale_verde", "horizonte", "esperanca", "nova_uniao", "inexistente"]

    for rid in regioes:
        parecer = montar_parecer(rid)
        print(f"\n{'='*60}")
        print(f"Região: {rid}  |  Score: {parecer['score']}  |  Confiança: {parecer['confianca']}")
        print(json.dumps(parecer, ensure_ascii=False, indent=2))
