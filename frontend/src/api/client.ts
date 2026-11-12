import axios from 'axios'
import type { Region, RegionSummary, GuardianResult, SimulatorParams } from '../types'

// Dev: backend em localhost:8000. Produção (build): mesma origem do site, pois a API serve o front.
const BASE_URL =
  import.meta.env.VITE_API_URL ?? (import.meta.env.PROD ? '' : 'http://localhost:8000')

const http = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// ─── Regions ─────────────────────────────────────────────────────────────────

export async function listarRegioes(): Promise<RegionSummary[]> {
  const { data } = await http.get<RegionSummary[]>('/regioes')
  return data
}

export async function consultarRegiao(id: string): Promise<Region> {
  const { data } = await http.get<Region>(`/regioes/${id}`)
  return data
}

// ─── Analysis ────────────────────────────────────────────────────────────────

export async function executarAnalise(
  id: string,
  fonte: 'local' | 'nuvem' = 'local',
): Promise<GuardianResult> {
  const { data } = await http.post<GuardianResult>(`/analise/${id}`, { fonte })
  return data
}

export async function baixarRelatorio(id: string): Promise<GuardianResult> {
  const { data } = await http.get<GuardianResult>(`/relatorio/${id}`)
  return data
}

// ─── Simulator ───────────────────────────────────────────────────────────────

export async function simularCenario(params: SimulatorParams): Promise<{
  base: GuardianResult
  parcerias: GuardianResult
}> {
  const { regiao_id, reducao_capex_pct, ancoras_adicionais, maturidade_parcerias } = params

  const [base, parcerias] = await Promise.all([
    executarAnalise(regiao_id, 'local'),
    http
      .post<GuardianResult>(`/analise/${regiao_id}`, {
        fonte: 'local',
        reducao_capex_pct,
        ancoras_adicionais,
        maturidade_parcerias,
      })
      .then((r) => r.data),
  ])

  return { base, parcerias }
}

// ─── Cloud mode status ───────────────────────────────────────────────────────

export async function statusNuvem(): Promise<boolean> {
  const { data } = await http.get<{ configurada: boolean }>('/nuvem/status')
  return data.configurada
}
