import { useEffect, useRef, useState } from 'react'
import type { Recomendacao } from '../../types'

const COLOR_MAP: Record<Recomendacao, string> = {
  investir_agora: '#24a148',
  realizar_piloto: '#0043ce',
  aguardar: '#f1c21b',
  escalar_humano: '#da1e28',
}

function scoreToRecomendacao(score: number): Recomendacao {
  if (score >= 70) return 'investir_agora'
  if (score >= 50) return 'realizar_piloto'
  if (score >= 30) return 'aguardar'
  return 'escalar_humano'
}

interface ScoreProgressBarProps {
  score: number
  recomendacao?: Recomendacao
  label?: string
  showNumber?: boolean
  height?: number
  animate?: boolean
}

export function ScoreProgressBar({
  score,
  recomendacao,
  label,
  showNumber = true,
  height = 20,
  animate = true,
}: ScoreProgressBarProps) {
  const [displayed, setDisplayed] = useState(animate ? 0 : score)
  const rafRef = useRef<number | null>(null)
  const startRef = useRef<number | null>(null)
  const duration = 800

  useEffect(() => {
    if (!animate) {
      setDisplayed(score)
      return
    }
    startRef.current = null
    const from = 0
    const to = score

    function step(ts: number) {
      if (startRef.current === null) startRef.current = ts
      const elapsed = ts - startRef.current
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplayed(Math.round(from + (to - from) * eased))
      if (progress < 1) rafRef.current = requestAnimationFrame(step)
    }
    rafRef.current = requestAnimationFrame(step)
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [score, animate])

  const color = COLOR_MAP[recomendacao ?? scoreToRecomendacao(score)]

  return (
    <div style={{ width: '100%' }}>
      {(label || showNumber) && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'baseline',
            marginBottom: '6px',
          }}
        >
          {label && (
            <span style={{ fontSize: '13px', color: '#6f6f6f', fontWeight: 500 }}>
              {label}
            </span>
          )}
          {showNumber && (
            <span style={{ fontSize: '16px', fontWeight: 700, color }}>
              {displayed} / 100
            </span>
          )}
        </div>
      )}
      <div
        style={{
          width: '100%',
          height,
          background: '#e0e0e0',
          borderRadius: '2px',
          overflow: 'hidden',
        }}
        role="progressbar"
        aria-valuenow={score}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label ?? 'Score'}
      >
        <div
          style={{
            width: `${displayed}%`,
            height: '100%',
            background: color,
            transition: 'width 0.05s linear',
            borderRadius: '2px',
          }}
        />
      </div>
    </div>
  )
}
