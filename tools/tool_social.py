"""
Ferramenta Python do Agente de Impacto Social — Conecta Conselho.

Analisa os benefícios sociais potenciais da expansão de conectividade
em uma região fictícia da base simulada.

Agente: Agente de Impacto Social (cc_impacto_social)
Integrante: Responsável pelo Agente de Impacto Social

AVISO: Todos os dados retornados são SIMULADOS e fictícios.
Não representam indicadores reais de nenhuma região do Brasil.

Publicação e integração na IBM Cloud serão realizadas posteriormente.

Estrutura de importação:
  Este arquivo está em inteli_girls/tools/tool_social.py.
  A base compartilhada está em inteli_girls/conecta-conselho/tools/consultar_regiao.py.
  O path insert garante que 'from tools.consultar_regiao import ...' resolva corretamente.
  Esta resolução é independente do diretório de execução (usa Path(__file__)).

Portabilidade do decorador @tool:
  O import do ADK usa try/except com fallback transparente (identidade).
  Isso permite:
    - Importar e testar este módulo sem o venv do ADK ativo.
    - Usar as funções puras (_calcular_*, _montar_*, _identificar_*) em qualquer
      ambiente Python 3.12.
    - Integrar ao ADK normalmente quando o pacote estiver disponível.
  O comportamento da ferramenta não muda entre os dois caminhos de import.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Adiciona o diretório conecta-conselho/ ao path para importar
# as ferramentas compartilhadas (consultar_regiao.py).
# Nota: tools/tool_social.py fica na raiz do repo (inteli_girls/tools/),
# enquanto a base de dados está em conecta-conselho/. O path insert
# garante que 'from tools.consultar_regiao import ...' resolva para
# conecta-conselho/tools/consultar_regiao.py
_CONECTA_CONSELHO_DIR = str(Path(__file__).parent.parent / "conecta-conselho")
if _CONECTA_CONSELHO_DIR not in sys.path:
    sys.path.insert(0, _CONECTA_CONSELHO_DIR)

try:
    from ibm_watsonx_orchestrate.agent_builder.tools import tool as tool  # noqa: PLC0414
    _ADK_DISPONIVEL = True
except ImportError:  # pragma: no cover — só ocorre fora do venv do ADK
    def tool(func):  # type: ignore[misc]
        """Fallback: sem ADK disponível, @tool é uma identidade (retorna a própria função)."""
        return func
    _ADK_DISPONIVEL = False

from tools.consultar_regiao import consultar_social, listar_ids_regioes

# ---------------------------------------------------------------------------
# Constantes de normalização (calibradas para as 6 regiões simuladas)
# ---------------------------------------------------------------------------

_REFERENCIA_MAX_PESSOAS_BENEFICIADAS = 120_000
"""Referência máxima para normalização do sub-score de alcance.

Premissa documentada (MVP):
  O maior valor de pessoas_potencialmente_beneficiadas na base simulada é 101.376
  (Região Horizonte). A referência de 120.000 foi escolhida ligeiramente acima desse
  máximo para que nenhuma região atinja automaticamente score 100 apenas por tamanho,
  preservando margem de discriminação entre regiões.

  Valores de todas as regiões:
    aurora      :  70.528
    horizonte   : 101.376  ← maior valor
    esperanca   :  62.400
    central     :  65.152
    vale_verde  :  44.544
    nova_uniao  :  41.984

  Fórmula: score_alcance = min(100, (pessoas / 120.000) × 100)
  Horizonte → min(100, 101376/120000 × 100) = min(100, 84.5) = 84.5 → 85

  Revisão: se novas regiões forem adicionadas com valores acima de 120.000,
  esta constante deve ser reavaliada em alinhamento com a equipe.
"""

_IDS_VALIDOS = frozenset({"aurora", "horizonte", "esperanca", "central", "vale_verde", "nova_uniao"})
"""IDs válidos de regiões. Usa frozenset para imutabilidade."""


# ---------------------------------------------------------------------------
# Lógica de cálculo — funções puras, testáveis sem o decorador @tool
# ---------------------------------------------------------------------------


def _calcular_percentual_seguro(numerador: int, denominador: int) -> float:
    """Calcula percentual de forma segura, retornando 0.0 se denominador for 0."""
    if denominador == 0:
        return 0.0
    return round((numerador / denominador) * 100, 1)


_CAMPOS_OBRIGATORIOS_SOCIAL = [
    "percentual_domicilios_sem_internet",
    "quantidade_escolas",
    "escolas_sem_conectividade_adequada",
    "unidades_saude",
    "unidades_saude_conectividade_inadequada",
    "percentual_populacao_baixa_renda",
    "indice_vulnerabilidade_social",
    "pessoas_potencialmente_beneficiadas",
]
"""Campos obrigatórios da perspectiva social. Usados em _determinar_confianca e _listar_ausentes."""

_CAMPOS_CRITICOS_SOCIAL = frozenset({
    "percentual_domicilios_sem_internet",
    "indice_vulnerabilidade_social",
    "pessoas_potencialmente_beneficiadas",
})
"""
Campos críticos: ausência de qualquer um deles compromete o sub-score principal.
  - percentual_domicilios_sem_internet : sub-score exclusão digital (peso 35%)
  - indice_vulnerabilidade_social       : sub-score vulnerabilidade (peso 20%)
  - pessoas_potencialmente_beneficiadas : sub-score alcance (peso 15%)
"""


def _listar_campos_ausentes(dados: dict) -> list[str]:
    """
    Retorna lista de campos obrigatórios ausentes ou None em `dados`.

    Usado para produzir avisos explícitos nas limitações do parecer quando
    a análise foi realizada com dados incompletos.
    """
    return [c for c in _CAMPOS_OBRIGATORIOS_SOCIAL if dados.get(c) is None]


def _determinar_confianca(dados: dict) -> str:
    """
    Determina confiança com base na completude dos dados — não é julgamento do LLM.

    IMPORTANTE: Este campo representa APENAS a completude dos dados consultados,
    não a confiança na recomendação do Guardião nem uma probabilidade estatística.
    Uma confiança "alta" significa que todos os campos esperados estavam presentes
    na base simulada; não implica que os dados são precisos ou que a análise é
    conclusiva para decisão de investimento.

    Critério (conforme PADRAO_DESENVOLVIMENTO_AGENTES.md, Seção 3.3):
      - "alta":       todos os 8 campos obrigatórios presentes e com valores não-None.
      - "media":      pelo menos 6 dos 8 campos presentes; nenhum campo crítico ausente.
      - "baixa":      menos de 6 campos presentes, ou campo crítico ausente.
      - "nao_avaliada": reservado para saída de erro (região não encontrada).
                        Nunca retornado por esta função; definido em _montar_resposta_erro.

    Campos críticos: percentual_domicilios_sem_internet, indice_vulnerabilidade_social,
                     pessoas_potencialmente_beneficiadas.
    """
    presentes = [c for c in _CAMPOS_OBRIGATORIOS_SOCIAL if dados.get(c) is not None]
    ausentes_criticos = [c for c in _CAMPOS_CRITICOS_SOCIAL if dados.get(c) is None]

    if ausentes_criticos:
        return "baixa"
    if len(presentes) == len(_CAMPOS_OBRIGATORIOS_SOCIAL):
        return "alta"
    if len(presentes) >= 6:
        return "media"
    return "baixa"


def _obter_campo_numerico(dados: dict, campo: str, tipo: type, padrao):
    """
    Extrai um campo numérico do dict de dados, distinguindo ausente/None de zero legítimo.

    Retorna o valor convertido para `tipo` se presente e não-None, ou `padrao` caso contrário.

    Motivação: dados.get("campo", 0) trata campo ausente e campo=0 da mesma forma.
    Esta função preserva a distinção para uso no logging e na detecção de confiança,
    sem alterar o comportamento do cálculo (o padrão continua sendo 0 para campos ausentes).

    Args:
        dados:  dicionário de dados brutos da base simulada.
        campo:  nome do campo a extrair.
        tipo:   tipo de conversão (int ou float).
        padrao: valor a retornar quando o campo está ausente ou é None.
    """
    valor = dados.get(campo)
    if valor is None:
        return padrao
    return tipo(valor)


def _calcular_indicadores_sociais(dados: dict) -> tuple[dict, int]:
    """
    Calcula todos os indicadores derivados e sub-scores a partir dos dados brutos.

    Fórmulas conforme PADRAO_DESENVOLVIMENTO_AGENTES.md, Seção 7.

    Sub-scores (todos de 0 a 100):

      score_exclusao_digital (peso 35%):
          = percentual_domicilios_sem_internet
          Quanto mais domicílios sem internet, maior o potencial de impacto.

      score_infraestrutura_social (peso 30%):
          Média simples de % escolas sem conectividade e % saúde sem conectividade.
          pct_escolas = (escolas_sem / total_escolas) × 100
          pct_saude   = (saude_sem / total_saude) × 100
          score_infra = (pct_escolas + pct_saude) / 2

      score_vulnerabilidade (peso 20%):
          = indice_vulnerabilidade_social  (já em escala 0–100 na base)
          0 = sem vulnerabilidade; 100 = máxima vulnerabilidade.

      score_alcance (peso 15%):
          Normaliza pessoas_potencialmente_beneficiadas pela referência máxima.
          = min(100, (pessoas / 120.000) × 100)

    Score final = 0.35×exclusão + 0.30×infraestrutura + 0.20×vulnerabilidade + 0.15×alcance
    Arredondado para inteiro (round() usa banker's rounding — determinístico).

    Returns:
        Tupla (indicadores: dict, score_final: int).
        Campos ausentes na base resultam em zero no cálculo; a confiança
        correspondente será reduzida por _determinar_confianca.
    """
    pct_sem_internet = _obter_campo_numerico(dados, "percentual_domicilios_sem_internet", float, 0.0)
    qtd_escolas      = _obter_campo_numerico(dados, "quantidade_escolas", int, 0)
    escolas_sem      = _obter_campo_numerico(dados, "escolas_sem_conectividade_adequada", int, 0)
    qtd_saude        = _obter_campo_numerico(dados, "unidades_saude", int, 0)
    saude_sem        = _obter_campo_numerico(dados, "unidades_saude_conectividade_inadequada", int, 0)
    vulnerabilidade  = _obter_campo_numerico(dados, "indice_vulnerabilidade_social", float, 0.0)
    pessoas          = _obter_campo_numerico(dados, "pessoas_potencialmente_beneficiadas", int, 0)
    baixa_renda      = _obter_campo_numerico(dados, "percentual_populacao_baixa_renda", float, 0.0)

    # Percentuais derivados — calculados em Python, não assumidos da base
    pct_escolas_sem = _calcular_percentual_seguro(escolas_sem, qtd_escolas)
    pct_saude_sem = _calcular_percentual_seguro(saude_sem, qtd_saude)

    # Sub-scores (todos em [0.0, 100.0] antes do arredondamento)
    score_exclusao_digital    = min(100.0, max(0.0, pct_sem_internet))
    score_infraestrutura_social = min(100.0, max(0.0, (pct_escolas_sem + pct_saude_sem) / 2))
    score_vulnerabilidade     = min(100.0, max(0.0, vulnerabilidade))
    score_alcance             = min(100.0, max(0.0, (pessoas / _REFERENCIA_MAX_PESSOAS_BENEFICIADAS) * 100))

    # Score final ponderado
    score_final = (
        0.35 * score_exclusao_digital
        + 0.30 * score_infraestrutura_social
        + 0.20 * score_vulnerabilidade
        + 0.15 * score_alcance
    )

    return {
        # Dados brutos da base (None substituído por 0 — confiança reflete ausências)
        "percentual_domicilios_sem_internet": pct_sem_internet,
        "quantidade_escolas": qtd_escolas,
        "escolas_sem_conectividade_adequada": escolas_sem,
        "unidades_saude": qtd_saude,
        "unidades_saude_conectividade_inadequada": saude_sem,
        "percentual_populacao_baixa_renda": baixa_renda,
        "indice_vulnerabilidade_social": vulnerabilidade,
        "pessoas_potencialmente_beneficiadas": pessoas,
        # Indicadores derivados calculados em Python
        "percentual_escolas_sem_conectividade": pct_escolas_sem,
        "percentual_saude_sem_conectividade": pct_saude_sem,
        # Sub-scores (todos 0–100, inteiros)
        "score_exclusao_digital": round(score_exclusao_digital),
        "score_infraestrutura_social": round(score_infraestrutura_social),
        "score_vulnerabilidade": round(score_vulnerabilidade),
        "score_alcance": round(score_alcance),
    }, round(score_final)


def _formatar_numero_ptbr(n: int) -> str:
    """
    Formata um inteiro com separador de milhar no padrão pt-BR (ponto).

    Exemplo: 101376 → "101.376"

    Não usa locale (evita dependência de configuração do sistema operacional)
    nem f-string ":," seguida de replace — que substituiria todas as vírgulas
    do texto, incluindo as gramaticais.
    """
    return f"{n:,}".replace(",", ".")


def _montar_justificativa(regiao_nome: str, indicadores: dict, score: int) -> str:
    """
    Monta texto de justificativa com base nos indicadores calculados.

    Usa _formatar_numero_ptbr para o separador de milhar pt-BR em vez de
    f-string :, + replace(",", "."), que substituiria todas as vírgulas do
    texto incluindo as gramaticais.
    """
    pct_sem = indicadores["percentual_domicilios_sem_internet"]
    vulnerabilidade = indicadores["indice_vulnerabilidade_social"]
    pessoas = indicadores["pessoas_potencialmente_beneficiadas"]
    pct_escolas = indicadores["percentual_escolas_sem_conectividade"]
    pct_saude = indicadores["percentual_saude_sem_conectividade"]
    baixa_renda = indicadores["percentual_populacao_baixa_renda"]

    pessoas_fmt = _formatar_numero_ptbr(pessoas)
    return (
        f"A {regiao_nome} apresenta {pct_sem:.0f}% dos domicílios sem acesso à internet, "
        f"índice de vulnerabilidade social de {vulnerabilidade:.0f}/100 e "
        f"{pessoas_fmt} pessoas potencialmente beneficiadas pela expansão. "
        f"{pct_escolas:.1f}% das escolas e {pct_saude:.1f}% das unidades de saúde "
        f"carecem de conectividade adequada. "
        f"A parcela de {baixa_renda:.0f}% da população em situação de baixa renda reforça "
        f"a necessidade de abordagem inclusiva. "
        f"Score de impacto social calculado: {score}/100 "
        f"(maior score indica maior potencial de benefício social com a expansão)."
    )


def _identificar_riscos(dados: dict, regiao_nome: str) -> list[str]:
    """Identifica riscos sociais relevantes com base nos dados da região."""
    riscos = []
    baixa_renda = float(dados.get("percentual_populacao_baixa_renda", 0))
    pct_sem = float(dados.get("percentual_domicilios_sem_internet", 0))
    vulnerabilidade = float(dados.get("indice_vulnerabilidade_social", 0))

    if baixa_renda > 50:
        riscos.append(
            f"Alta concentração de baixa renda ({baixa_renda:.0f}%) pode limitar "
            f"adesão ao serviço sem modelo de plano subsidiado."
        )
    if pct_sem > 60:
        riscos.append(
            f"Exclusão digital elevada ({pct_sem:.0f}% dos domicílios) exige "
            f"infraestrutura de suporte e letramento digital para conversão em adesão."
        )
    if vulnerabilidade > 65:
        riscos.append(
            f"Índice de vulnerabilidade social alto ({vulnerabilidade:.0f}/100) indica "
            f"que a expansão isolada pode não ser suficiente sem políticas complementares."
        )
    if not riscos:
        riscos.append("Perfil social moderado; riscos identificados são compatíveis com o projeto.")
    return riscos


def _montar_resposta_erro(regiao_id: str, mensagem_erro: str) -> dict:
    """
    Monta resposta padronizada de erro conforme contrato v1.0 (Seção 3.4).

    O campo 'confianca' é definido como 'nao_avaliada' para erros fatais.
    O Guardião identifica erro por: erro != null e confianca == 'nao_avaliada'.
    """
    ids_validos = ", ".join(sorted(_IDS_VALIDOS))
    return {
        "agente": "impacto_social",
        "regiao_id": regiao_id,
        "regiao_nome": None,
        "score": 0,
        "confianca": "nao_avaliada",
        "indicadores": {},
        "justificativa": (
            f"Região '{regiao_id}' não encontrada na base de dados simulada. "
            f"IDs válidos: {ids_validos}."
        ),
        "riscos": [],
        "limitacoes": ["Região não encontrada na base simulada."],
        "simulado": True,
        "erro": mensagem_erro,
    }


# ---------------------------------------------------------------------------
# Ferramenta pública — decorada com @tool para o ADK
# ---------------------------------------------------------------------------


@tool
def analisar_impacto_social(regiao_id: str) -> dict:
    """
    Analisa o impacto social potencial da expansão de conectividade em uma região.

    Consulta a base de dados simulada do Conecta Conselho e calcula um score de
    impacto social de 0 a 100 com base em exclusão digital, infraestrutura social
    (escolas e unidades de saúde sem conectividade), vulnerabilidade social e
    alcance estimado de beneficiados.

    Quanto maior o score, maior o potencial de benefício social com a expansão.
    Todos os dados são SIMULADOS — não representam indicadores reais.

    Args:
        regiao_id: Identificador da região. Valores válidos:
                   aurora, horizonte, esperanca, central, vale_verde, nova_uniao

    Returns:
        Parecer estruturado com score de 0-100, indicadores calculados,
        justificativa, riscos e limitações. Segue o contrato padrão de
        saída dos agentes especialistas do Conecta Conselho.
    """
    print(f"[INFO][agente_impacto_social] Consultando região: {regiao_id}")

    resultado = consultar_social(regiao_id)

    if "erro" in resultado:
        print(
            f"[ERRO][agente_impacto_social] Região não encontrada: {regiao_id}",
            file=sys.stderr,
        )
        return _montar_resposta_erro(regiao_id, resultado["erro"])

    regiao_nome = resultado.get("nome", regiao_id)
    dados_sociais = resultado.get("dados", {})

    campos_ausentes = _listar_campos_ausentes(dados_sociais)
    confianca = _determinar_confianca(dados_sociais)
    indicadores, score = _calcular_indicadores_sociais(dados_sociais)
    justificativa = _montar_justificativa(regiao_nome, indicadores, score)
    riscos = _identificar_riscos(dados_sociais, regiao_nome)

    if campos_ausentes:
        print(
            f"[AVISO][agente_impacto_social] Região {regiao_id} — "
            f"campos ausentes na base: {campos_ausentes}",
            file=sys.stderr,
        )

    print(
        f"[INFO][agente_impacto_social] Região {regiao_id} — score={score}, confianca={confianca}"
    )

    # Limitações base — sempre presentes
    limitacoes = [
        # Texto exato conforme contrato PADRAO_DESENVOLVIMENTO_AGENTES.md Seção 3.2
        "Dado simulado — não reflete condições reais.",
        "Índice de vulnerabilidade social é proxy simulado, não metodologia IBGE.",
        "Pessoas beneficiadas estimadas com base em premissa de 3,2 moradores/domicílio.",
        (
            f"Referência de normalização de alcance: "
            f"{_REFERENCIA_MAX_PESSOAS_BENEFICIADAS} pessoas "
            f"(calibrada acima do máximo da base: 101.376 — Região Horizonte)."
        ),
        "confianca indica completude dos dados, não probabilidade de sucesso do investimento.",
    ]

    # Limitações adicionais — apenas quando há campos ausentes
    # Sinaliza incompletude via limitacoes e confianca.
    # O Guardião identifica pareceres parciais por confianca == 'baixa'.
    if campos_ausentes:
        ausentes_str = ", ".join(campos_ausentes)
        criticos_ausentes = [c for c in campos_ausentes if c in _CAMPOS_CRITICOS_SOCIAL]
        if criticos_ausentes:
            criticos_str = ", ".join(criticos_ausentes)
            limitacoes.append(
                f"ATENÇÃO: campos críticos ausentes na base — {criticos_str}. "
                f"Sub-scores correspondentes foram calculados como zero. "
                f"Este parecer é PARCIAL e não deve ser usado isoladamente para decisão."
            )
        else:
            limitacoes.append(
                f"Campos não críticos ausentes na base: {ausentes_str}. "
                f"Score calculado com dados parciais."
            )

    return {
        "agente": "impacto_social",
        "regiao_id": resultado["id"],
        "regiao_nome": regiao_nome,
        "score": score,
        # confianca representa APENAS completude dos dados (ver _determinar_confianca).
        # Não representa confiança na recomendação de investimento.
        # Guardião identifica pareceres parciais por confianca == 'baixa'.
        "confianca": confianca,
        "indicadores": indicadores,
        "justificativa": justificativa,
        "riscos": riscos,
        "limitacoes": limitacoes,
        "simulado": True,
        "erro": None,
    }


# ---------------------------------------------------------------------------
# Bloco de execução direta para teste rápido
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Teste rápido do Agente de Impacto Social ===\n")
    for rid in ["horizonte", "aurora", "nova_uniao", "nao_existe"]:
        # O decorador @tool envolve o retorno em ToolResponse; acessar via .content
        resposta = analisar_impacto_social(rid)
        resultado = resposta.content
        print(f"--- {rid} ---")
        print(f"  score     : {resultado['score']}")
        print(f"  confianca : {resultado['confianca']}")
        print(f"  erro      : {resultado['erro']}")
        if resultado.get("indicadores"):
            ind = resultado["indicadores"]
            print(f"  pct_sem_internet : {ind.get('percentual_domicilios_sem_internet')}")
            print(f"  score_exclusao   : {ind.get('score_exclusao_digital')}")
            print(f"  score_infra      : {ind.get('score_infraestrutura_social')}")
        print()
