import React, { useState } from 'react'
import { InlineNotification } from '@carbon/react'
import {
  ArrowRight,
  ShoppingCart,
  Group,
  Settings,
  Finance,
  Partnership,
  Checkmark,
  Chemistry,
  Time,
  UserMultiple,
  WarningAlt,
} from '@carbon/icons-react'
import { useNavigate } from 'react-router-dom'

// Team characters (flat illustration, same style as the pitch deck)
type Hair = 'curlyLong' | 'curly' | 'wavyLong' | 'straight' | 'curlyShort'
interface TeamMember {
  initials: string
  name: string
  hair: Hair
  hairColor: string
  skin: string
  top: string
  stripes?: boolean
  glasses?: boolean
  hoops?: boolean
}

const TEAM: TeamMember[] = [
  { initials: 'MC', name: 'Milena Castro',  hair: 'curlyLong',  hairColor: '#2a1a14', skin: '#f0c7a3', top: '#e8dac3' },
  { initials: 'LR', name: 'Laura Rodrigues', hair: 'curlyLong',  hairColor: '#2a1a14', skin: '#f0c7a3', top: '#1f2226' },
  { initials: 'GS', name: 'Gabriela Silva', hair: 'wavyLong',   hairColor: '#1d1512', skin: '#f0c7a3', top: '#9d8aab', stripes: true },
  { initials: 'TV', name: 'Thalyta Viana',  hair: 'straight',   hairColor: '#7a5238', skin: '#f0c7a3', top: '#3a2a24' },
  { initials: 'AB', name: 'Ana Beggiato',   hair: 'curlyShort', hairColor: '#2a1a14', skin: '#f0c7a3', top: '#1f2226', glasses: true, hoops: true },
]

function TeamCharacter({ member: m }: { member: TeamMember }) {
  const { hair, hairColor: hc, skin, top } = m
  return (
    <svg
      viewBox="0 0 100 130"
      width="104"
      height="135"
      role="img"
      aria-label={m.name}
    >
      <title>{m.name}</title>
      {/* Hair behind head */}
      {hair === 'curlyLong' && (
        <g fill={hc}>
          <circle cx="50" cy="30" r="24" />
          <circle cx="26" cy="44" r="10" /><circle cx="22" cy="62" r="9" /><circle cx="26" cy="80" r="8" />
          <circle cx="74" cy="44" r="10" /><circle cx="78" cy="62" r="9" /><circle cx="74" cy="80" r="8" />
        </g>
      )}
      {hair === 'wavyLong' && (
        <g fill={hc}>
          <path d="M24 40 Q22 16 50 14 Q78 16 76 40 L80 84 Q74 92 68 82 L66 50 L34 50 L32 82 Q26 92 20 84 Z" />
        </g>
      )}
      {hair === 'straight' && (
        <path d="M26 38 Q26 12 50 12 Q74 12 74 38 L76 82 L24 82 Z" fill={hc} />
      )}
      {hair === 'curlyShort' && (
        <g fill={hc}>
          <circle cx="36" cy="22" r="11" /><circle cx="50" cy="16" r="12" /><circle cx="64" cy="22" r="11" />
          <circle cx="30" cy="34" r="8" /><circle cx="70" cy="34" r="8" />
        </g>
      )}

      {/* Shoulders / top */}
      <path d="M14 130 L14 112 Q14 88 50 86 Q86 88 86 112 L86 130 Z" fill={top} />
      {m.stripes && (
        <g stroke="#fff" strokeOpacity="0.55" strokeWidth="2">
          <line x1="34" y1="92" x2="34" y2="130" /><line x1="66" y1="92" x2="66" y2="130" />
          <line x1="50" y1="96" x2="50" y2="130" />
        </g>
      )}
      {/* Neck */}
      <rect x="44" y="68" width="12" height="20" fill={skin} />
      {/* V collar */}
      <path d="M42 88 L50 100 L58 88 Z" fill={skin} />

      {/* Ears / hoops */}
      <circle cx="28" cy="52" r="4" fill={skin} />
      <circle cx="72" cy="52" r="4" fill={skin} />
      {m.hoops && (
        <g fill="none" stroke="#d9dde3" strokeWidth="2">
          <circle cx="26" cy="62" r="6" /><circle cx="74" cy="62" r="6" />
        </g>
      )}

      {/* Face */}
      <ellipse cx="50" cy="48" rx="22" ry="24" fill={skin} />

      {/* Fringe */}
      {hair === 'straight' && <path d="M28 44 Q30 22 50 22 Q70 22 72 44 Q60 32 50 34 Q40 32 28 44 Z" fill={hc} />}
      {hair === 'wavyLong' && <path d="M28 46 Q28 22 50 22 Q72 22 72 46 Q60 30 50 34 Q36 30 28 46 Z" fill={hc} />}
      {(hair === 'curlyLong') && <path d="M28 40 Q32 22 50 24 Q68 22 72 40 Q60 30 50 32 Q40 30 28 40 Z" fill={hc} />}

      {/* Eyes */}
      <circle cx="41" cy="48" r="2" fill="#2b1d17" />
      <circle cx="59" cy="48" r="2" fill="#2b1d17" />
      {/* Glasses */}
      {m.glasses && (
        <g fill="none" stroke="#b07a4a" strokeWidth="1.8">
          <circle cx="41" cy="48" r="7" /><circle cx="59" cy="48" r="7" /><line x1="48" y1="48" x2="52" y2="48" />
        </g>
      )}
      {/* Smile */}
      <path d="M42 60 Q50 67 58 60" fill="none" stroke="#2b1d17" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

const AGENTS = [
  {
    key: 'mercado',
    label: 'Mercado',
    fullLabel: 'Agente de Mercado',
    Icon: ShoppingCart,
    mandate: 'Defende o retorno financeiro',
    question: 'Vale a pena financeiramente?',
    detail: 'Analisa renda, crescimento populacional, demanda e competitividade.',
    color: '#0f62fe',
  },
  {
    key: 'social',
    label: 'Social',
    fullLabel: 'Agente de Impacto Social',
    Icon: Group,
    mandate: 'Defende escolas, saúde e inclusão',
    question: 'Quem ganha com a conexão?',
    detail: 'Conta escolas, postos de saúde e famílias sem acesso.',
    color: '#24a148',
  },
  {
    key: 'engenharia',
    label: 'Engenharia',
    fullLabel: 'Agente de Engenharia',
    Icon: Settings,
    mandate: 'Avalia a viabilidade técnica',
    question: 'Dá para construir?',
    detail: 'Distância do backbone, tipo de rede (FTTH, FWA, LEO) e prazo de obra.',
    color: '#8a3ffc',
  },
  {
    key: 'orcamento',
    label: 'Orçamento',
    fullLabel: 'Agente de Orçamento',
    Icon: Finance,
    mandate: 'Controla custo e prazo',
    question: 'Cabe no limite de custo e prazo?',
    detail: 'CAPEX, OPEX, payback e margem mensal.',
    color: '#f1c21b',
  },
  {
    key: 'pontes',
    label: 'Pontes',
    fullLabel: 'Agente de Pontes',
    Icon: Partnership,
    mandate: 'Busca clientes âncora',
    question: 'Dá para tornar a região viável?',
    detail: 'Prefeituras, escolas e postos de saúde como clientes âncora.',
    color: '#ee5396',
  },
  {
    key: 'guardiao',
    label: '🛡 Guardião',
    fullLabel: 'Guardião',
    Icon: UserMultiple,
    mandate: 'Sintetiza e decide com imparcialidade',
    question: 'O que fazemos com esta região?',
    detail: 'Recebe os 5 pareceres, resolve divergências e emite uma recomendação final — investir, pilotar, aguardar ou escalar para humano.',
    color: '#0f62fe',
  },
]

const OUTCOMES = [
  { label: 'Investir Agora', Icon: Checkmark, color: '#24a148', bg: '#defbe6', rule: 'Score ≥ 70 E orçamento ≥ 60 E engenharia ≥ 60' },
  { label: 'Realizar Piloto', Icon: Chemistry, color: '#0f62fe', bg: '#edf5ff', rule: 'Score ≥ 50, não atende critérios acima' },
  { label: 'Aguardar', Icon: Time, color: '#a16207', bg: '#fef9c3', rule: '30 ≤ Score < 50' },
  { label: 'Escalar Humano', Icon: UserMultiple, color: '#da1e28', bg: '#fff1f1', rule: 'Score < 30 OU engenharia < 20 OU orçamento < 20' },
]

// ── Interactive flow node ────────────────────────────────────────────────────
interface FlowNodeProps {
  label: string
  color: string
  isActive: boolean
  isGuardian?: boolean
  onEnter: () => void
  onLeave: () => void
  children?: React.ReactNode
}

function FlowNode({ label, color, isActive, isGuardian, onEnter, onLeave, children }: FlowNodeProps) {
  return (
    <div
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      style={{
        position: 'relative',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: isGuardian ? '10px 28px' : '8px 18px',
        borderRadius: '6px',
        border: `2px solid ${isActive ? color : isGuardian ? '#161616' : '#d0d0d0'}`,
        background: isGuardian
          ? isActive ? '#262626' : '#161616'
          : isActive ? `${color}18` : '#ffffff',
        cursor: 'default',
        userSelect: 'none',
        transition: 'all 0.18s ease',
        boxShadow: isActive ? `0 0 0 3px ${color}33` : 'none',
        minWidth: isGuardian ? '160px' : '110px',
      }}
    >
      <span style={{
        fontSize: isGuardian ? '14px' : '12px',
        fontWeight: 700,
        color: isGuardian ? '#ffffff' : isActive ? color : '#525252',
        fontFamily: 'IBM Plex Sans, sans-serif',
        whiteSpace: 'nowrap',
      }}>
        {children ?? label}
      </span>
    </div>
  )
}

export default function ComoFunciona() {
  const navigate = useNavigate()
  const [activeAgent, setActiveAgent] = useState<string | null>(null)
  const [activeOutcome, setActiveOutcome] = useState<string | null>(null)

  const activeAgentData = AGENTS.find(a => a.key === activeAgent)
  const activeOutcomeData = OUTCOMES.find(o => o.label === activeOutcome)

  return (
    <div>
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <div
        style={{
          background: 'linear-gradient(145deg, #0a0a0a 0%, #001141 50%, #0f3460 100%)',
          padding: '80px 24px 72px',
          color: '#ffffff',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Decorative IBM blue accent bar */}
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, height: '3px',
          background: 'linear-gradient(90deg, #0f62fe 0%, #4589ff 50%, #0f62fe 100%)',
        }} />

        {/* Background subtle grid */}
        <div style={{
          position: 'absolute', inset: 0, opacity: 0.04,
          backgroundImage: 'repeating-linear-gradient(0deg, #fff 0px, #fff 1px, transparent 1px, transparent 48px), repeating-linear-gradient(90deg, #fff 0px, #fff 1px, transparent 1px, transparent 48px)',
          pointerEvents: 'none',
        }} />

        {/* Two-column layout: left = copy, right = team avatars */}
        <div style={{
          maxWidth: '960px', margin: '0 auto', position: 'relative',
          display: 'grid', gridTemplateColumns: '1fr auto', gap: '48px', alignItems: 'center',
        }}>
          {/* Left column */}
          <div>
            <p style={{
              fontSize: '11px', fontWeight: 600, letterSpacing: '0.12em',
              color: '#4589ff', textTransform: 'uppercase', marginBottom: '20px',
            }}>
              IBM SkillsBuild · Trilha 3 · 2024
            </p>

            <h1 style={{
              fontSize: 'clamp(40px, 6vw, 68px)', fontWeight: 700,
              lineHeight: 1.05, marginBottom: '12px',
              fontFamily: 'IBM Plex Sans, sans-serif', letterSpacing: '-0.02em',
            }}>
              Conecta<br />
              <span style={{ color: '#4589ff' }}>Conselho</span>
            </h1>

            <p style={{ fontSize: '20px', color: '#a8c7fa', lineHeight: 1.5, marginBottom: '8px', fontWeight: 300 }}>
              Cinco vozes especializadas.
            </p>
            <p style={{ fontSize: '20px', color: '#ffffff', lineHeight: 1.5, marginBottom: '36px', fontWeight: 600 }}>
              Uma decisão mais justa.
            </p>

            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              {/* Primary IBM blue button */}
              <button
                onClick={() => navigate('/analise')}
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: '8px',
                  padding: '14px 24px', fontSize: '16px', fontWeight: 600,
                  fontFamily: 'IBM Plex Sans, sans-serif', cursor: 'pointer',
                  background: '#0f62fe', color: '#ffffff',
                  border: '2px solid #0f62fe', borderRadius: '0',
                  transition: 'background 0.15s',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = '#0353e9')}
                onMouseLeave={e => (e.currentTarget.style.background = '#0f62fe')}
              >
                Analisar Região
                <ArrowRight size={20} aria-hidden />
              </button>

              {/* Secondary outlined button — always white border visible */}
              <button
                onClick={() => navigate('/analise?demo=central')}
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: '8px',
                  padding: '14px 24px', fontSize: '16px', fontWeight: 600,
                  fontFamily: 'IBM Plex Sans, sans-serif', cursor: 'pointer',
                  background: 'transparent', color: '#ffffff',
                  border: '2px solid rgba(255,255,255,0.7)', borderRadius: '0',
                  transition: 'border-color 0.15s, background 0.15s',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = '#ffffff'
                  e.currentTarget.style.background = 'rgba(255,255,255,0.08)'
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = 'rgba(255,255,255,0.7)'
                  e.currentTarget.style.background = 'transparent'
                }}
              >
                Ver Demo (Central)
              </button>
            </div>
          </div>

          {/* Right column — team illustrated characters (no circles, no names) */}
          <div
            role="group"
            aria-label="Equipe Bob Girls"
            style={{
              display: 'flex', flexWrap: 'wrap', gap: '4px 8px',
              alignItems: 'flex-end', justifyContent: 'center', maxWidth: '360px',
            }}
          >
            {TEAM.map((m) => (
              <TeamCharacter key={m.initials} member={m} />
            ))}
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

      {/* ── Interactive flow diagram ───────────────────────────────────── */}
      <div style={{ background: '#f4f4f4', padding: '56px 24px' }}>
        <div style={{ maxWidth: '860px', margin: '0 auto' }}>

          {/* Header */}
          <div style={{ textAlign: 'center', marginBottom: '48px' }}>
            <h2 style={{ fontSize: '26px', fontWeight: 700, color: '#161616', marginBottom: '8px' }}>
              Como o sistema funciona
            </h2>
            <p style={{ fontSize: '15px', color: '#6f6f6f', maxWidth: '500px', margin: '0 auto' }}>
              Passe o mouse sobre cada agente para ver seu mandato e a pergunta que ele responde.
            </p>
          </div>

          {/* ── Flow layout ── */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0' }}>

            {/* Row 1: 5 agents */}
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', justifyContent: 'center' }}>
              {AGENTS.map((agent) => (
                <FlowNode
                  key={agent.key}
                  label={agent.label}
                  color={agent.color}
                  isActive={activeAgent === agent.key}
                  onEnter={() => { setActiveAgent(agent.key); setActiveOutcome(null) }}
                  onLeave={() => setActiveAgent(null)}
                />
              ))}
            </div>

            {/* Connector lines SVG */}
            <svg viewBox="0 0 600 70" style={{ width: '100%', maxWidth: '700px', height: '60px', overflow: 'visible' }}>
              {AGENTS.map((_, i) => {
                const x = (i / 4) * 540 + 30
                return (
                  <line key={i}
                    x1={x} y1={5} x2={300} y2={65}
                    stroke={activeAgent === AGENTS[i].key ? AGENTS[i].color : '#c6c6c6'}
                    strokeWidth={activeAgent === AGENTS[i].key ? 2 : 1}
                    strokeDasharray="5 3"
                    style={{ transition: 'stroke 0.2s' }}
                  />
                )
              })}
            </svg>

            {/* Row 2: Guardian — uses same AGENTS entry for tooltip */}
            <FlowNode
              label="🛡 Guardião"
              color="#0f62fe"
              isActive={activeAgent === 'guardiao'}
              isGuardian
              onEnter={() => { setActiveAgent('guardiao'); setActiveOutcome(null) }}
              onLeave={() => setActiveAgent(null)}
            />

            {/* Connector lines SVG */}
            <svg viewBox="0 0 600 70" style={{ width: '100%', maxWidth: '700px', height: '60px', overflow: 'visible' }}>
              {OUTCOMES.map((o, i) => {
                const x = (i / 3) * 540 + 30
                return (
                  <line key={i}
                    x1={300} y1={5} x2={x} y2={65}
                    stroke={activeOutcome === o.label ? o.color : '#c6c6c6'}
                    strokeWidth={activeOutcome === o.label ? 2 : 1}
                    style={{ transition: 'stroke 0.2s' }}
                  />
                )
              })}
            </svg>

            {/* Row 3: 4 outcomes */}
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', justifyContent: 'center' }}>
              {OUTCOMES.map((o) => (
                <FlowNode
                  key={o.label}
                  label={o.label}
                  color={o.color}
                  isActive={activeOutcome === o.label}
                  onEnter={() => { setActiveOutcome(o.label); setActiveAgent(null) }}
                  onLeave={() => setActiveOutcome(null)}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <o.Icon size={13} aria-hidden />
                    {o.label}
                  </span>
                </FlowNode>
              ))}
            </div>
          </div>

          {/* ── Info panel — appears on hover ── */}
          <div style={{
            marginTop: '40px',
            minHeight: '120px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            {/* Agent tooltip */}
            {activeAgentData && (
              <div style={{
                background: '#ffffff',
                border: `2px solid ${activeAgentData.color}`,
                borderRadius: '8px',
                padding: '24px 28px',
                maxWidth: '560px',
                width: '100%',
                boxShadow: `0 4px 24px ${activeAgentData.color}22`,
                display: 'flex',
                gap: '20px',
                alignItems: 'flex-start',
                animation: 'fadeIn 0.18s ease',
              }}>
                <div style={{
                  width: '44px', height: '44px', borderRadius: '8px', flexShrink: 0,
                  background: `${activeAgentData.color}18`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {activeAgentData.key === 'guardiao'
                    ? <span style={{ fontSize: '22px' }}>🛡</span>
                    : <activeAgentData.Icon size={22} style={{ color: activeAgentData.color }} />
                  }
                </div>
                <div>
                  <p style={{ fontWeight: 700, fontSize: '16px', color: '#161616', margin: '0 0 4px' }}>
                    {activeAgentData.key === 'guardiao' ? 'Guardião' : activeAgentData.fullLabel}
                  </p>
                  <p style={{ fontSize: '13px', color: activeAgentData.color, fontWeight: 600, margin: '0 0 8px' }}>
                    {activeAgentData.mandate}
                  </p>
                  <p style={{ fontSize: '14px', color: '#525252', margin: '0 0 6px', lineHeight: 1.6 }}>
                    {activeAgentData.detail}
                  </p>
                  <p style={{ fontSize: '14px', color: '#161616', fontWeight: 600, margin: 0 }}>
                    → {activeAgentData.question}
                  </p>
                </div>
              </div>
            )}

            {/* Outcome tooltip */}
            {activeOutcomeData && (
              <div style={{
                background: activeOutcomeData.bg,
                border: `2px solid ${activeOutcomeData.color}`,
                borderRadius: '8px',
                padding: '24px 28px',
                maxWidth: '560px',
                width: '100%',
                boxShadow: `0 4px 24px ${activeOutcomeData.color}22`,
                display: 'flex',
                gap: '20px',
                alignItems: 'flex-start',
                animation: 'fadeIn 0.18s ease',
              }}>
                <div style={{
                  width: '44px', height: '44px', borderRadius: '8px', flexShrink: 0,
                  background: `${activeOutcomeData.color}22`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <activeOutcomeData.Icon size={22} style={{ color: activeOutcomeData.color }} />
                </div>
                <div>
                  <p style={{ fontWeight: 700, fontSize: '16px', color: activeOutcomeData.color, margin: '0 0 8px' }}>
                    {activeOutcomeData.label}
                  </p>
                  <p style={{ fontSize: '13px', color: '#525252', lineHeight: 1.6, margin: 0 }}>
                    <strong>Regra:</strong> {activeOutcomeData.rule}
                  </p>
                </div>
              </div>
            )}

            {/* Placeholder when nothing is hovered */}
            {!activeAgentData && !activeOutcomeData && (
              <p style={{ fontSize: '13px', color: '#8d8d8d', textAlign: 'center' }}>
                ↑ Passe o mouse sobre um agente ou resultado para ver os detalhes
              </p>
            )}
          </div>
        </div>
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
