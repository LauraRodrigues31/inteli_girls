import { Tag } from '@carbon/react'
import {
  Checkmark,
  Chemistry,
  Time,
  UserMultiple,
} from '@carbon/icons-react'
import type { Recomendacao } from '../../types'

// Carbon Tag accepts these type strings — cast via 'as' to avoid union type mismatch
type TagType = 'green' | 'blue' | 'warm-gray' | 'red' | 'gray' | 'teal' | 'cyan' | 'purple' | 'cool-gray' | 'high-contrast' | 'outline'

const CONFIG: Record<Recomendacao, { label: string; type: TagType; Icon: React.ElementType }> = {
  investir_agora:  { label: 'Investir Agora',      type: 'green',     Icon: Checkmark    },
  realizar_piloto: { label: 'Realizar Piloto',      type: 'blue',      Icon: Chemistry    },
  aguardar:        { label: 'Aguardar',             type: 'warm-gray', Icon: Time         },
  escalar_humano:  { label: 'Escalar para Humano',  type: 'red',       Icon: UserMultiple },
}

interface RecommendationTagProps {
  recomendacao: Recomendacao
  size?: 'sm' | 'md' | 'lg'
}

export function RecommendationTag({ recomendacao, size = 'md' }: RecommendationTagProps) {
  const { label, type, Icon } = CONFIG[recomendacao] ?? CONFIG['aguardar']

  const fontSize  = size === 'lg' ? '16px' : size === 'sm' ? '12px' : '14px'
  const padding   = size === 'lg' ? '10px 18px' : size === 'sm' ? '2px 8px' : '6px 12px'
  const iconSize  = size === 'lg' ? 20 : 16

  return (
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    <Tag type={type as any} style={{ fontSize, padding, fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '6px', borderRadius: '4px' }}>
      <Icon size={iconSize} aria-hidden />
      {label}
    </Tag>
  )
}
