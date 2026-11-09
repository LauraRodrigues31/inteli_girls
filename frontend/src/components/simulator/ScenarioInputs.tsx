import React from 'react'
import {
  Select,
  SelectItem,
  Slider,
  RadioButtonGroup,
  RadioButton,
  Button,
  Tile,
  InlineNotification,
} from '@carbon/react'
import { PlayFilled } from '@carbon/icons-react'
import type { RegionSummary, SimulatorParams } from '../../types'

interface ScenarioInputsProps {
  regioes: RegionSummary[]
  params: SimulatorParams
  loading: boolean
  onChange: (params: SimulatorParams) => void
  onSimulate: () => void
  onQuickFill: () => void
}

export function ScenarioInputs({
  regioes,
  params,
  loading,
  onChange,
  onSimulate,
  onQuickFill,
}: ScenarioInputsProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <Tile style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>
          Configurar Simulação
        </h3>

        {/* Region selector */}
        <Select
          id="sim-regiao"
          labelText="Região"
          value={params.regiao_id}
          onChange={(e) => onChange({ ...params, regiao_id: e.target.value })}
        >
          {regioes.map((r) => (
            <SelectItem key={r.id} value={r.id} text={r.nome} />
          ))}
        </Select>

        <div style={{ marginTop: '20px' }}>
          <p
            style={{
              fontSize: '12px',
              fontWeight: 600,
              color: '#6f6f6f',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              marginBottom: '12px',
            }}
          >
            Cenário com Parcerias
          </p>

          <Slider
            id="sim-capex"
            labelText={`Redução de CAPEX por parcerias: ${params.reducao_capex_pct}%`}
            min={0}
            max={50}
            step={1}
            value={params.reducao_capex_pct}
            onChange={({ value }) => onChange({ ...params, reducao_capex_pct: value })}
          />

          <div style={{ marginTop: '16px' }}>
            <Slider
              id="sim-ancoras"
              labelText={`Instituições âncora adicionais: +${params.ancoras_adicionais}`}
              min={0}
              max={10}
              step={1}
              value={params.ancoras_adicionais}
              onChange={({ value }) => onChange({ ...params, ancoras_adicionais: value })}
            />
          </div>

          <div style={{ marginTop: '16px' }}>
            <p style={{ fontSize: '14px', fontWeight: 500, marginBottom: '8px' }}>
              Maturidade das parcerias
            </p>
            <RadioButtonGroup
              legendText=""
              name="maturidade"
              valueSelected={params.maturidade_parcerias}
              onChange={(value) =>
                onChange({
                  ...params,
                  maturidade_parcerias: value as SimulatorParams['maturidade_parcerias'],
                })
              }
              orientation="horizontal"
            >
              <RadioButton labelText="Baixa" value="baixa" id="mat-baixa" />
              <RadioButton labelText="Média" value="média" id="mat-media" />
              <RadioButton labelText="Alta" value="alta" id="mat-alta" />
            </RadioButtonGroup>
          </div>
        </div>
      </Tile>

      {/* Quick-fill */}
      <InlineNotification
        kind="info"
        title="Atalho:"
        subtitle='Preenche automaticamente "Esperança + parcerias" — o caso que mostra score 44 → 50.'
        lowContrast
        hideCloseButton
        actions={
          <Button kind="ghost" size="sm" onClick={onQuickFill}>
            ▶️ História Esperança + parcerias
          </Button>
        }
      />

      {/* Simulate button */}
      <Button
        renderIcon={PlayFilled}
        iconDescription="Simular"
        onClick={onSimulate}
        disabled={loading || !params.regiao_id}
        style={{ width: '100%' }}
      >
        {loading ? 'Simulando...' : '▶ Simular'}
      </Button>
    </div>
  )
}
