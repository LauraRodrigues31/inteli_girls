import React from 'react'
import {
  Button,
  Grid,
  Column,
  Tile,
  Tag,
  InlineNotification,
} from '@carbon/react'
import {
  ArrowRight,
  ShoppingCart,
  Group,
  Settings,
  Finance,
  Partnership,
  DocumentProtected,
  Checkmark,
  Chemistry,
  Time,
  UserMultiple,
  WarningAlt,
} from '@carbon/icons-react'
import { useNavigate } from 'react-router-dom'

const AGENTS = [
  {
    key: 'mercado',
    label: 'Agente de Mercado',
    Icon: ShoppingCart,
    mandate: 'Defende o retorno financeiro',
    question: 'Vale a pena financeiramente?',
    color: '#0043ce',
  },
  {
    key: 'social',
    label: 'Agente de Impacto Social',
    Icon: Group,
    mandate: 'Defende escolas, saúde e inclusão',
    question: 'Quem ganha com a conexão?',
    color: '#24a148',
  },
  {
    key: 'engenharia',
    label: 'Agente de Engenharia',
    Icon: Settings,
    mandate: 'Avalia a viabilidade técnica',
    question: 'Dá para construir?',
    color: '#8a3ffc',
  },
  {
    key: 'orcamento',
    label: 'Agente de Orçamento',
    Icon: Finance,
    mandate: 'Controla custo e prazo',
    question: 'Cabe no limite de custo e prazo?',
    color: '#f1c21b',
  },
  {
    key: 'pontes',
    label: 'Agente de Pontes',
    Icon: Partnership,
    mandate: 'Busca clientes âncora',
    question: 'Dá para tornar a região viável?',
    color: '#ff7eb6',
  },
  {
    key: 'guardiao',
    label: 'Guardião',
    Icon: DocumentProtected,
    mandate: 'Sintetiza e decide',
    question: 'O que fazemos?',
    color: '#da1e28',
  },
]

const OUTCOMES = [
  {
    recomendacao: 'Investir Agora',
    icon: Checkmark,
    color: '#24a148',
    bg: '#defbe6',
    rule: 'Score ≥ 70 E orçamento ≥ 60 E engenharia ≥ 60',
  },
  {
    recomendacao: 'Realizar Piloto',
    icon: Chemistry,
    color: '#0043ce',
    bg: '#edf5ff',
    rule: 'Score ≥ 50, não atende critérios acima',
  },
  {
    recomendacao: 'Aguardar',
    icon: Time,
    color: '#a16207',
    bg: '#fef9c3',
    rule: '30 ≤ Score < 50',
  },
  {
    recomendacao: 'Escalar a Humano',
    icon: UserMultiple,
    color: '#da1e28',
    bg: '#fff1f1',
    rule: 'Score < 30 OU engenharia < 20 OU orçamento < 20 OU confiança baixa',
  },
]

export default function ComoFunciona() {
  const navigate = useNavigate()

  return (
    <div>
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <div
        style={{
          background: 'linear-gradient(135deg, #161616 0%, #262626 100%)',
          padding: '72px 24px',
          color: '#ffffff',
        }}
      >
        <div style={{ maxWidth: '900px', margin: '0 auto' }}>
          <Tag type="blue" size="sm" style={{ marginBottom: '16px' }}>
            IBM SkillsBuild · Trilha 3 · Telecomunicações Inteligentes
          </Tag>
          <h1
            style={{
              fontSize: 'clamp(32px, 5vw, 56px)',
              fontWeight: 700,
              lineHeight: 1.15,
              marginBottom: '16px',
              fontFamily: 'IBM Plex Sans, sans-serif',
            }}
          >
            Conecta Conselho
          </h1>
          <p
            style={{
              fontSize: '18px',
              color: '#c6c6c6',
              maxWidth: '600px',
              lineHeight: 1.7,
              marginBottom: '32px',
            }}
          >
            Sistema multiagente de apoio à decisão que reúne cinco perspectivas
            especializadas para que <strong style={{ color: '#fff' }}>nenhuma decisão de
            expansão de conectividade seja tomada só pelo lucro.</strong>
          </p>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <Button
              kind="primary"
              renderIcon={ArrowRight}
              onClick={() => navigate('/analise')}
            >
              Analisar Região
            </Button>
            <Button
              kind="tertiary"
              onClick={() => navigate('/analise?demo=central')}
              style={{ color: '#fff', borderColor: '#fff' }}
            >
              Ver Demo (Central)
            </Button>
          </div>
        </div>
      </div>

      {/* ── Simulated data warning ─────────────────────────────────────── */}
      <div style={{ maxWidth: '900px', margin: '24px auto 0', padding: '0 24px' }}>
        <InlineNotification
          kind="warning"
          title="Dados Simulados —"
          subtitle="Todos os indicadores são fictícios e criados exclusivamente para fins de demonstração."
          hideCloseButton
          lowContrast
        />
      </div>

      {/* ── How it works ──────────────────────────────────────────────── */}
      <div style={{ maxWidth: '900px', margin: '48px auto', padding: '0 24px' }}>
        <h2
          style={{
            fontSize: '24px',
            fontWeight: 700,
            marginBottom: '8px',
            color: '#161616',
          }}
        >
          Como o sistema funciona
        </h2>
        <p style={{ color: '#6f6f6f', marginBottom: '28px', fontSize: '15px' }}>
          Cada agente defende um ponto de vista diferente de propósito, para que nenhuma
          análise seja unilateral.
        </p>

        <Grid narrow>
          {AGENTS.map((agent) => {
            const { Icon } = agent
            return (
              <Column key={agent.key} sm={4} md={4} lg={8}>
                <Tile
                  style={{
                    padding: '24px',
                    borderTop: `4px solid ${agent.color}`,
                    height: '100%',
                    marginBottom: '16px',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      marginBottom: '10px',
                    }}
                  >
                    <Icon size={24} style={{ color: agent.color }} aria-hidden />
                    <p style={{ fontWeight: 700, fontSize: '15px' }}>{agent.label}</p>
                  </div>
                  <p style={{ fontSize: '13px', color: '#525252', marginBottom: '6px' }}>
                    <em>{agent.mandate}</em>
                  </p>
                  <p style={{ fontSize: '14px', color: '#161616', fontWeight: 500 }}>
                    → {agent.question}
                  </p>
                </Tile>
              </Column>
            )
          })}
        </Grid>
      </div>

      {/* ── Flow diagram (SVG) ─────────────────────────────────────────── */}
      <div
        style={{
          background: '#f4f4f4',
          padding: '48px 24px',
        }}
      >
        <div style={{ maxWidth: '700px', margin: '0 auto', textAlign: 'center' }}>
          <h2
            style={{ fontSize: '22px', fontWeight: 700, marginBottom: '32px', color: '#161616' }}
          >
            Fluxo de decisão
          </h2>
          <svg
            viewBox="0 0 600 300"
            style={{ width: '100%', maxWidth: '600px', fontFamily: 'IBM Plex Sans, sans-serif' }}
            aria-label="Fluxo multiagente do Conecta Conselho"
          >
            {/* 5 Agent boxes */}
            {['Mercado', 'Social', 'Engenharia', 'Orçamento', 'Pontes'].map((name, i) => (
              <g key={name}>
                <rect x={i * 110 + 5} y={20} width={100} height={36} rx={4}
                  fill="#edf5ff" stroke="#0043ce" strokeWidth={1.5} />
                <text x={i * 110 + 55} y={43} textAnchor="middle" fontSize={11} fill="#0043ce" fontWeight={600}>
                  {name}
                </text>
                <line x1={i * 110 + 55} y1={56} x2={300} y2={130}
                  stroke="#c6c6c6" strokeWidth={1} strokeDasharray="4 2" />
              </g>
            ))}
            {/* Guardiao */}
            <rect x={210} y={130} width={180} height={44} rx={4}
              fill="#161616" stroke="#0043ce" strokeWidth={2} />
            <text x={300} y={157} textAnchor="middle" fontSize={13} fill="#ffffff" fontWeight={700}>
              🛡 Guardião
            </text>
            {/* 4 Outcomes */}
            {[
              { label: 'Investir Agora', color: '#24a148', x: 20, },
              { label: 'Realizar Piloto', color: '#0043ce', x: 160 },
              { label: 'Aguardar', color: '#a16207', x: 320 },
              { label: 'Escalar Humano', color: '#da1e28', x: 460 },
            ].map((o) => (
              <g key={o.label}>
                <line x1={300} y1={174} x2={o.x + 60} y2={232}
                  stroke={o.color} strokeWidth={1.5} />
                <rect x={o.x} y={232} width={120} height={36} rx={4}
                  fill="white" stroke={o.color} strokeWidth={2} />
                <text x={o.x + 60} y={255} textAnchor="middle" fontSize={10} fill={o.color} fontWeight={600}>
                  {o.label}
                </text>
              </g>
            ))}
          </svg>
        </div>
      </div>

      {/* ── 4 Outcomes ────────────────────────────────────────────────── */}
      <div style={{ maxWidth: '900px', margin: '48px auto', padding: '0 24px' }}>
        <h2 style={{ fontSize: '22px', fontWeight: 700, marginBottom: '24px', color: '#161616' }}>
          Critérios de decisão
        </h2>
        <Grid narrow>
          {OUTCOMES.map((o) => {
            const { icon: Icon } = o
            return (
              <Column key={o.recomendacao} sm={4} md={4} lg={8}>
                <Tile
                  style={{
                    padding: '20px',
                    background: o.bg,
                    borderLeft: `4px solid ${o.color}`,
                    marginBottom: '16px',
                    height: '100%',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <Icon size={20} style={{ color: o.color }} aria-hidden />
                    <p style={{ fontWeight: 700, fontSize: '15px', color: o.color }}>
                      {o.recomendacao}
                    </p>
                  </div>
                  <p style={{ fontSize: '13px', color: '#525252', lineHeight: 1.6 }}>{o.rule}</p>
                </Tile>
              </Column>
            )
          })}
        </Grid>
      </div>

      {/* ── About ─────────────────────────────────────────────────────── */}
      <div
        style={{
          background: '#161616',
          color: '#c6c6c6',
          padding: '48px 24px',
        }}
      >
        <div style={{ maxWidth: '700px', margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <WarningAlt size={20} style={{ color: '#f1c21b' }} />
            <p style={{ color: '#f1c21b', fontWeight: 600 }}>
              Todos os dados são 100% simulados e fictícios.
            </p>
          </div>
          <p style={{ lineHeight: 1.7, marginBottom: '16px', fontSize: '14px' }}>
            O Conecta Conselho foi desenvolvido na trilha de <strong style={{ color: '#fff' }}>
            Telecomunicações Inteligentes com Fundação Telefônica</strong> do{' '}
            <strong style={{ color: '#fff' }}>IBM AI Experiential Learning Lab · IBM SkillsBuild</strong>.
            O sistema <em>apoia</em> a triagem de oportunidades — não autoriza obras,
            não calcula CAPEX executivo e não substitui análise de campo.
          </p>
          <p style={{ fontSize: '13px', color: '#8d8d8d' }}>
            Equipe: Laura Rodrigues · Ana Beggiato · Milena Castro · Gabriela Silva · Thalyta Viana
          </p>
        </div>
      </div>
    </div>
  )
}
