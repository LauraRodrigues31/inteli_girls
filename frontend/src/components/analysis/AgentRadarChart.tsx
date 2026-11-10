import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import type { GuardianPaeceres } from '../../types'

interface AgentRadarChartProps {
  pareceres: GuardianPaeceres
}

const AGENT_LABELS: Record<string, string> = {
  mercado: 'Mercado',
  impacto_social: 'Social',
  engenharia: 'Engenharia',
  orcamento: 'Orçamento',
  pontes: 'Pontes',
}

export function AgentRadarChart({ pareceres }: AgentRadarChartProps) {
  const data = Object.entries(pareceres).map(([key, p]) => ({
    agente: AGENT_LABELS[key] ?? key,
    score: p.score ?? 0,
  }))

  return (
    <div style={{ width: '100%', height: 280 }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
          <PolarGrid stroke="#e0e0e0" />
          <PolarAngleAxis
            dataKey="agente"
            tick={{ fontSize: 12, fill: '#525252', fontFamily: 'IBM Plex Sans, sans-serif' }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fontSize: 10, fill: '#8d8d8d' }}
            tickCount={6}
          />
          <Radar
            name="Score"
            dataKey="score"
            stroke="#0043ce"
            fill="#0043ce"
            fillOpacity={0.25}
            strokeWidth={2}
          />
          <Tooltip
            formatter={(value: number) => [`${value} / 100`, 'Score']}
            contentStyle={{
              fontFamily: 'IBM Plex Sans, sans-serif',
              fontSize: '13px',
              border: '1px solid #e0e0e0',
              borderRadius: '4px',
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
