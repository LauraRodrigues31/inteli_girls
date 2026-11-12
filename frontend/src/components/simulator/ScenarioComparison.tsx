import { Tile, InlineNotification, StructuredListWrapper, StructuredListRow, StructuredListCell, StructuredListBody } from '@carbon/react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import type { GuardianResult } from '../../types'
import { ScoreProgressBar } from '../analysis/ScoreProgressBar'
import { RecommendationTag } from '../analysis/RecommendationTag'

const AGENT_LABELS: Record<string, string> = {
  mercado: 'Mercado',
  impacto_social: 'Social',
  engenharia: 'Engenharia',
  orcamento: 'Orçamento',
  pontes: 'Pontes',
}

interface ScenarioComparisonProps {
  base: GuardianResult
  parcerias: GuardianResult
}

export function ScenarioComparison({ base, parcerias }: ScenarioComparisonProps) {
  const mudou = base.recomendacao !== parcerias.recomendacao

  const chartData = Object.keys(base.pareceres).map((key) => ({
    agente: AGENT_LABELS[key] ?? key,
    Base: base.pareceres[key as keyof typeof base.pareceres]?.score ?? 0,
    Parcerias: parcerias.pareceres[key as keyof typeof parcerias.pareceres]?.score ?? 0,
  }))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Recommendation changed alert */}
      {mudou && (
        <InlineNotification
          kind="success"
          title="Recomendação mudou!"
          subtitle={`De "${base.recomendacao.replace(/_/g, ' ')}" para "${parcerias.recomendacao.replace(/_/g, ' ')}" com as parcerias.`}
          hideCloseButton
        />
      )}

      {/* Side-by-side score cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        {/* Base */}
        <Tile style={{ padding: '20px', borderTop: '4px solid #8d8d8d' }}>
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
            Cenário Base
          </p>
          <ScoreProgressBar
            score={base.score_consolidado}
            recomendacao={base.recomendacao}
            height={16}
            animate
          />
          <div style={{ marginTop: '12px' }}>
            <RecommendationTag recomendacao={base.recomendacao} size="sm" />
          </div>
        </Tile>

        {/* Parcerias */}
        <Tile style={{ padding: '20px', borderTop: '4px solid #0043ce' }}>
          <p
            style={{
              fontSize: '12px',
              fontWeight: 600,
              color: '#0043ce',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              marginBottom: '12px',
            }}
          >
            Cenário com Parcerias
          </p>
          <ScoreProgressBar
            score={parcerias.score_consolidado}
            recomendacao={parcerias.recomendacao}
            height={16}
            animate
          />
          <div style={{ marginTop: '12px' }}>
            <RecommendationTag recomendacao={parcerias.recomendacao} size="sm" />
          </div>
        </Tile>
      </div>

      {/* Key metrics table */}
      <Tile style={{ padding: '20px' }}>
        <p style={{ fontWeight: 600, marginBottom: '12px' }}>Comparativo de métricas</p>
        <StructuredListWrapper>
          <StructuredListBody>
            <StructuredListRow>
              <StructuredListCell>Score Base</StructuredListCell>
              <StructuredListCell>{base.score_consolidado} / 100</StructuredListCell>
            </StructuredListRow>
            <StructuredListRow>
              <StructuredListCell>Score com Parcerias</StructuredListCell>
              <StructuredListCell>{parcerias.score_consolidado} / 100</StructuredListCell>
            </StructuredListRow>
            <StructuredListRow>
              <StructuredListCell>Diferença</StructuredListCell>
              <StructuredListCell
                style={{
                  color:
                    parcerias.score_consolidado > base.score_consolidado
                      ? '#24a148'
                      : '#da1e28',
                  fontWeight: 700,
                }}
              >
                {parcerias.score_consolidado > base.score_consolidado ? '+' : ''}
                {parcerias.score_consolidado - base.score_consolidado}
              </StructuredListCell>
            </StructuredListRow>
            <StructuredListRow>
              <StructuredListCell>Recomendação mudou?</StructuredListCell>
              <StructuredListCell style={{ fontWeight: 700, color: mudou ? '#24a148' : '#6f6f6f' }}>
                {mudou ? 'Sim ✅' : 'Não'}
              </StructuredListCell>
            </StructuredListRow>
          </StructuredListBody>
        </StructuredListWrapper>
      </Tile>

      {/* Grouped bar chart */}
      <Tile style={{ padding: '20px' }}>
        <p style={{ fontWeight: 600, marginBottom: '16px' }}>📊 Scores por agente</p>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
            <XAxis dataKey="agente" tick={{ fontSize: 12, fontFamily: 'IBM Plex Sans, sans-serif' }} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                fontFamily: 'IBM Plex Sans, sans-serif',
                fontSize: '13px',
                border: '1px solid #e0e0e0',
                borderRadius: '4px',
              }}
            />
            <Legend />
            <Bar dataKey="Base" fill="#8d8d8d" radius={[2, 2, 0, 0]} />
            <Bar dataKey="Parcerias" fill="#0043ce" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Tile>

      <InlineNotification
        kind="info"
        title="Simulação hipotética —"
        subtitle="Os resultados são baseados em dados fictícios e parâmetros estimados. Não representam projeções reais."
        lowContrast
        hideCloseButton
      />
    </div>
  )
}
