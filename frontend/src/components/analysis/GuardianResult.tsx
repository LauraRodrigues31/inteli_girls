import {
  Tile,
  Accordion,
  AccordionItem,
  Button,
  InlineNotification,
  Tag,
} from '@carbon/react'
import { Download } from '@carbon/icons-react'
import type { GuardianResult } from '../../types'
import { ScoreProgressBar } from './ScoreProgressBar'
import { RecommendationTag } from './RecommendationTag'
import { AgentCard } from './AgentCard'
import { AgentRadarChart } from './AgentRadarChart'
import { DivergenceList } from './DivergenceList'

interface GuardianResultPanelProps {
  resultado: GuardianResult
}

function downloadJSON(resultado: GuardianResult) {
  const blob = new Blob([JSON.stringify(resultado, null, 2)], {
    type: 'application/json',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `relatorio_${resultado.regiao_id}.json`
  a.click()
  URL.revokeObjectURL(url)
}

export function GuardianResultPanel({ resultado }: GuardianResultPanelProps) {
  const isIncomplete = resultado.status === 'analise_incompleta'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* ── Score + Recommendation ── */}
      <Tile style={{ padding: '24px' }}>
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
          Recomendação do Guardião — {resultado.regiao_nome}
        </p>

        {isIncomplete ? (
          <InlineNotification
            kind="error"
            title="Análise incompleta"
            subtitle="Não foi possível emitir recomendação. Verifique os agentes com falha."
            hideCloseButton
          />
        ) : (
          <>
            <div style={{ marginBottom: '20px' }}>
              <ScoreProgressBar
                score={resultado.score_consolidado}
                recomendacao={resultado.recomendacao}
                label="Score Consolidado"
                height={24}
                animate
              />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
              <RecommendationTag recomendacao={resultado.recomendacao} size="lg" />
              <Tag type="gray" size="sm">
                {resultado.fonte === 'nuvem' ? '☁️ IBM watsonx Orchestrate' : '💻 Local'}
              </Tag>
              {resultado.tempo_analise_segundos !== undefined && (
                <Tag type="gray" size="sm">
                  ⏱ {resultado.tempo_analise_segundos}s
                </Tag>
              )}
            </div>
          </>
        )}
      </Tile>

      {/* ── Priority Alert ── */}
      {resultado.atencao_prioritaria && (
        <InlineNotification
          kind="error"
          title="🚨 Atenção Prioritária"
          subtitle={
            resultado.pontos_criticos?.length > 0
              ? resultado.pontos_criticos.join(' • ')
              : 'Esta região requer cuidado especial antes de qualquer decisão.'
          }
          hideCloseButton
        />
      )}

      {/* ── Justificativa ── */}
      {resultado.justificativa_consolidada && (
        <Tile style={{ padding: '20px', background: '#edf5ff', borderLeft: '4px solid #0043ce' }}>
          <p style={{ fontSize: '14px', lineHeight: 1.7, color: '#161616', margin: 0 }}>
            {resultado.justificativa_consolidada}
          </p>
        </Tile>
      )}

      {/* ── Motivos / Caminhos (aguardar) ── */}
      {resultado.recomendacao === 'aguardar' && (
        <Accordion>
          {resultado.motivos?.length > 0 && (
            <AccordionItem title="🔍 Por que aguardar" open>
              <ul style={{ paddingLeft: '18px', fontSize: '14px', lineHeight: 1.8 }}>
                {resultado.motivos.map((m, i) => (
                  <li key={i}>{m}</li>
                ))}
              </ul>
            </AccordionItem>
          )}
          {resultado.caminhos?.length > 0 && (
            <AccordionItem title="🛤️ Caminhos para viabilizar" open>
              <ul style={{ paddingLeft: '18px', fontSize: '14px', lineHeight: 1.8 }}>
                {resultado.caminhos.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </AccordionItem>
          )}
        </Accordion>
      )}

      {/* ── Divergências ── */}
      {resultado.divergencias?.length > 0 && (
        <Accordion>
          <AccordionItem title={`⚡ Divergências identificadas (${resultado.divergencias.length})`}>
            <DivergenceList divergencias={resultado.divergencias} />
          </AccordionItem>
        </Accordion>
      )}

      {/* ── Principais Riscos ── */}
      {resultado.principais_riscos?.length > 0 && (
        <Tile style={{ padding: '20px' }}>
          <p style={{ fontWeight: 600, marginBottom: '8px' }}>⚠️ Principais Riscos</p>
          <ul style={{ paddingLeft: '18px', fontSize: '13px', lineHeight: 1.8 }}>
            {resultado.principais_riscos.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </Tile>
      )}

      {/* ── 5 Agent Cards ── */}
      <div>
        <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px', color: '#161616' }}>
          5 Agentes Especialistas
        </h3>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
            gap: '12px',
          }}
        >
          {Object.entries(resultado.pareceres).map(([key, parecer]) => (
            <AgentCard key={key} agentKey={key} parecer={parecer} />
          ))}
        </div>
      </div>

      {/* ── Radar Chart ── */}
      <Tile style={{ padding: '20px' }}>
        <p style={{ fontWeight: 600, marginBottom: '12px' }}>📊 Radar dos Agentes</p>
        <AgentRadarChart pareceres={resultado.pareceres} />
      </Tile>

      {/* ── Limitações ── */}
      {resultado.limitacoes?.length > 0 && (
        <Accordion>
          <AccordionItem title="📌 Limitações da análise">
            <ul style={{ paddingLeft: '18px', fontSize: '13px', color: '#6f6f6f', lineHeight: 1.8 }}>
              {resultado.limitacoes.map((l, i) => (
                <li key={i}>{l}</li>
              ))}
            </ul>
          </AccordionItem>
        </Accordion>
      )}

      {/* ── Download ── */}
      <div>
        <Button
          kind="secondary"
          renderIcon={Download}
          iconDescription="Download"
          onClick={() => downloadJSON(resultado)}
        >
          ⬇️ Baixar Relatório JSON (trilha de auditoria)
        </Button>
      </div>
    </div>
  )
}
