import React, { useEffect, useState, useCallback } from 'react'
import {
  Button,
  Select,
  SelectItem,
  RadioButtonGroup,
  RadioButton,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Tile,
  InlineLoading,
  DataTable,
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  InlineNotification,
} from '@carbon/react'
import { PlayFilled } from '@carbon/icons-react'
import { useSearchParams } from 'react-router-dom'
import { useApp } from '../context/AppContext'
import { listarRegioes, consultarRegiao, executarAnalise } from '../api/client'
import type { Region, GuardianResult, Recomendacao } from '../types'
import { IndicatorTabs } from '../components/indicators/IndicatorTabs'
import { GuardianResultPanel } from '../components/analysis/GuardianResult'
import { RecommendationTag } from '../components/analysis/RecommendationTag'
import { RegionMap } from '../components/map/RegionMap'
import { EmptyState } from '../components/common/EmptyState'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'

export default function Analise() {
  const { state, setRegioes, setRegiao, setFonte, addHistorico, addToast, getHistoricoByRegiao } =
    useApp()
  const [searchParams] = useSearchParams()

  const [loadingRegioes, setLoadingRegioes] = useState(false)
  const [loadingRegiao, setLoadingRegiao] = useState(false)
  const [loadingAnalise, setLoadingAnalise] = useState(false)
  const [regionData, setRegionData] = useState<Region | null>(null)
  const [resultado, setResultado] = useState<GuardianResult | null>(null)
  const [activeTab, setActiveTab] = useState(0)

  // Load region list on mount
  useEffect(() => {
    if (state.regioes.length > 0) return
    setLoadingRegioes(true)
    listarRegioes()
      .then((data) => {
        setRegioes(data)
      })
      .catch(() =>
        addToast({ kind: 'error', title: 'Erro ao carregar regiões', subtitle: 'Verifique se o backend está rodando.' }),
      )
      .finally(() => setLoadingRegioes(false))
  }, [])

  // Handle ?demo= query param
  useEffect(() => {
    const demo = searchParams.get('demo')
    if (demo && state.regioes.some((r) => r.id === demo)) {
      setRegiao(demo)
    }
  }, [searchParams, state.regioes])

  // Load region data when selection changes
  useEffect(() => {
    if (!state.regiaoSelecionada) return
    setLoadingRegiao(true)
    consultarRegiao(state.regiaoSelecionada)
      .then(setRegionData)
      .catch(() =>
        addToast({ kind: 'error', title: 'Erro ao carregar dados da região' }),
      )
      .finally(() => setLoadingRegiao(false))

    // Restore previous result if available
    const prev = getHistoricoByRegiao(state.regiaoSelecionada)
    setResultado(prev ?? null)
  }, [state.regiaoSelecionada])

  const handleExecutar = useCallback(async () => {
    if (!state.regiaoSelecionada) return
    setLoadingAnalise(true)
    setActiveTab(1)
    try {
      const result = await executarAnalise(state.regiaoSelecionada, state.fonte)
      setResultado(result)
      addHistorico(result)
      addToast({
        kind: 'success',
        title: 'Análise concluída',
        subtitle: result.regiao_nome,
      })
    } catch {
      addToast({
        kind: 'error',
        title: 'Erro na análise',
        subtitle: 'Não foi possível conectar ao backend.',
      })
    } finally {
      setLoadingAnalise(false)
    }
  }, [state.regiaoSelecionada, state.fonte])

  // Build recommendation map for the map component
  const recomendacoes: Record<string, Recomendacao> = {}
  const priorityAlert: Record<string, boolean> = {}
  state.historico.forEach((h) => {
    recomendacoes[h.resultado.regiao_id] = h.resultado.recomendacao
    priorityAlert[h.resultado.regiao_id] = h.resultado.atencao_prioritaria
  })

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 96px)', overflow: 'hidden' }}>
      {/* ── Sidebar ── */}
      <aside
        style={{
          width: '280px',
          minWidth: '240px',
          background: '#f4f4f4',
          borderRight: '1px solid #e0e0e0',
          padding: '24px 16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          overflowY: 'auto',
        }}
      >
        <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#161616' }}>
          Análise de Região
        </h2>

        {loadingRegioes ? (
          <InlineLoading description="Carregando regiões..." />
        ) : (
          <Select
            id="regiao-select"
            labelText="Selecionar região"
            value={state.regiaoSelecionada}
            onChange={(e) => setRegiao(e.target.value)}
          >
            {state.regioes.map((r) => (
              <SelectItem key={r.id} value={r.id} text={r.nome} />
            ))}
          </Select>
        )}

        <div>
          <p
            style={{
              fontSize: '12px',
              fontWeight: 600,
              color: '#6f6f6f',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              marginBottom: '8px',
            }}
          >
            Fonte dos pareceres
          </p>
          <RadioButtonGroup
            legendText=""
            name="fonte"
            valueSelected={state.fonte}
            onChange={(v) => setFonte(v as 'local' | 'nuvem')}
            orientation="vertical"
          >
            <RadioButton labelText="Local (determinístico)" value="local" id="fonte-local" />
            <RadioButton labelText="IBM watsonx Orchestrate" value="nuvem" id="fonte-nuvem" />
          </RadioButtonGroup>

          {state.fonte === 'nuvem' && (
            <InlineNotification
              kind="warning"
              title="Requer credenciais"
              subtitle="Configure as variáveis CC_AGENT_ID_* no .env"
              lowContrast
              hideCloseButton
              style={{ marginTop: '8px' }}
            />
          )}
        </div>

        <Button
          renderIcon={loadingAnalise ? undefined : PlayFilled}
          iconDescription="Executar"
          onClick={handleExecutar}
          disabled={loadingAnalise || !state.regiaoSelecionada}
          style={{ width: '100%' }}
        >
          {loadingAnalise ? (
            <InlineLoading description="Consultando agentes..." />
          ) : (
            '▶ Executar Conselho'
          )}
        </Button>
      </aside>

      {/* ── Main content ── */}
      <main style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
        <Tabs selectedIndex={activeTab} onChange={({ selectedIndex }) => setActiveTab(selectedIndex)}>
          <TabList aria-label="Seções da análise" contained>
            <Tab>📊 Indicadores</Tab>
            <Tab>🛡️ Conselho</Tab>
            <Tab>🏆 Ranking &amp; Histórico</Tab>
          </TabList>

          <TabPanels>
            {/* Tab 1 — Indicators */}
            <TabPanel>
              <RegionMap
                selectedRegion={state.regiaoSelecionada}
                recomendacoes={recomendacoes}
                priorityAlert={priorityAlert}
                onSelectRegion={setRegiao}
              />
              <div style={{ marginTop: '16px' }}>
                {loadingRegiao ? (
                  <LoadingSkeleton />
                ) : regionData ? (
                  <IndicatorTabs region={regionData} />
                ) : (
                  <EmptyState
                    title="Selecione uma região"
                    subtitle="Escolha uma região na barra lateral ou clicando no mapa."
                  />
                )}
              </div>
            </TabPanel>

            {/* Tab 2 — Guardian result */}
            <TabPanel>
              {loadingAnalise ? (
                <Tile style={{ padding: '48px', textAlign: 'center' }}>
                  <InlineLoading description="Consultando os 5 agentes especialistas..." />
                </Tile>
              ) : resultado ? (
                <GuardianResultPanel resultado={resultado} />
              ) : (
                <EmptyState
                  title="Nenhuma análise executada"
                  subtitle="Clique em ▶ Executar Conselho para analisar a região selecionada."
                />
              )}
            </TabPanel>

            {/* Tab 3 — Ranking */}
            <TabPanel>
              {state.historico.length === 0 ? (
                <EmptyState
                  title="Nenhuma análise nesta sessão"
                  subtitle="Execute o Conselho para uma região e ela aparecerá aqui."
                />
              ) : (
                <DataTable
                  rows={state.historico.map((h) => ({
                    id: h.resultado.regiao_id,
                    regiao: h.resultado.regiao_nome,
                    score: h.resultado.score_consolidado ?? '—',
                    recomendacao: h.resultado.recomendacao,
                    fonte: h.resultado.fonte === 'nuvem' ? '☁️ Nuvem' : '💻 Local',
                    tempo: h.resultado.tempo_analise_segundos
                      ? `${h.resultado.tempo_analise_segundos}s`
                      : '—',
                  }))}
                  headers={[
                    { key: 'regiao', header: 'Região' },
                    { key: 'score', header: 'Score' },
                    { key: 'recomendacao', header: 'Recomendação' },
                    { key: 'fonte', header: 'Fonte' },
                    { key: 'tempo', header: 'Tempo' },
                  ]}
                >
                  {({ rows, headers, getHeaderProps, getTableProps }) => (
                    <TableContainer title="Histórico da sessão">
                      <Table {...getTableProps()}>
                        <TableHead>
                          <TableRow>
                            {headers.map((h) => (
                              <TableHeader key={h.key} {...getHeaderProps({ header: h })}>
                                {h.header}
                              </TableHeader>
                            ))}
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {rows.map((row) => (
                            <TableRow key={row.id}>
                              {row.cells.map((cell) => (
                                <TableCell key={cell.id}>
                                  {cell.info.header === 'recomendacao' ? (
                                    <RecommendationTag
                                      recomendacao={cell.value as Recomendacao}
                                      size="sm"
                                    />
                                  ) : (
                                    cell.value
                                  )}
                                </TableCell>
                              ))}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  )}
                </DataTable>
              )}
            </TabPanel>
          </TabPanels>
        </Tabs>
      </main>
    </div>
  )
}
