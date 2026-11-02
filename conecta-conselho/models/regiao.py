"""
Modelos de dados para o sistema Conecta Conselho.

Todos os dados representados por estes modelos são SIMULADOS e fictícios.
Não representam indicadores reais de nenhuma região do Brasil.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Submodelos por perspectiva
# ---------------------------------------------------------------------------


class DadosMercado(BaseModel):
    """Indicadores de mercado e demanda por conectividade."""

    populacao_estimada: int = Field(..., gt=0, description="População estimada da região")
    domicilios_total: int = Field(..., gt=0, description="Quantidade total de domicílios")
    renda_media_mensal_reais: float = Field(..., gt=0, description="Renda média mensal por domicílio em R$")
    taxa_crescimento_populacional_pct: float = Field(..., ge=0, le=20, description="Taxa de crescimento populacional anual (%)")
    percentual_domicilios_conectados: float = Field(..., ge=0, le=100, description="Percentual de domicílios com internet (%)")
    clientes_potenciais: int = Field(..., ge=0, description="Clientes potenciais estimados (domicílios sem internet)")
    ticket_medio_mensal_reais: float = Field(..., gt=0, description="Ticket médio mensal do serviço em R$")
    numero_concorrentes: int = Field(..., ge=0, description="Número de concorrentes na região")

    @model_validator(mode="after")
    def validar_consistencia_domicilios(self) -> "DadosMercado":
        # população deve ser pelo menos 3× os domicílios
        if self.populacao_estimada < self.domicilios_total * 3:
            raise ValueError(
                f"populacao_estimada ({self.populacao_estimada}) deve ser >= "
                f"domicilios_total * 3 ({self.domicilios_total * 3})"
            )
        # clientes potenciais não podem superar total de domicílios
        if self.clientes_potenciais > self.domicilios_total:
            raise ValueError(
                f"clientes_potenciais ({self.clientes_potenciais}) não pode "
                f"ser maior que domicilios_total ({self.domicilios_total})"
            )
        return self


class DadosSocial(BaseModel):
    """Indicadores de impacto social da expansão de conectividade."""

    percentual_domicilios_sem_internet: float = Field(..., ge=0, le=100, description="% domicílios sem internet")
    quantidade_escolas: int = Field(..., ge=0, description="Total de escolas na região")
    escolas_sem_conectividade_adequada: int = Field(..., ge=0, description="Escolas sem conectividade adequada")
    unidades_saude: int = Field(..., ge=0, description="Total de unidades de saúde")
    unidades_saude_conectividade_inadequada: int = Field(..., ge=0, description="Unidades de saúde com conectividade inadequada")
    percentual_populacao_baixa_renda: float = Field(..., ge=0, le=100, description="% da população de baixa renda")
    indice_vulnerabilidade_social: float = Field(..., ge=0, le=100, description="Índice de vulnerabilidade social (0=sem vulnerabilidade, 100=máxima)")
    pessoas_potencialmente_beneficiadas: int = Field(..., ge=0, description="Pessoas estimadas beneficiadas pela expansão")

    @model_validator(mode="after")
    def validar_subconjuntos(self) -> "DadosSocial":
        if self.escolas_sem_conectividade_adequada > self.quantidade_escolas:
            raise ValueError("escolas_sem_conectividade_adequada não pode superar quantidade_escolas")
        if self.unidades_saude_conectividade_inadequada > self.unidades_saude:
            raise ValueError("unidades_saude_conectividade_inadequada não pode superar unidades_saude")
        return self


class DadosEngenharia(BaseModel):
    """Indicadores de viabilidade técnica e engenharia."""

    tipo_infraestrutura_disponivel: str = Field(..., min_length=5, description="Descrição da infraestrutura disponível")
    distancia_backbone_km: float = Field(..., ge=0, description="Distância até o backbone em km")
    percentual_cobertura_fibra: float = Field(..., ge=0, le=100, description="% de cobertura de fibra óptica")
    capacidade_infraestrutura_existente: str = Field(..., min_length=5, description="Descrição da capacidade da infraestrutura existente")
    dificuldades_tecnicas: List[str] = Field(..., min_length=1, description="Lista de dificuldades técnicas")
    prazo_implantacao_meses: int = Field(..., gt=0, description="Prazo estimado de implantação em meses")
    tecnologias_viaveis: List[str] = Field(..., min_length=1, description="Lista de tecnologias viáveis para expansão")
    indice_viabilidade_tecnica: float = Field(..., ge=0, le=100, description="Índice de viabilidade técnica (0=inviável, 100=totalmente viável)")


class DadosFinanceiro(BaseModel):
    """Indicadores de orçamento e viabilidade financeira."""

    capex_reais: float = Field(..., gt=0, description="Custo inicial de implantação em R$ (CAPEX)")
    opex_mensal_reais: float = Field(..., gt=0, description="Custo operacional mensal em R$ (OPEX)")
    orcamento_disponivel_reais: float = Field(..., gt=0, description="Orçamento disponível em R$")
    taxa_adesao_esperada_pct: float = Field(..., ge=0, le=100, description="Taxa de adesão esperada (%)")
    receita_mensal_reais: float = Field(..., ge=0, description="Receita mensal potencial em R$")
    payback_meses: Optional[int] = Field(None, description="Payback estimado em meses (null = inviável financeiramente)")
    restricoes_orcamentarias: str = Field(..., min_length=5, description="Descrição das restrições orçamentárias")
    riscos_financeiros: List[str] = Field(..., min_length=1, description="Lista de riscos financeiros")


MaturidadeParcerias = Literal["baixa", "média", "alta"]


class DadosParcerias(BaseModel):
    """Indicadores de pontes e oportunidades de parcerias."""

    quantidade_instituicoes_ancora: int = Field(..., ge=0, description="Número de instituições âncora identificadas")
    parceiros_publicos_possiveis: List[str] = Field(..., description="Lista de possíveis parceiros públicos")
    parceiros_privados_possiveis: List[str] = Field(..., description="Lista de possíveis parceiros privados")
    infraestrutura_compartilhavel: bool = Field(..., description="Existe infraestrutura compartilhável disponível?")
    oportunidades_reducao_custos: List[str] = Field(..., description="Oportunidades de redução de custos via parceria")
    percentual_economia_potencial_pct: float = Field(..., ge=0, le=100, description="% potencial de economia mediante parceria")
    maturidade_parcerias: MaturidadeParcerias = Field(..., description="Maturidade estimada das oportunidades de parceria")


# ---------------------------------------------------------------------------
# Modelo principal da Região
# ---------------------------------------------------------------------------


class Regiao(BaseModel):
    """
    Modelo completo de uma região para o sistema Conecta Conselho.

    AVISO: Todos os dados são SIMULADOS e fictícios.
    """

    id: str = Field(..., min_length=2, description="Identificador único da região (slug)")
    nome: str = Field(..., min_length=3, description="Nome da região")
    descricao_perfil: str = Field(..., min_length=10, description="Descrição resumida do perfil da região")
    mercado: DadosMercado
    social: DadosSocial
    engenharia: DadosEngenharia
    financeiro: DadosFinanceiro
    parcerias: DadosParcerias

    @field_validator("id")
    @classmethod
    def id_sem_espacos(cls, v: str) -> str:
        if " " in v:
            raise ValueError("ID da região não pode conter espaços")
        return v.lower()


class ListaRegioes(BaseModel):
    """Wrapper para lista completa de regiões com metadados."""

    metadados: dict
    regioes: List[Regiao]
