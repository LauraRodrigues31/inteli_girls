"""
Funções de consulta à base de dados do Conecta Conselho.

Estas funções são agnósticas à plataforma IBM e podem ser utilizadas
diretamente em Python, no Streamlit, ou como base para ferramentas
do IBM watsonx Orchestrate ADK (sem importação automática nesta etapa).

AVISO: Todos os dados retornados são SIMULADOS e fictícios.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# ---------------------------------------------------------------------------
# Carregamento da base de dados
# ---------------------------------------------------------------------------

_DATA_PATH = Path(__file__).parent.parent / "data" / "regioes.json"


def _carregar_dados() -> Dict[str, Any]:
    """Carrega o arquivo JSON de regiões. Lança FileNotFoundError se ausente."""
    if not _DATA_PATH.exists():
        raise FileNotFoundError(
            f"Arquivo de dados não encontrado: {_DATA_PATH}\n"
            "Certifique-se de que 'data/regioes.json' existe na pasta conecta-conselho."
        )
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _get_regioes_raw() -> List[Dict[str, Any]]:
    """Retorna a lista bruta de regiões do JSON."""
    dados = _carregar_dados()
    return dados.get("regioes", [])


def _buscar_por_id(id_regiao: str) -> Optional[Dict[str, Any]]:
    """Retorna o dicionário bruto da região pelo ID, ou None se não encontrar."""
    id_normalizado = id_regiao.strip().lower()
    for regiao in _get_regioes_raw():
        if regiao.get("id", "").lower() == id_normalizado:
            return regiao
    return None


def _regiao_nao_encontrada(id_regiao: str) -> Dict[str, str]:
    """Retorna mensagem padronizada para região não encontrada."""
    regioes = [r["id"] for r in _get_regioes_raw()]
    return {
        "erro": "Região não encontrada",
        "id_consultado": id_regiao,
        "mensagem": (
            f"Nenhuma região com id '{id_regiao}' foi encontrada na base de dados. "
            f"IDs disponíveis: {', '.join(regioes)}"
        ),
    }


# ---------------------------------------------------------------------------
# Funções públicas de consulta
# ---------------------------------------------------------------------------


def listar_regioes() -> List[Dict[str, str]]:
    """
    Retorna a lista de todas as regiões disponíveis com ID e nome.

    Returns:
        Lista de dicionários com 'id', 'nome' e 'descricao_perfil' de cada região.

    Exemplo de uso:
        >>> regioes = listar_regioes()
        >>> for r in regioes:
        ...     print(r['id'], '-', r['nome'])
    """
    return [
        {
            "id": r["id"],
            "nome": r["nome"],
            "descricao_perfil": r.get("descricao_perfil", ""),
        }
        for r in _get_regioes_raw()
    ]


def consultar_regiao(id_regiao: str) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Retorna todos os dados estruturados de uma região pelo ID.

    Args:
        id_regiao: Identificador único da região (ex: 'aurora', 'central').

    Returns:
        Dicionário completo da região com todos os indicadores,
        ou dicionário de erro com mensagem clara se não encontrada.

    Exemplo de uso:
        >>> dados = consultar_regiao('aurora')
        >>> print(dados['nome'])
        Região Aurora
    """
    regiao = _buscar_por_id(id_regiao)
    if regiao is None:
        return _regiao_nao_encontrada(id_regiao)
    return regiao


def consultar_mercado(id_regiao: str) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Retorna os indicadores de mercado de uma região.

    Args:
        id_regiao: Identificador único da região.

    Returns:
        Dicionário com indicadores de mercado (população, domicílios, renda,
        clientes potenciais, ticket médio, concorrentes), com identificação
        da região. Retorna erro se a região não existir.

    Exemplo de uso:
        >>> mercado = consultar_mercado('horizonte')
        >>> print(mercado['clientes_potenciais'])
    """
    regiao = _buscar_por_id(id_regiao)
    if regiao is None:
        return _regiao_nao_encontrada(id_regiao)
    return {
        "id": regiao["id"],
        "nome": regiao["nome"],
        "perspectiva": "mercado",
        "dados": regiao["mercado"],
    }


def consultar_social(id_regiao: str) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Retorna os indicadores de impacto social de uma região.

    Args:
        id_regiao: Identificador único da região.

    Returns:
        Dicionário com indicadores sociais (domicílios sem internet, escolas,
        unidades de saúde, vulnerabilidade social, pessoas beneficiadas).
        Retorna erro se a região não existir.

    Exemplo de uso:
        >>> social = consultar_social('horizonte')
        >>> print(social['dados']['indice_vulnerabilidade_social'])
    """
    regiao = _buscar_por_id(id_regiao)
    if regiao is None:
        return _regiao_nao_encontrada(id_regiao)
    return {
        "id": regiao["id"],
        "nome": regiao["nome"],
        "perspectiva": "social",
        "dados": regiao["social"],
    }


def consultar_engenharia(id_regiao: str) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Retorna os indicadores de engenharia e viabilidade técnica de uma região.

    Args:
        id_regiao: Identificador único da região.

    Returns:
        Dicionário com indicadores técnicos (infraestrutura, distância do backbone,
        cobertura de fibra, tecnologias viáveis, prazo e índice de viabilidade).
        Retorna erro se a região não existir.

    Exemplo de uso:
        >>> eng = consultar_engenharia('esperanca')
        >>> print(eng['dados']['indice_viabilidade_tecnica'])
    """
    regiao = _buscar_por_id(id_regiao)
    if regiao is None:
        return _regiao_nao_encontrada(id_regiao)
    return {
        "id": regiao["id"],
        "nome": regiao["nome"],
        "perspectiva": "engenharia",
        "dados": regiao["engenharia"],
    }


def consultar_financeiro(id_regiao: str) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Retorna os indicadores financeiros e orçamentários de uma região.

    Args:
        id_regiao: Identificador único da região.

    Returns:
        Dicionário com indicadores financeiros (CAPEX, OPEX, receita, payback,
        restrições orçamentárias e riscos financeiros).
        Retorna erro se a região não existir.

    Exemplo de uso:
        >>> fin = consultar_financeiro('central')
        >>> print(fin['dados']['payback_meses'])
    """
    regiao = _buscar_por_id(id_regiao)
    if regiao is None:
        return _regiao_nao_encontrada(id_regiao)
    return {
        "id": regiao["id"],
        "nome": regiao["nome"],
        "perspectiva": "financeiro",
        "dados": regiao["financeiro"],
    }


def consultar_parcerias(id_regiao: str) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Retorna os indicadores de parcerias e oportunidades de uma região.

    Args:
        id_regiao: Identificador único da região.

    Returns:
        Dicionário com indicadores de parcerias (instituições âncora, parceiros
        públicos e privados, oportunidades de redução de custos, maturidade).
        Retorna erro se a região não existir.

    Exemplo de uso:
        >>> parcerias = consultar_parcerias('vale_verde')
        >>> print(parcerias['dados']['maturidade_parcerias'])
    """
    regiao = _buscar_por_id(id_regiao)
    if regiao is None:
        return _regiao_nao_encontrada(id_regiao)
    return {
        "id": regiao["id"],
        "nome": regiao["nome"],
        "perspectiva": "parcerias",
        "dados": regiao["parcerias"],
    }


# ---------------------------------------------------------------------------
# Utilitários de apoio ao Streamlit e comparação
# ---------------------------------------------------------------------------


def listar_ids_regioes() -> List[str]:
    """Retorna somente os IDs de todas as regiões. Útil para validações."""
    return [r["id"] for r in _get_regioes_raw()]


def comparar_indicador(campo_path: str) -> List[Dict[str, Any]]:
    """
    Compara um indicador específico entre todas as regiões.

    Args:
        campo_path: Caminho do campo no formato 'secao.campo'
                    Ex: 'mercado.renda_media_mensal_reais',
                        'engenharia.indice_viabilidade_tecnica',
                        'financeiro.payback_meses'

    Returns:
        Lista ordenada de dicionários com id, nome e valor do indicador.
        Regiões com valor None (ex: payback inviável) aparecem por último.

    Exemplo de uso:
        >>> ranking = comparar_indicador('engenharia.indice_viabilidade_tecnica')
        >>> for item in ranking:
        ...     print(item['nome'], '->', item['valor'])
    """
    partes = campo_path.split(".", 1)
    if len(partes) != 2:
        return [{"erro": "campo_path deve ter formato 'secao.campo'", "exemplo": "mercado.renda_media_mensal_reais"}]

    secao, campo = partes
    resultado = []
    for regiao in _get_regioes_raw():
        secao_dados = regiao.get(secao, {})
        valor = secao_dados.get(campo)
        resultado.append({"id": regiao["id"], "nome": regiao["nome"], "valor": valor})

    # Ordena: valores numéricos primeiro (desc), None por último
    resultado.sort(
        key=lambda x: (x["valor"] is None, -(x["valor"] or 0) if isinstance(x["valor"], (int, float)) else 0)
    )
    return resultado
