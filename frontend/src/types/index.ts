// ─── Region Data ────────────────────────────────────────────────────────────

export interface RegionSummary {
  id: string
  nome: string
  descricao_perfil: string
}

export interface RegionMercado {
  populacao_estimada: number
  domicilios_total: number
  renda_media_mensal_reais: number
  taxa_crescimento_populacional_pct: number
  percentual_domicilios_conectados: number
  clientes_potenciais: number
  ticket_medio_mensal_reais: number
  numero_concorrentes: number
}

export interface RegionSocial {
  percentual_domicilios_sem_internet: number
  quantidade_escolas: number
  escolas_sem_conectividade_adequada: number
  unidades_saude: number
  unidades_saude_conectividade_inadequada: number
  percentual_populacao_baixa_renda: number
  indice_vulnerabilidade_social: number
  pessoas_potencialmente_beneficiadas: number
}

export interface RegionEngenharia {
  tipo_infraestrutura_disponivel: string
  distancia_backbone_km: number
  percentual_cobertura_fibra: number
  capacidade_infraestrutura_existente: string
  dificuldades_tecnicas: string[]
  prazo_implantacao_meses: number
  tecnologias_viaveis: string[]
  indice_viabilidade_tecnica: number
}

export interface RegionFinanceiro {
  capex_reais: number
  opex_mensal_reais: number
  orcamento_disponivel_reais: number
  taxa_adesao_esperada_pct: number
  receita_mensal_reais: number
  payback_meses: number | null
  restricoes_orcamentarias: string
  riscos_financeiros: string[]
}

export interface RegionParcerias {
  quantidade_instituicoes_ancora: number
  parceiros_publicos_possiveis: string[]
  parceiros_privados_possiveis: string[]
  infraestrutura_compartilhavel: boolean
  oportunidades_reducao_custos: string[]
  maturidade_parcerias: 'baixa' | 'média' | 'alta'
  economia_estimada_pct: number
}

export interface Region extends RegionSummary {
  mercado: RegionMercado
  social: RegionSocial
  engenharia: RegionEngenharia
  financeiro: RegionFinanceiro
  parcerias: RegionParcerias
}

// ─── Agent Reports ───────────────────────────────────────────────────────────

export type Confianca = 'alta' | 'media' | 'baixa' | 'nao_avaliada'

export interface AgentReport {
  score: number
  confianca: Confianca
  justificativa: string
  riscos: string[]
  limitacoes: string[]
  regiao_id?: string
  regiao_nome?: string
  erro?: string
}

export interface GuardianPaeceres {
  mercado: AgentReport
  impacto_social: AgentReport
  engenharia: AgentReport
  orcamento: AgentReport
  pontes: AgentReport
}

// ─── Guardian Result ─────────────────────────────────────────────────────────

export type Recomendacao =
  | 'investir_agora'
  | 'realizar_piloto'
  | 'aguardar'
  | 'escalar_humano'

export type AnaliseStatus = 'concluida' | 'analise_incompleta'

export interface GuardianResult {
  regiao_id: string
  regiao_nome: string
  score_consolidado: number
  recomendacao: Recomendacao
  status: AnaliseStatus
  atencao_prioritaria: boolean
  pontos_criticos: string[]
  justificativa_consolidada: string
  motivos: string[]
  caminhos: string[]
  divergencias: string[]
  principais_riscos: string[]
  limitacoes: string[]
  fonte: 'local' | 'nuvem'
  tempo_analise_segundos: number
  pareceres: GuardianPaeceres
  agentes_com_falha?: Array<{ agente: string; motivo: string }>
  erro?: string
}

// ─── Simulator ───────────────────────────────────────────────────────────────

export interface SimulatorParams {
  regiao_id: string
  reducao_capex_pct: number
  ancoras_adicionais: number
  maturidade_parcerias: 'baixa' | 'média' | 'alta'
}

export interface SimulatorResult {
  base: GuardianResult
  parcerias: GuardianResult
  mudou_recomendacao: boolean
}

// ─── Session History ─────────────────────────────────────────────────────────

export interface HistoryEntry {
  resultado: GuardianResult
  timestamp: string
}
