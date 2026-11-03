"""
Ferramenta Python do Agente Guardiao — Conecta Conselho.

Consolida os cinco pareceres especialistas (mercado, impacto_social,
engenharia, orcamento, pontes) e produz uma recomendacao final fundamentada.

Agente: Agente Guardiao (cc_guardiao)

AVISO: Todos os dados retornados sao SIMULADOS e ficticios.

Requer o ADK instalado (ver requirements.txt). Import direto do @tool:
o runtime da nuvem nao aceita try/except em volta dele.

IMPORTANTE: Este arquivo e autocontido. Nao importa consultar_regiao nem
outras tools. O runtime da nuvem nao acessa outros arquivos do repositorio.
"""

from __future__ import annotations

import json
import math

from ibm_watsonx_orchestrate.agent_builder.tools import tool


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
      - score NaN/Infinity        -> score 0, erro explicativo
      - score fora de 0-100       -> score 0, erro explicativo
      - confianca ausente/nao-str -> "nao_avaliada"
      - riscos nao-lista          -> []; items dict -> primeiro valor de texto
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
    """Media ponderada dos cinco scores. Resultado arredondado para inteiro.
    Itera na ordem fixa de _AGENTES_VALIDOS para resultado deterministico."""
    total = sum(
        _PESOS[agente] * float(pareceres[agente]["score"])
        for agente in _AGENTES_VALIDOS
    )
    return round(total)


def _determinar_recomendacao(score: int, pareceres: dict) -> str:
    """
    Criterios objetivos — sem 'escalar'. A decisao final e sempre humana.

    Hierarquia:
      investir_agora : score >= 70 E orcamento >= 60 E engenharia >= 60
      realizar_piloto: score >= 50 (e nao investir_agora)
      aguardar       : score < 50
    """
    eng_score = int(pareceres["engenharia"]["score"])
    orc_score = int(pareceres["orcamento"]["score"])

    if score >= 70 and orc_score >= 60 and eng_score >= 60:
        return "investir_agora"
    if score >= 50:
        return "realizar_piloto"
    return "aguardar"


def _fmt_brl(valor: float) -> str:
    """Formata valor monetario em reais no padrao brasileiro: R$ 9.000.000 ou R$ 81.288,16."""
    negativo = valor < 0
    abs_val = abs(valor)
    if round(abs_val % 1, 6) != 0:
        # tem centavos
        int_fmt = f"{int(abs_val):,}".replace(",", ".")
        centavos = round((abs_val - int(abs_val)) * 100)
        result = f"R$ {int_fmt},{centavos:02d}"
    else:
        int_fmt = f"{int(abs_val):,}".replace(",", ".")
        result = f"R$ {int_fmt}"
    return f"R$ -{result[3:]}" if negativo else result


def _fmt_pct(valor: float) -> str:
    """Formata percentual no padrao brasileiro: 57,5%."""
    s = f"{valor:.1f}".replace(".", ",")
    return f"{s}%"


def _calcular_atencao_prioritaria(score: int, pareceres: dict) -> tuple[bool, list[str]]:
    """
    Retorna (atencao_prioritaria: bool, pontos_criticos: list[str]).
    Condicoes (independentes da recomendacao):
      - engenharia < 20
      - orcamento < 20
      - score_consolidado < 30
      - qualquer parecer com confianca "baixa"
    Frases montadas a partir dos indicadores do parecer, nao da justificativa.
    """
    pontos: list[str] = []

    eng_score = int(pareceres["engenharia"]["score"])
    orc_score = int(pareceres["orcamento"]["score"])

    if orc_score < 20:
        ind_orc = pareceres["orcamento"].get("indicadores") or {}
        margem = ind_orc.get("margem_mensal_reais")
        cobertura = ind_orc.get("cobertura_orcamentaria_pct")
        deficit = ind_orc.get("deficit_orcamentario_reais")
        partes = []
        if isinstance(margem, (int, float)):
            partes.append(f"margem mensal de {_fmt_brl(margem)}")
        if isinstance(cobertura, (int, float)):
            partes.append(f"cobertura orçamentária de {_fmt_pct(cobertura)}")
        if isinstance(deficit, (int, float)) and deficit > 0:
            partes.append(f"déficit de {_fmt_brl(deficit)}")
        detalhe = "; ".join(partes) if partes else "verificar indicadores financeiros"
        pontos.append(
            f"Orçamento com score {orc_score}: {detalhe}."
        )

    if eng_score < 20:
        ind_eng = pareceres["engenharia"].get("indicadores") or {}
        dist = ind_eng.get("distancia_backbone_km")
        cobertura_fibra = ind_eng.get("percentual_cobertura_fibra")
        prazo = ind_eng.get("prazo_implantacao_meses")
        partes = []
        if isinstance(dist, (int, float)):
            partes.append(f"backbone a {int(dist)} km")
        if isinstance(cobertura_fibra, (int, float)):
            partes.append(f"{int(cobertura_fibra)}% de cobertura de fibra")
        if isinstance(prazo, (int, float)):
            partes.append(f"prazo de implantação de {int(prazo)} meses")
        detalhe = "; ".join(partes) if partes else "verificar indicadores técnicos"
        pontos.append(
            f"Engenharia com score {eng_score}: {detalhe}."
        )

    if score < 30:
        pontos.append(
            f"Score consolidado {score} abaixo de 30: viabilidade geral muito baixa."
        )

    for agente, p in pareceres.items():
        if p.get("confianca") == "baixa":
            nome = agente.replace("_", " ").capitalize()
            pontos.append(
                f"Confiança baixa no parecer de {nome}."
            )

    return (len(pontos) > 0, pontos)


def _calcular_motivos_e_caminhos(pareceres: dict) -> tuple[list[str], list[str]]:
    """
    Retorna (motivos, caminhos) — preenchidos APENAS quando recomendacao == 'aguardar'.
    Motivos: uma frase por agente com score < 50, construida a partir dos indicadores.
    Caminhos: extraidos de campos reais dos pareceres (sem inventar).
    """
    motivos: list[str] = []
    caminhos: list[str] = []

    ind_eng  = pareceres["engenharia"].get("indicadores") or {}
    ind_pont = pareceres["pontes"].get("indicadores") or {}
    ind_orc  = pareceres["orcamento"].get("indicadores") or {}
    ind_merc = pareceres["mercado"].get("indicadores") or {}
    ind_soc  = pareceres["impacto_social"].get("indicadores") or {}

    # Motivos: agentes com score < 50, frases construidas dos indicadores
    for agente in _AGENTES_VALIDOS:
        p = pareceres[agente]
        sc = int(p.get("score", 0))
        if sc >= 50:
            continue

        if agente == "engenharia":
            dist = ind_eng.get("distancia_backbone_km")
            cob  = ind_eng.get("percentual_cobertura_fibra")
            prazo = ind_eng.get("prazo_implantacao_meses")
            partes = []
            if isinstance(dist, (int, float)):
                partes.append(f"backbone a {int(dist)} km")
            if isinstance(cob, (int, float)):
                partes.append(f"{int(cob)}% de cobertura de fibra")
            if isinstance(prazo, (int, float)):
                partes.append(f"prazo de {int(prazo)} meses")
            detalhe = "; ".join(partes) if partes else f"score {sc} abaixo do limiar de viabilidade"
            motivos.append(f"Engenharia (score {sc}): {detalhe}.")

        elif agente == "orcamento":
            cob_orc = ind_orc.get("cobertura_orcamentaria_pct")
            deficit = ind_orc.get("deficit_orcamentario_reais")
            payback = ind_orc.get("payback_meses")
            margem  = ind_orc.get("margem_mensal_reais")
            partes = []
            if isinstance(cob_orc, (int, float)):
                cob_str = _fmt_pct(cob_orc)
                if isinstance(deficit, (int, float)) and deficit > 0:
                    partes.append(f"orçamento cobre {cob_str} do CAPEX (déficit de {_fmt_brl(deficit)})")
                else:
                    partes.append(f"orçamento cobre {cob_str} do CAPEX")
            if payback is None:
                partes.append("payback indefinido (margem negativa)")
            elif isinstance(payback, (int, float)):
                partes.append(f"payback de {int(payback)} meses")
            if isinstance(margem, (int, float)) and margem <= 0:
                partes.append(f"margem mensal negativa ({_fmt_brl(margem)})")
            detalhe = "; ".join(partes) if partes else f"score {sc} abaixo do limiar de viabilidade"
            motivos.append(f"Orçamento (score {sc}): {detalhe}.")

        elif agente == "pontes":
            total = ind_pont.get("total_parceiros_possiveis")
            matur = ind_pont.get("maturidade_parcerias")
            partes = []
            if isinstance(total, int):
                partes.append(f"{total} parceiros possíveis")
            if isinstance(matur, str):
                partes.append(f"maturidade de parcerias {matur}")
            detalhe = "; ".join(partes) if partes else f"score {sc} abaixo do limiar de viabilidade"
            motivos.append(f"Pontes (score {sc}): {detalhe}.")

        elif agente == "mercado":
            # usa indicadores se disponíveis, caso contrário descreve o score
            pop = ind_merc.get("populacao_alvo") or ind_merc.get("populacao")
            penetracao = ind_merc.get("taxa_penetracao_esperada_pct") or ind_merc.get("penetracao_esperada_pct")
            partes = []
            if isinstance(pop, (int, float)) and pop > 0:
                partes.append(f"população-alvo de {int(pop):,}".replace(",", "."))
            if isinstance(penetracao, (int, float)):
                partes.append(f"penetração esperada de {_fmt_pct(penetracao)}")
            detalhe = "; ".join(partes) if partes else f"score {sc} abaixo do limiar de viabilidade"
            motivos.append(f"Mercado (score {sc}): {detalhe}.")

        else:  # impacto_social
            pop_ben = ind_soc.get("populacao_beneficiada") or ind_soc.get("populacao_alvo")
            idh = ind_soc.get("idh") or ind_soc.get("indice_idh")
            partes = []
            if isinstance(pop_ben, (int, float)) and pop_ben > 0:
                partes.append(f"população beneficiada de {int(pop_ben):,}".replace(",", "."))
            if isinstance(idh, (int, float)):
                partes.append(f"IDH {idh:.3f}")
            detalhe = "; ".join(partes) if partes else f"score {sc} abaixo do limiar de viabilidade"
            motivos.append(f"Impacto social (score {sc}): {detalhe}.")

    # Caminhos: extraidos de campos existentes nos pareceres
    # Tecnologias viaveis (engenharia)
    tecnologias = ind_eng.get("tecnologias_viaveis")
    if tecnologias and isinstance(tecnologias, list) and tecnologias:
        lista = ", ".join(str(t) for t in tecnologias[:3])
        caminhos.append(f"Tecnologias alternativas viáveis: {lista}.")

    # Parcerias (pontes)
    oportunidades_red = ind_pont.get("oportunidades_reducao_custos")
    if oportunidades_red and isinstance(oportunidades_red, list) and oportunidades_red:
        caminhos.append(
            f"Oportunidades de redução de custos via parcerias: "
            f"{oportunidades_red[0]}."
        )
    infra_comp = ind_pont.get("infraestrutura_compartilhavel")
    if infra_comp is True:
        caminhos.append("Infraestrutura compartilhável identificada: pode reduzir CAPEX.")
    ancora = ind_pont.get("quantidade_instituicoes_ancora")
    if isinstance(ancora, int) and ancora > 0:
        pct = ind_pont.get("percentual_economia_potencial_pct")
        if isinstance(pct, (int, float)):
            caminhos.append(
                f"{ancora} instituições âncora identificadas com potencial de "
                f"economia de {_fmt_pct(pct)} nos custos."
            )

    # Orcamento em fases
    deficit = ind_orc.get("deficit_orcamentario_reais")
    cobertura = ind_orc.get("cobertura_orcamentaria_pct")
    if isinstance(cobertura, (int, float)) and cobertura > 0:
        if isinstance(deficit, (int, float)) and deficit > 0:
            caminhos.append(
                f"Implantação em fases: o orçamento cobre {_fmt_pct(cobertura)} do CAPEX "
                f"(déficit de {_fmt_brl(deficit)})."
            )
        else:
            caminhos.append(
                f"Implantação em fases: o orçamento cobre {_fmt_pct(cobertura)} do CAPEX."
            )

    return motivos, caminhos


def _identificar_divergencias(pareceres: dict) -> list[str]:
    """
    Tres regras da Secao 11 (D1 nos dois sentidos com abs) + pareceres com erro.
    D1 tem texto diferente conforme a direcao da divergencia.
    """
    divergencias: list[str] = []

    s_social = int(pareceres["impacto_social"]["score"])
    s_orc    = int(pareceres["orcamento"]["score"])
    s_eng    = int(pareceres["engenharia"]["score"])
    s_merc   = int(pareceres["mercado"]["score"])
    s_pont   = int(pareceres["pontes"]["score"])

    # D1: divergencia entre impacto social e orcamento (abs > 30)
    if abs(s_social - s_orc) > 30:
        if s_orc > s_social:
            # Direcao inversa: orcamento alto, impacto social baixo
            divergencias.append(
                f"Região financeiramente atrativa (orçamento {s_orc}), mas com baixo "
                f"impacto social (social {s_social}): avaliar contrapartidas sociais na expansão."
            )
        else:
            # Direcao original: impacto social alto, orcamento baixo
            divergencias.append(
                f"Alto impacto social (score {s_social}) contrastado com baixa "
                f"viabilidade financeira (orçamento {s_orc}). "
                f"Parcerias e subsídios podem ser necessários para viabilização."
            )

    # D2: boa demanda mas viabilidade tecnica baixa
    if s_eng < 40 and s_merc > 60:
        divergencias.append(
            f"Boa demanda de mercado (score {s_merc}) mas viabilidade tecnica "
            f"insuficiente (engenharia score {s_eng}). "
            f"Expansao tecnica necessaria antes do investimento."
        )

    # D3: parcerias fortes mas orcamento fraco
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
    """Extrai score, confianca, justificativa e erro de cada parecer."""
    return {
        agente: {
            "score":         p.get("score", 0),
            "confianca":     p.get("confianca", "nao_avaliada"),
            "justificativa": p.get("justificativa", ""),
            "erro":          p.get("erro"),
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
    engenharia, orcamento e pontes. Se qualquer parecer tiver erro ou estiver
    ausente, retorna status "analise_incompleta" com recomendacao null.
    Caso contrario, retorna status "concluida" com recomendacao deterministica
    (investir_agora | realizar_piloto | aguardar — sem "escalar").

    Args:
        pareceres_json: String JSON contendo um objeto com os cinco pareceres
            especialistas. Aceita JSON puro ou embrulhado em bloco markdown.
            Exemplo: '{"mercado": {...}, "impacto_social": {...}, ...}'

    Returns:
        Dicionario com status, score_consolidado, recomendacao, pareceres,
        divergencias, atencao_prioritaria, pontos_criticos, motivos, caminhos,
        justificativa_consolidada, principais_riscos e limitacoes.
    """
    resultado_base: dict = {
        "agente": "guardiao",
        "regiao_id": "",
        "regiao_nome": "",
        "status": "concluida",
        "recomendacao": None,
        "score_consolidado": None,
        "pareceres": {},
        "divergencias": [],
        "atencao_prioritaria": False,
        "pontos_criticos": [],
        "motivos": [],
        "caminhos": [],
        "justificativa_consolidada": "",
        "principais_riscos": [],
        "limitacoes": [_LIMITACAO_OBRIGATORIA],
        "simulado": True,
        "erro": None,
    }

    # --- Pre-processamento: extrai JSON de blocos markdown ou texto com prefixo ---
    if isinstance(pareceres_json, str):
        s = pareceres_json.strip()
        if s.startswith("```"):
            linhas = s.splitlines()
            linhas = linhas[1:]
            if linhas and linhas[-1].strip() == "```":
                linhas = linhas[:-1]
            s = "\n".join(linhas).strip()
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
        resultado_base["status"] = "analise_incompleta"
        resultado_base["erro"] = f"JSON invalido: {exc}"
        resultado_base["justificativa_consolidada"] = (
            "Nao foi possivel processar os pareceres: entrada JSON invalida."
        )
        return resultado_base

    if not isinstance(pareceres_completos, dict):
        resultado_base["status"] = "analise_incompleta"
        resultado_base["erro"] = "pareceres_json deve ser um objeto JSON com os cinco pareceres."
        resultado_base["justificativa_consolidada"] = (
            "Entrada invalida: esperado objeto JSON com chaves dos cinco agentes."
        )
        return resultado_base

    # --- Filtra apenas as 5 chaves dos agentes; ignora chaves extras ---
    pareceres_agentes: dict = {}
    for agente in _AGENTES_VALIDOS:
        p_raw = pareceres_completos.get(agente)
        if p_raw is None:
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

    # --- Verifica analise incompleta (algum parecer com erro) ---
    agentes_com_falha: list[dict] = []
    for agente in _AGENTES_VALIDOS:
        p = pareceres_completos[agente]
        if p.get("erro") is not None:
            agentes_com_falha.append({
                "agente": agente,
                "motivo": p["erro"],
            })

    pareceres_res = _extrair_pareceres_resumo(pareceres_completos)
    resultado_base["pareceres"] = pareceres_res

    if agentes_com_falha:
        resultado_base["status"] = "analise_incompleta"
        resultado_base["recomendacao"] = None
        resultado_base["score_consolidado"] = None
        resultado_base["agentes_com_falha"] = agentes_com_falha
        resultado_base["justificativa_consolidada"] = (
            f"Analise incompleta: {len(agentes_com_falha)} agente(s) com falha — "
            f"{', '.join(f['agente'] for f in agentes_com_falha)}. "
            "Corrija os pareceres e resubmeta para obter uma recomendacao."
        )
        resultado_base["principais_riscos"] = _consolidar_riscos(pareceres_completos)
        return resultado_base

    # --- Analise concluida: calculos deterministicos ---
    score        = _calcular_score_consolidado(pareceres_completos)
    recomendacao = _determinar_recomendacao(score, pareceres_completos)
    divergencias = _identificar_divergencias(pareceres_completos)
    riscos       = _consolidar_riscos(pareceres_completos)
    atencao, pontos_criticos = _calcular_atencao_prioritaria(score, pareceres_completos)
    justificativa = _construir_justificativa(pareceres_res, score, recomendacao)

    # Motivos e caminhos apenas para "aguardar"
    if recomendacao == "aguardar":
        motivos, caminhos = _calcular_motivos_e_caminhos(pareceres_completos)
    else:
        motivos, caminhos = [], []

    resultado_base.update({
        "status":                   "concluida",
        "recomendacao":             recomendacao,
        "score_consolidado":        score,
        "divergencias":             divergencias,
        "atencao_prioritaria":      atencao,
        "pontos_criticos":          pontos_criticos,
        "motivos":                  motivos,
        "caminhos":                 caminhos,
        "justificativa_consolidada": justificativa,
        "principais_riscos":        riscos,
    })
    return resultado_base
