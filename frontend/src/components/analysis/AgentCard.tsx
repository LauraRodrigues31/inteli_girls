import { Tile, Tag, Accordion, AccordionItem } from '@carbon/react'
import {
  ShoppingCart,
  Group,
  Settings,
  Finance,
  Partnership,
} from '@carbon/icons-react'
import type { AgentReport, Confianca } from '../../types'
import { ScoreProgressBar } from './ScoreProgressBar'

const AGENT_CONFIG: Record<string, { label: string; Icon: React.ElementType; description: string }> = {
  mercado:       { label: 'Mercado',        Icon: ShoppingCart, description: 'Vale a pena financeiramente?' },
  impacto_social:{ label: 'Impacto Social', Icon: Group,        description: 'Quem ganha com a conexão?' },
  engenharia:    { label: 'Engenharia',     Icon: Settings,     description: 'Dá para construir?' },
  orcamento:     { label: 'Orçamento',      Icon: Finance,      description: 'Cabe no limite de custo e prazo?' },
  pontes:        { label: 'Pontes',         Icon: Partnership,  description: 'Dá para tornar a região viável?' },
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyTagType = any

const CONFIANCA_TYPE: Record<Confianca, AnyTagType> = {
  alta:         'green',
  media:        'blue',
  baixa:        'red',
  nao_avaliada: 'gray',
}

const CONFIANCA_LABEL: Record<Confianca, string> = {
  alta:         'Alta',
  media:        'Média',
  baixa:        'Baixa',
  nao_avaliada: 'Não avaliada',
}

interface AgentCardProps {
  agentKey: string
  parecer: AgentReport
}

export function AgentCard({ agentKey, parecer }: AgentCardProps) {
  const config = AGENT_CONFIG[agentKey] ?? { label: agentKey, Icon: Settings, description: '' }
  const { Icon } = config
  const confianca = parecer.confianca ?? 'nao_avaliada'

  return (
    <Tile style={{ padding: '20px', borderLeft: `4px solid ${parecer.erro ? '#da1e28' : '#0043ce'}` }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Icon size={20} style={{ color: '#0043ce' }} aria-hidden />
          <div>
            <p style={{ fontWeight: 600, fontSize: '15px', margin: 0 }}>{config.label}</p>
            <p style={{ fontSize: '12px', color: '#6f6f6f', margin: 0 }}>{config.description}</p>
          </div>
        </div>
        <Tag type={CONFIANCA_TYPE[confianca]} size="sm">
          {CONFIANCA_LABEL[confianca]}
        </Tag>
      </div>

      {/* Score bar */}
      {!parecer.erro && <ScoreProgressBar score={parecer.score ?? 0} height={12} showNumber animate />}

      {/* Error */}
      {parecer.erro && <p style={{ color: '#da1e28', fontSize: '13px', marginTop: '8px' }}>⚠ {parecer.erro}</p>}

      {/* Justificativa accordion — wrap in div to avoid Accordion style prop error */}
      {!parecer.erro && parecer.justificativa && (
        <div style={{ marginTop: '12px' }}>
          <Accordion>
            <AccordionItem title="📋 Justificativa, Riscos e Limitações">
              <p style={{ fontSize: '13px', lineHeight: 1.6, marginBottom: '8px' }}>{parecer.justificativa}</p>
              {parecer.riscos?.length > 0 && (
                <>
                  <p style={{ fontWeight: 600, fontSize: '13px' }}>Riscos:</p>
                  <ul style={{ paddingLeft: '18px', fontSize: '13px' }}>
                    {parecer.riscos.map((r, i) => <li key={i}>{r}</li>)}
                  </ul>
                </>
              )}
              {parecer.limitacoes?.length > 0 && (
                <>
                  <p style={{ fontWeight: 600, fontSize: '13px', marginTop: '8px' }}>Limitações:</p>
                  <ul style={{ paddingLeft: '18px', fontSize: '13px' }}>
                    {parecer.limitacoes.map((l, i) => <li key={i}>{l}</li>)}
                  </ul>
                </>
              )}
            </AccordionItem>
          </Accordion>
        </div>
      )}
    </Tile>
  )
}
