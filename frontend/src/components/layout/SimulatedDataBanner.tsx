import React from 'react'
import { InlineNotification } from '@carbon/react'

export function SimulatedDataBanner() {
  return (
    <div
      style={{
        position: 'sticky',
        top: '48px',
        zIndex: 999,
        width: '100%',
      }}
    >
      <InlineNotification
        kind="warning"
        title="Dados Simulados —"
        subtitle="Todos os indicadores são fictícios e não representam regiões, operadoras ou instituições reais."
        lowContrast={false}
        hideCloseButton
        style={{ maxWidth: '100%', borderRadius: 0 }}
      />
    </div>
  )
}
