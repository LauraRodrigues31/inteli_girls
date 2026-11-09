import React from 'react'
import { InlineNotification } from '@carbon/react'

interface DivergenceListProps {
  divergencias: string[]
}

export function DivergenceList({ divergencias }: DivergenceListProps) {
  if (!divergencias || divergencias.length === 0) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {divergencias.map((d, i) => (
        <InlineNotification
          key={i}
          kind="warning"
          title={`Divergência ${i + 1}:`}
          subtitle={d}
          lowContrast
          hideCloseButton
        />
      ))}
    </div>
  )
}
