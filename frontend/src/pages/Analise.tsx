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
  Tag,
} from '@carbon/react'
import { PlayFilled, ChevronRight } from '@carbon/icons-react'
import { useSearchParams } from 'react-router-dom'
import { useApp } from '../context/AppContext'
import { listarRegioes, consultarRegiao, executarAnalise } from '../api/client'
import type { Region, GuardianResult, Recomendacao } from '../types'
import { IndicatorTabs } from '../components/indicators/IndicatorTabs'
import { GuardianResultPanel } from '../components/analysis/GuardianResult'
import { RecommendationTag } from '../components/analysis/RecommendationTag'
import { ScoreProgressBar } from '../components/analysis/ScoreProgressBar'
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
      .then((data) => setRegioes(data))
      .catch(() =>
        addToast({
          kind: 'error',
          title: 'Erro ao carregar regiões',
          subtitle: 'Verifique se o backend está rodando em localhost:8000.',
        }),
      )
      .finally(() => setLoadingRegioes(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Handle ?demo= query param
  useEffect(() => {
    const demo = searchParams.get('demo')
    if (demo && state.regioes.some((r) => r.id === demo)) setRegiao(demo)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, state.regioes])

  // Load region data when selection changes
  useEffect(() => {
    if (!state.regiaoSelecionada) return
    setLoadingRegiao(true)
    consultarRegiao(state.regiaoSelecionada)
      .then(setRegionData)
      .catch(() => addToast({ kind: 'error', title: 'Erro ao carregar dados da região' }))
      .finally(() => setLoadingRegiao(false))

    const prev = getHistoricoByRegiao(state.regiaoSelecionada)
    setResultado(prev ?? null)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.regiaoSelecionada])

  const handleExecutar = useCallback(async () => {
    if (!state.regiaoSelecionada) return
    setLoadingAnalise(true)
    setActiveTab(1)
    try {
      const result = await executarAnalise(state.regiaoSelecionada, state.fonte)
      setResultado(result)
      addHistorico(result)
      addToast({ kind: 'success', title: 'Análise concluída', subtitle: result.regiao_nome })
    } catch {
      addToast({ kind: 'error', title: 'Erro na análise', subtitle: 'Não foi possível conectar ao backend.' })
    } finally {
      setLoadingAnalise(false)
    }
  }, [state.regiaoSelecionada, state.fonte, addHistorico, addToast])

  // Map color state
  const recomendacoes: Record<string, Recomendacao> = {}
  const priorityAlert: Record<string, boolean> = {}
  state.historico.forEach((h) => {
    recomendacoes[h.resultado.regiao_id] = h.resultado.recomendacao
    priorityAlert[h.resultado.regiao_id] = h.resultado.atencao_prioritaria
  })

  // Current region profile text
  const regiaoAtual = state.regioes.find((r) => r.id === state.regiaoSelecionada)

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 90px)', overflow: 'hidden' }}>

      {/* ── Sidebar ──────────────────────────────────────────────────────── */}
      <aside
        style={{
          width: '272px',
          minWidth: '240px',
          background: '#ffffff',
          borderRight: '1px solid #e0e0e0',
          display: 'flex',
          flexDirection: 'column',
          overflowY: 'auto',
        }}
      >
        {/* Header strip */}
        <div
          style={{
            padding: '20px 16px 16px',
            borderBottom: '1px solid #e0e0e0',
            background: '#161616',
          }}
        >
          <p style={{ fontSize: '11px', fontWeight: 600, color: '#8d8d8d', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '4px' }}>
            Conecta Conselho
          </p>
          <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#ffffff', margin: 0 }}>
            Análise de Região
          </h2>
        </div>

        {/* Region selector */}
        <div style={{ padding: '16px', borderBottom: '1px solid #e0e0e0' }}>
          {loadingRegioes ? (
            <InlineLoading description="Carregando regiões..." />
          ) : (
            <Select
              id="regiao-select"
              labelText="Região"
              value={state.regiaoSelecionada}
              onChange={(e) => setRegiao(e.target.value)}
            >
              {state.regioes.map((r) => (
                <SelectItem key={r.id} value={r.id} text={r.nome} />
              ))}
            </Select>
          )}

          {/* Region profile description */}
          {regiaoAtual?.descricao_perfil && (
            <p
              style={{
                fontSize: '12px',
                color: '#525252',
                marginTop: '8px',
                lineHeight: 1.5,
                fontStyle: 'italic',
              }}
            >
              {regiaoAtual.descricao_perfil}
            </p>
          )}

          {/* Previous result badge */}
          {resultado && !loadingAnalise && (
            <div
              style={{
                marginTop: '10px',
                padding: '8px 10px',
                background: '#f4f4f4',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span style={{ fontSize: '12px', color: '#525252' }}>Último resultado</span>
              <RecommendationTag recomendacao={resultado.recomendacao} size="sm" />
            </div>
          )}
        </div>

        {/* Source selector */}
        <div style={{ padding: '16px', borderBottom: '1px solid #e0e0e0' }}>
          <p style={{ fontSize: '11px', fontWeight: 600, color: '#6f6f6f', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '10px' }}>
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
              subtitle="Configure CC_AGENT_ID_* no .env"
              lowContrast
              hideCloseButton
              style={{ marginTop: '8px' }}
            />
          )}
        </div>

        {/* CTA */}
        <div style={{ padding: '16px' }}>
          <Button
            renderIcon={loadingAnalise ? undefined : PlayFilled}
            iconDescription="Executar Conselho"
            onClick={handleExecutar}
            disabled={loadingAnalise || !state.regiaoSelecionada}
            style={{ width: '100%' }}
            size="lg"
          >
            {loadingAnalise ? (
              <InlineLoading description="Consultando agentes..." />
            ) : (
              'Executar Conselho'
            )}
          </Button>

          {/* Hint */}
          {!resultado && !loadingAnalise && (
            <p style={{ fontSize: '11px', color: '#8d8d8d', marginTop: '8px', textAlign: 'center', lineHeight: 1.5 }}>
              Selecione uma região e clique para obter o parecer dos 5 agentes especialistas.
            </p>
          )}
        </div>

        {/* Session mini-ranking */}
        {state.historico.length > 0 && (
          <div style={{ padding: '0 16px 16px' }}>
            <p style={{ fontSize: '11px', fontWeight: 600, color: '#6f6f6f', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px' }}>
              Sessão atual
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {state.historico.slice(0, 5).map((h) => (
                <button
                  key={h.resultado.regiao_id}
                  onClick={() => setRegiao(h.resultado.regiao_id)}
                  style={{
                    all: 'unset',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '6px 8px',
                    borderRadius: '4px',
                    background: h.resultado.regiao_id === state.regiaoSelecionada ? '#e8f5e9' : '#f4f4f4',
                    border: h.resultado.regiao_id === state.regiaoSelecionada ? '1px solid #24a148' : '1px solid transparent',
                  }}
                >
                  <span style={{ fontSize: '12px', fontWeight: 500, color: '#161616' }}>
                    {h.resultado.regiao_nome}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ fontSize: '11px', color: '#525252' }}>
                      {h.resultado.score_consolidado}
                    </span>
                    <ChevronRight size={12} style={{ color: '#8d8d8d' }} />
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </aside>

      {/* ── Main content ─────────────────────────────────────────────────── */}
      <main style={{ flex: 1, overflowY: 'auto', background: '#f4f4f4' }}>
        <Tabs
          selectedIndex={activeTab}
          onChange={({ selectedIndex }) => setActiveTab(selectedIndex)}
        >
          <TabList
            aria-label="Seções da análise"
            contained
            style={{ background: '#ffffff', borderBottom: '1px solid #e0e0e0' }}
          >
            <Tab>📊 Indicadores</Tab>
            <Tab>
              🛡️ Conselho
              {resultado && !loadingAnalise && (
                <Tag
                  type={resultado.atencao_prioritaria ? 'red' : 'blue'}
                  size="sm"
                  style={{ marginLeft: '6px', verticalAlign: 'middle' }}
                >
                  {resultado.score_consolidado}
                </Tag>
              )}
            </Tab>
            <Tab>🏆 Histórico</Tab>
          </TabList>

          <TabPanels>
            {/* ── Tab 1: Indicators ── */}
            <TabPanel style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>

              {/* Map */}
              <RegionMap
                selectedRegion={state.regiaoSelecionada}
                recomendacoes={recomendacoes}
                priorityAlert={priorityAlert}
                onSelectRegion={setRegiao}
              />

              {/* Region data */}
              <div
                style={{
                  background: '#ffffff',
                  borderRadius: '6px',
                  border: '1px solid #e0e0e0',
                  overflow: 'hidden',
                }}
              >
                {/* Region name header */}
                {regiaoAtual && (
                  <div
                    style={{
                      padding: '14px 20px',
                      borderBottom: '1px solid #e0e0e0',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      background: '#ffffff',
                    }}
                  >
                    <div>
                      <h3 style={{ fontSize: '15px', fontWeight: 700, margin: 0, color: '#161616' }}>
                        {regiaoAtual.nome}
                      </h3>
                      <p style={{ fontSize: '12px', color: '#6f6f6f', margin: '2px 0 0' }}>
                        {regiaoAtual.descricao_perfil}
                      </p>
                    </div>
                    {resultado && (
                      <div style={{ textAlign: 'right' }}>
                        <ScoreProgressBar
                          score={resultado.score_consolidado}
                          recomendacao={resultado.recomendacao}
                          showNumber
                          height={10}
                          animate={false}
                        />
                      </div>
                    )}
                  </div>
                )}

                <div style={{ padding: '0' }}>
                  {loadingRegiao ? (
                    <div style={{ padding: '24px' }}>
                      <LoadingSkeleton />
                    </div>
                  ) : regionData ? (
                    <IndicatorTabs region={regionData} />
                  ) : (
                    <div style={{ padding: '24px' }}>
                      <EmptyState
                        title="Selecione uma região"
                        subtitle="Escolha uma região na barra lateral ou clicando no mapa."
                      />
                    </div>
                  )}
                </div>
              </div>
            </TabPanel>

            {/* ── Tab 2: Guardian result ── */}
            <TabPanel style={{ padding: '20px' }}>
              {loadingAnalise ? (
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '80px 24px',
                    gap: '16px',
                  }}
                >
                  <InlineLoading description="Consultando os 5 agentes especialistas..." />
                  <p style={{ fontSize: '13px', color: '#6f6f6f', textAlign: 'center', maxWidth: '320px' }}>
                    Cada agente analisa uma perspectiva diferente da região simultaneamente.
                    Isso pode levar alguns segundos.
                  </p>
                </div>
              ) : resultado ? (
                <GuardianResultPanel resultado={resultado} />
              ) : (
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '80px 24px',
                    gap: '16px',
                    textAlign: 'center',
                  }}
                >
                  <div
                    style={{
                      width: '64px',
                      height: '64px',
                      borderRadius: '50%',
                      background: '#e8f5e9',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '28px',
                    }}
                  >
                    🛡️
                  </div>
                  <div>
                    <p style={{ fontSize: '16px', fontWeight: 600, color: '#161616', margin: '0 0 8px' }}>
                      Nenhuma análise executada
                    </p>
                    <p style={{ fontSize: '14px', color: '#6f6f6f', margin: 0, maxWidth: '300px' }}>
                      Selecione uma região e clique em <strong>Executar Conselho</strong> para ver o parecer dos 5 agentes.
                    </p>
                  </div>
                  <Button kind="primary" renderIcon={PlayFilled} onClick={handleExecutar} disabled={!state.regiaoSelecionada}>
                    Executar Conselho
                  </Button>
                </div>
              )}
            </TabPanel>

            {/* ── Tab 3: History ── */}
            <TabPanel style={{ padding: '20px' }}>
              {state.historico.length === 0 ? (
                <EmptyState
                  title="Nenhuma análise nesta sessão"
                  subtitle="Execute o Conselho para uma região e ela aparecerá aqui."
                />
              ) : (
                <div
                  style={{
                    background: '#ffffff',
                    borderRadius: '6px',
                    border: '1px solid #e0e0e0',
                    overflow: 'hidden',
                  }}
                >
                  <DataTable
                    rows={[...state.historico]
                      .sort((a, b) => (b.resultado.score_consolidado ?? 0) - (a.resultado.score_consolidado ?? 0))
                      .map((h) => ({
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
                      <TableContainer title="Histórico da sessão (ordenado por score)">
                        <Table {...getTableProps()} size="sm">
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
                              <TableRow
                                key={row.id}
                                style={{ cursor: 'pointer' }}
                                onClick={() => {
                                  setRegiao(row.id)
                                  setActiveTab(1)
                                }}
                              >
                                {row.cells.map((cell) => (
                                  <TableCell key={cell.id}>
                                    {cell.info.header === 'recomendacao' ? (
                                      <RecommendationTag
                                        recomendacao={cell.value as Recomendacao}
                                        size="sm"
                                      />
                                    ) : cell.info.header === 'score' ? (
                                      <strong style={{ fontSize: '14px' }}>{cell.value}</strong>
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
                </div>
              )}
            </TabPanel>
          </TabPanels>
        </Tabs>
      </main>
    </div>
  )
}
