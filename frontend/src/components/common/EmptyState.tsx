import React from 'react'
import { Tile } from '@carbon/react'
import { Lightning } from '@carbon/icons-react'

interface EmptyStateProps {
  title?: string
  subtitle?: string
  icon?: React.ReactNode
}

export function EmptyState({
  title = 'Nenhum dado disponível',
  subtitle = 'Execute o Conselho para ver os resultados aqui.',
  icon,
}: EmptyStateProps) {
  return (
    <Tile
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 24px',
        textAlign: 'center',
        gap: '12px',
        minHeight: '200px',
      }}
    >
      <div style={{ color: '#8d8d8d' }}>
        {icon ?? <Lightning size={40} />}
      </div>
      <p style={{ fontSize: '16px', fontWeight: 600, color: '#161616' }}>{title}</p>
      <p style={{ fontSize: '14px', color: '#6f6f6f' }}>{subtitle}</p>
    </Tile>
  )
}
