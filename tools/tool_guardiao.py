"""
Ferramenta Python do Agente Guardiao — Conecta Conselho.

Consolida os cinco pareceres especialistas (mercado, impacto_social,
engenharia, orcamento, pontes) e produz uma recomendacao final fundamentada.

Agente: Agente Guardiao (cc_guardiao)

AVISO: Todos os dados retornados sao SIMULADOS e ficticios.

Portabilidade do decorador @tool:
  O import do ADK usa try/except com fallback transparente (identidade).
  Isso permite importar e testar este modulo sem o venv do ADK ativo.

IMPORTANTE: Este arquivo e autocontido. Nao importa consultar_regiao nem
outras tools. O runtime da nuvem nao acessa outros arquivos do repositorio.
"""

from __future__ import annotations

import json
import math

try:
    from ibm_watsonx_orchestrate.agent_builder.tools import tool as tool  # noqa: PLC0414
    _ADK_DISPONIVEL = True
except ImportError:  # pragma: no cover
    def tool(func):  # type: ignore[misc]
        """Fallback: sem ADK disponivel, @tool e uma identidade."""
        return func
    _ADK_DISPONIVEL = False


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# Ordem fixa garante soma deterministica (set nao tem ordem garantida)
_AGENTES_VALIDOS = ("mercado", "impacto_social", "engenharia", "orcamento", "pontes")
_PESOS = {
    "mercado":        0.20,
    "impacto_social": 0.20,
    "engenharia":     0.25,
    "orcamento":      0.25,
    "pontes":         0.10,
}
_LIMITACAO_OBRIGATORIA = (
    "Recomendacao baseada em dados simulados e pesos hipoteticos definidos para o MVP."
)


# ---------------------------------------------------------------------------
# Normalizacao de pareceres — prova de erro para entradas malformadas
# ---------------------------------------------------------------------------


def _normalizar_parecer(agente: str, p) -> dict:
    """
    Normaliza e valida um parecer individual antes de qualquer calculo.

    Garante que a tool nunca lanca excecao por entrada malformada do LLM:
      - p nao e dict              -> parecer de erro com score 0
      - score ausente/None/bool   -> score 0, erro explicativo
      - score texto numerico "72" -> converte para int
      - score float               -> round para int
      - score fora de 0-100       -> score 0, erro explicativo
      - confianca ausente/nao-str -> "nao_avaliada"
      - riscos nao-lista          -> []
      - demais campos preservados
    """
    # p nao e dict: retorna parecer de erro completo
    if not isinstance(p, dict):
        return {
            "score": 0,
            "confianca": "nao_avaliada",
            "justificativa": "",
            "riscos": [],
            "erro": f"Parecer do agente '{agente}' em formato invalido.",
        }

    resultado = dict(p)  # copia rasa para nao mutar o original
    erro_score: str | None = None

    score_raw = resultado.get("score")

    # bool e subclasse de int em Python — tratar antes de int
    if isinstance(score_raw, bool):
        erro_score = f"Score do agente '{agente}' e booleano; esperado inteiro 0-100."
        score_raw = None

    if score_raw is None:
        if erro_score is None:
            erro_score = f"Score do agente '{agente}' ausente ou nulo."
        resultado["score"] = 0
        resultado["erro"] = resultado.get("erro") or erro_score
    elif isinstance(score_raw, float):
        if not math.isfinite(score_raw):
            resultado["score"] = 0
            resultado["erro"] = (
                resultado.get("erro")
                or f"Score do agente '{agente}' nao e um numero finito."
            )
        else:
            score_int = round(score_raw)
            if 0 <= score_int <= 100:
                resultado["score"] = score_int
            else:
                resultado["score"] = 0
                resultado["erro"] = (
                    resultado.get("erro")
                    or f"Score do agente '{agente}' fora do intervalo 0-100: {score_raw}."
                )
    elif isinstance(score_raw, int):
        if 0 <= score_raw <= 100:
            resultado["score"] = score_raw
        else:
            resultado["score"] = 0
            resultado["erro"] = (
                resultado.get("erro")
                or f"Score do agente '{agente}' fora do intervalo 0-100: {score_raw}."
            )
    elif isinstance(score_raw, str):
        try:
            score_float = float(score_raw)
            if not math.isfinite(score_float):
                resultado["score"] = 0
                resultado["erro"] = (
                    resultado.get("erro")
                    or f"Score do agente '{agente}' nao e um numero finito."
                )
            else:
                score_conv = int(score_float)
                if 0 <= score_conv <= 100:
                    resultado["score"] = score_conv
                else:
                    resultado["score"] = 0
                    resultado["erro"] = (
                        resultado.get("erro")
                        or f"Score do agente '{agente}' fora do intervalo 0-100: {score_raw}."
                    )
        except (ValueError, TypeError):
            resultado["score"] = 0
            resultado["erro"] = (
                resultado.get("erro")
                or f"Score do agente '{agente}' nao e numerico: '{score_raw}'."
            )
    else:
        resultado["score"] = 0
        resultado["erro"] = (
            resultado.get("erro")
            or f"Score do agente '{agente}' em tipo invalido: {type(score_raw).__name__}."
        )

    # confianca deve ser string
    confianca = resultado.get("confianca")
    if not isinstance(confianca, str):
        resultado["confianca"] = "nao_avaliada"

    # riscos deve ser lista; cada item normalizado para string
    riscos_raw = resultado.get("riscos")
    if not isinstance(riscos_raw, list):
        resultado["riscos"] = []
    else:
        riscos_norm: list[str] = []
        for item in riscos_raw:
            if item is None:
                continue
            if isinstance(item, str):
                riscos_norm.append(item)
            elif isinstance(item, dict):
                # Pega o primeiro valor de texto do dict, ou json.dumps como fallback
                texto = next(
                    (str(v) for v in item.values() if v is not None and str(v)),
                    json.dumps(item, ensure_ascii=False),
                )
                riscos_norm.append(texto)
            else:
                riscos_norm.append(str(item))
        resultado["riscos"] = riscos_norm

    return resultado


# ---------------------------------------------------------------------------
# Calculos deterministicos
# ---------------------------------------------------------------------------


def _calcular_score_consolidado(pareceres: dict) -> int:
    """Média ponderada dos cinco scores. Resultado arredondado para inteiro.
    Itera na ordem fixa de _AGENTES_VALIDOS para resultado determinístico."""
    total = sum(
        _PESOS[agente] * float(pareceres[agente]["score"])
        for agente in _AGENTES_VALIDOS
    )
    return round(total)


def _determinar_recomendacao(score: int, pareceres: dict) -> str:
    """
    Criterios objetivos (nao e julgamento do LLM):

    Regra extra aprovada pelo grupo:
      "escalar" se score < 30 OU engenharia < 20 OU orcamento < 20
                OU qualquer parecer com erro != null OU confianca == "baixa"

    Hierarquia:
      investir_agora : score >= 70 E orcamento >= 60 E engenharia >= 60
      realizar_piloto: score >= 50 (e nao investir_agora)
      aguardar       : score >= 30 e < 50
      escalar        : demais casos (incluindo regra extra do grupo)
    """
    eng_score = int(pareceres["engenharia"]["score"])
    orc_score = int(pareceres["orcamento"]["score"])

    # Regra extra do grupo: escalar forcado
    if score < 30 or eng_score < 20 or orc_score < 20:
        return "escalar"
    for p in pareceres.values():
        if p.get("erro") is not None or p.get("confianca") == "baixa":
            return "escalar"

    # Hierarquia normal
    if score >= 70 and orc_score >= 60 and eng_score >= 60:
        return "investir_agora"
    if score >= 50:
        return "realizar_piloto"
    if score >= 30:
        return "aguardar"
    return "escalar"  # fallback (ja coberto acima, mas por seguranca)


def _identificar_divergencias(pareceres: dict) -> list[str]:
    """
    Tres regras da Secao 11 + registro de pareceres com erro.
    """
    divergencias: list[str] = []

    s_social = int(pareceres["impacto_social"]["score"])
    s_orc    = int(pareceres["orcamento"]["score"])
    s_eng    = int(pareceres["engenharia"]["score"])
    s_merc   = int(pareceres["mercado"]["score"])
    s_pont   = int(pareceres["pontes"]["score"])

    # Regra 1: alto impacto social vs baixa viabilidade financeira
    if abs(s_social - s_orc) > 30:
        maior, menor = ("impacto_social", "orcamento") if s_social > s_orc else ("orcamento", "impacto_social")
        divergencias.append(
            f"Alto {maior.replace('_',' ')} (score {max(s_social,s_orc)}) "
            f"contrastado com baixo {menor.replace('_',' ')} (score {min(s_social,s_orc)}). "
            f"Parcerias e subsidios podem ser necessarios para viabilizacao."
        )

    # Regra 2: boa demanda mas viabilidade tecnica baixa
    if s_eng < 40 and s_merc > 60:
        divergencias.append(
            f"Boa demanda de mercado (score {s_merc}) mas viabilidade tecnica "
            f"insuficiente (engenharia score {s_eng}). "
            f"Expansao tecnica necessaria antes do investimento."
        )

    # Regra 3: parcerias fortes mas orcamento fraco
    if s_pont > 70 and s_orc < 40:
        divergencias.append(
            f"Forte potencial de parcerias (score {s_pont}) pode viabilizar "
            f"o que o orcamento nao consegue sozinho (score {s_orc}). "
            f"Estrategia de cofinanciamento recomendada."
        )

    # Registro de pareceres com erro
    for agente, p in pareceres.items():
        if p.get("erro") is not None:
            divergencias.append(
                f"Parecer do agente '{agente}' retornou erro: {p['erro']}. "
                f"Score utilizado: {p.get('score', 0)}."
            )

    return divergencias


def _extrair_pareceres_resumo(pareceres_completos: dict) -> dict:
    """Extrai apenas score, confianca e justificativa de cada parecer."""
    return {
        agente: {
            "score":        p.get("score", 0),
            "confianca":    p.get("confianca", "nao_avaliada"),
            "justificativa": p.get("justificativa", ""),
            "erro":         p.get("erro"),
        }
        for agente, p in pareceres_completos.items()
    }


def _consolidar_riscos(pareceres_completos: dict) -> list[str]:
    """Une os riscos de todos os pareceres, removendo duplicatas, max 10."""
    vistos: set[str] = set()
    riscos: list[str] = []
    for p in pareceres_completos.values():
        for risco in p.get("riscos", []):
            if risco not in vistos:
                vistos.add(risco)
                riscos.append(risco)
    return riscos[:10]


def _consolidar_oportunidades(pareceres_completos: dict, recomendacao: str) -> list[str]:
    """Oportunidades derivadas dos pareceres com scores mais altos."""
    oportunidades: list[str] = []
    for agente, p in pareceres_completos.items():
        score = p.get("score", 0)
        if score >= 60:
            oportunidades.append(
                f"Perspectiva de {agente.replace('_',' ')} com score {score} indica potencial relevante."
            )
    if not oportunidades:
        oportunidades.append("Nenhuma perspectiva com score alto identificada no momento.")
    return oportunidades


def _construir_justificativa(pareceres_resumo: dict, score: int, recomendacao: str) -> str:
    """Justificativa consolidada em texto, minimo 100 caracteres."""
    linhas = [
        f"Score consolidado: {score}/100. Recomendacao: {recomendacao.replace('_',' ').upper()}.",
        "Perspectivas analisadas:",
    ]
    for agente, p in pareceres_resumo.items():
        linhas.append(
            f"  - {agente.replace('_',' ').capitalize()}: score {p['score']} "
            f"(confianca {p['confianca']})."
        )
    return " ".join(linhas)


# ---------------------------------------------------------------------------
# Ferramenta principal
# ---------------------------------------------------------------------------


@tool
def consolidar_pareceres(pareceres_json: str) -> dict:
    """
    Consolida os cinco pareceres especialistas do sistema Conecta Conselho
    e produz uma recomendacao final fundamentada.

    Recebe um JSON com os pareceres dos agentes mercado, impacto_social,
    engenharia, orcamento e pontes, e retorna o parecer consolidado do
    Agente Guardiao com score ponderado, recomendacao, divergencias e riscos.

    Args:
        pareceres_json: String JSON contendo um objeto com os cinco pareceres
            especialistas. Cada parecer deve ter pelo menos os campos:
            'score' (int), 'confianca' (str), 'justificativa' (str),
            'riscos' (list), 'erro' (str|null).
            Exemplo: '{"mercado": {...}, "impacto_social": {...}, ...}'

    Returns:
        Dicionario com o parecer consolidado do Guardiao incluindo
        score_consolidado, recomendacao, pareceres resumidos, divergencias,
        justificativa_consolidada, principais_riscos e oportunidades.
    """
    resultado_base: dict = {
        "agente": "guardiao",
        "regiao_id": "",
        "regiao_nome": "",
        "recomendacao": "escalar",
        "score_consolidado": 0,
        "pareceres": {},
        "divergencias": [],
        "justificativa_consolidada": "",
        "principais_riscos": [],
        "principais_oportunidades": [],
        "limitacoes": [_LIMITACAO_OBRIGATORIA],
        "simulado": True,
        "erro": None,
    }

    # --- Pre-processamento: extrai JSON de blocos markdown ou texto com prefixo ---
    if isinstance(pareceres_json, str):
        s = pareceres_json.strip()
        # Remove bloco de codigo markdown: ```json ... ``` ou ``` ... ```
        if s.startswith("```"):
            linhas = s.splitlines()
            # Remove primeira linha (```json ou ```) e ultima linha (```)
            linhas = linhas[1:]
            if linhas and linhas[-1].strip() == "```":
                linhas = linhas[:-1]
            s = "\n".join(linhas).strip()
        # Se ainda nao comecar com "{", tenta encontrar primeiro "{" e ultimo "}"
        if not s.startswith("{"):
            inicio = s.find("{")
            fim = s.rfind("}")
            if inicio != -1 and fim != -1 and fim > inicio:
                s = s[inicio:fim + 1]
        pareceres_json = s

    # --- Parse do JSON de entrada ---
    try:
        pareceres_completos: dict = json.loads(pareceres_json)
    except (json.JSONDecodeError, TypeError) as exc:
        resultado_base["erro"] = f"JSON invalido: {exc}"
        resultado_base["justificativa_consolidada"] = (
            "Nao foi possivel processar os pareceres: entrada JSON invalida."
        )
        return resultado_base

    if not isinstance(pareceres_completos, dict):
        resultado_base["erro"] = "pareceres_json deve ser um objeto JSON com os cinco pareceres."
        resultado_base["justificativa_consolidada"] = (
            "Entrada invalida: esperado objeto JSON com chaves dos cinco agentes."
        )
        return resultado_base

    # --- Filtra apenas as 5 chaves dos agentes; ignora chaves extras (ex: "regiao_id") ---
    pareceres_agentes: dict = {}
    for agente in _AGENTES_VALIDOS:
        p_raw = pareceres_completos.get(agente)
        if p_raw is None:
            # Agente ausente: cria parecer de erro
            pareceres_agentes[agente] = {
                "score": 0,
                "confianca": "nao_avaliada",
                "justificativa": f"Parecer do agente '{agente}' nao fornecido.",
                "riscos": [],
                "erro": f"Parecer ausente para o agente '{agente}'.",
            }
        else:
            pareceres_agentes[agente] = _normalizar_parecer(agente, p_raw)

    pareceres_completos = pareceres_agentes

    # --- Extrai regiao_id e regiao_nome do primeiro parecer valido ---
    for p in pareceres_completos.values():
        if isinstance(p, dict) and p.get("regiao_id"):
            resultado_base["regiao_id"]   = p["regiao_id"]
            resultado_base["regiao_nome"] = p.get("regiao_nome", "")
            break

    # --- Calculos deterministicos ---
    score           = _calcular_score_consolidado(pareceres_completos)
    recomendacao    = _determinar_recomendacao(score, pareceres_completos)
    divergencias    = _identificar_divergencias(pareceres_completos)
    pareceres_res   = _extrair_pareceres_resumo(pareceres_completos)
    riscos          = _consolidar_riscos(pareceres_completos)
    oportunidades   = _consolidar_oportunidades(pareceres_completos, recomendacao)
    justificativa   = _construir_justificativa(pareceres_res, score, recomendacao)

    resultado_base.update({
        "recomendacao":             recomendacao,
        "score_consolidado":        score,
        "pareceres":                pareceres_res,
        "divergencias":             divergencias,
        "justificativa_consolidada": justificativa,
        "principais_riscos":        riscos,
        "principais_oportunidades": oportunidades,
    })
    return resultado_base
