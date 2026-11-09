import React, {
  createContext,
  useContext,
  useReducer,
  useCallback,
  type ReactNode,
} from 'react'
import type { GuardianResult, RegionSummary, HistoryEntry } from '../types'

// ─── State ───────────────────────────────────────────────────────────────────

interface AppState {
  regioes: RegionSummary[]
  regiaoSelecionada: string
  fonte: 'local' | 'nuvem'
  historico: HistoryEntry[]
  toasts: Toast[]
}

export interface Toast {
  id: string
  kind: 'success' | 'error' | 'warning' | 'info'
  title: string
  subtitle?: string
}

// ─── Actions ─────────────────────────────────────────────────────────────────

type Action =
  | { type: 'SET_REGIOES'; payload: RegionSummary[] }
  | { type: 'SET_REGIAO'; payload: string }
  | { type: 'SET_FONTE'; payload: 'local' | 'nuvem' }
  | { type: 'ADD_HISTORICO'; payload: GuardianResult }
  | { type: 'ADD_TOAST'; payload: Toast }
  | { type: 'REMOVE_TOAST'; payload: string }

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_REGIOES':
      return {
        ...state,
        regioes: action.payload,
        regiaoSelecionada: state.regiaoSelecionada || action.payload[0]?.id || '',
      }
    case 'SET_REGIAO':
      return { ...state, regiaoSelecionada: action.payload }
    case 'SET_FONTE':
      return { ...state, fonte: action.payload }
    case 'ADD_HISTORICO': {
      const result = action.payload
      const existing = state.historico.findIndex(
        (h) => h.resultado.regiao_id === result.regiao_id,
      )
      const entry: HistoryEntry = {
        resultado: result,
        timestamp: new Date().toISOString(),
      }
      if (existing >= 0) {
        const updated = [...state.historico]
        updated[existing] = entry
        return { ...state, historico: updated }
      }
      const next = [entry, ...state.historico].slice(0, 10)
      return { ...state, historico: next }
    }
    case 'ADD_TOAST':
      return { ...state, toasts: [...state.toasts, action.payload] }
    case 'REMOVE_TOAST':
      return { ...state, toasts: state.toasts.filter((t) => t.id !== action.payload) }
    default:
      return state
  }
}

const initialState: AppState = {
  regioes: [],
  regiaoSelecionada: '',
  fonte: 'local',
  historico: [],
  toasts: [],
}

// ─── Context ─────────────────────────────────────────────────────────────────

interface AppContextValue {
  state: AppState
  setRegioes: (regioes: RegionSummary[]) => void
  setRegiao: (id: string) => void
  setFonte: (fonte: 'local' | 'nuvem') => void
  addHistorico: (resultado: GuardianResult) => void
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
  getHistoricoByRegiao: (id: string) => GuardianResult | undefined
}

const AppContext = createContext<AppContextValue | null>(null)

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState)

  const setRegioes = useCallback(
    (regioes: RegionSummary[]) => dispatch({ type: 'SET_REGIOES', payload: regioes }),
    [],
  )
  const setRegiao = useCallback(
    (id: string) => dispatch({ type: 'SET_REGIAO', payload: id }),
    [],
  )
  const setFonte = useCallback(
    (fonte: 'local' | 'nuvem') => dispatch({ type: 'SET_FONTE', payload: fonte }),
    [],
  )
  const addHistorico = useCallback(
    (resultado: GuardianResult) => dispatch({ type: 'ADD_HISTORICO', payload: resultado }),
    [],
  )
  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`
    dispatch({ type: 'ADD_TOAST', payload: { ...toast, id } })
    setTimeout(() => dispatch({ type: 'REMOVE_TOAST', payload: id }), 5000)
  }, [])
  const removeToast = useCallback(
    (id: string) => dispatch({ type: 'REMOVE_TOAST', payload: id }),
    [],
  )
  const getHistoricoByRegiao = useCallback(
    (id: string) => state.historico.find((h) => h.resultado.regiao_id === id)?.resultado,
    [state.historico],
  )

  return (
    <AppContext.Provider
      value={{
        state,
        setRegioes,
        setRegiao,
        setFonte,
        addHistorico,
        addToast,
        removeToast,
        getHistoricoByRegiao,
      }}
    >
      {children}
    </AppContext.Provider>
  )
}

export function useApp(): AppContextValue {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used inside AppProvider')
  return ctx
}
