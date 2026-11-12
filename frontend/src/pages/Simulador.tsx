import { useEffect, useState } from 'react'
import { Grid, Column, InlineLoading, Tile } from '@carbon/react'
import { useApp } from '../context/AppContext'
import { listarRegioes, simularCenario } from '../api/client'
import type { GuardianResult, SimulatorParams } from '../types'
import { ScenarioInputs } from '../components/simulator/ScenarioInputs'
import { ScenarioComparison } from '../components/simulator/ScenarioComparison'
import { EmptyState } from '../components/common/EmptyState'

const DEFAULT_PARAMS: SimulatorParams = {
  regiao_id: '',
  reducao_capex_pct: 10,
  ancoras_adicionais: 2,
  maturidade_parcerias: 'média',
}

const ESPERANCA_PARAMS: SimulatorParams = {
  regiao_id: 'esperanca',
  reducao_capex_pct: 28,
  ancoras_adicionais: 4,
  maturidade_parcerias: 'média',
}

export default function Simulador() {
  const { state, setRegioes, addToast } = useApp()
  const [params, setParams] = useState<SimulatorParams>(DEFAULT_PARAMS)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{ base: GuardianResult; parcerias: GuardianResult } | null>(null)

  useEffect(() => {
    if (state.regioes.length === 0) {
      listarRegioes()
        .then((data) => {
          setRegioes(data)
          setParams((p) => ({ ...p, regiao_id: p.regiao_id || data[0]?.id || '' }))
        })
        .catch(() =>
          addToast({ kind: 'error', title: 'Erro ao carregar regiões' }),
        )
    } else if (!params.regiao_id) {
      setParams((p) => ({ ...p, regiao_id: state.regioes[0]?.id ?? '' }))
    }
  }, [state.regioes])

  async function handleSimulate() {
    if (!params.regiao_id) return
    setLoading(true)
    setResult(null)
    try {
      const data = await simularCenario(params)
      setResult(data)
    } catch {
      addToast({
        kind: 'error',
        title: 'Erro na simulação',
        subtitle: 'Verifique se o backend está rodando.',
      })
    } finally {
      setLoading(false)
    }
  }

  function handleQuickFill() {
    setParams(ESPERANCA_PARAMS)
  }

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#161616', marginBottom: '4px' }}>
          Simulador de Cenários
        </h1>
        <p style={{ color: '#6f6f6f', fontSize: '14px' }}>
          Explore o impacto de parcerias institucionais na viabilidade de uma região.
        </p>
      </div>

      <Grid narrow>
        <Column sm={4} md={4} lg={6}>
          <ScenarioInputs
            regioes={state.regioes}
            params={params}
            loading={loading}
            onChange={setParams}
            onSimulate={handleSimulate}
            onQuickFill={handleQuickFill}
          />
        </Column>

        <Column sm={4} md={4} lg={10}>
          {loading ? (
            <Tile style={{ padding: '48px', textAlign: 'center' }}>
              <InlineLoading description="Simulando cenários base e com parcerias..." />
            </Tile>
          ) : result ? (
            <ScenarioComparison base={result.base} parcerias={result.parcerias} />
          ) : (
            <EmptyState
              title="Configure e simule"
              subtitle="Ajuste os parâmetros de parceria à esquerda e clique em ▶ Simular para comparar os cenários."
            />
          )}
        </Column>
      </Grid>
    </div>
  )
}
