import React, { useState, useCallback } from 'react'
import type { Recomendacao } from '../../types'

// ── Color palette ────────────────────────────────────────────────────────────
const REC_COLOR: Record<Recomendacao, string> = {
  investir_agora:  '#24a148',
  realizar_piloto: '#0f62fe',
  aguardar:        '#f1c21b',
  escalar_humano:  '#da1e28',
}

const REC_LABEL: Record<Recomendacao, string> = {
  investir_agora:  'Investir Agora',
  realizar_piloto: 'Realizar Piloto',
  aguardar:        'Aguardar',
  escalar_humano:  'Escalar a Humano',
}

// ── 6 fictional regions positioned on a Brazil silhouette SVG ────────────────
// Coordinates are in SVG viewBox space (0 0 500 560)
// Arranged to loosely reflect geographic spread across Brazil
const REGIONS = [
  {
    id: 'aurora',
    nome: 'Região Aurora',
    // Northwest — Amazônia
    cx: 118, cy: 148,
    path: 'M 78,118 L 158,118 L 165,148 L 158,178 L 78,178 L 71,148 Z',
  },
  {
    id: 'central',
    nome: 'Região Central',
    // Center-west — Mato Grosso
    cx: 238, cy: 248,
    path: 'M 198,218 L 278,218 L 285,248 L 278,278 L 198,278 L 191,248 Z',
  },
  {
    id: 'esperanca',
    nome: 'Região Esperança',
    // Northeast — Bahia
    cx: 358, cy: 198,
    path: 'M 318,168 L 398,168 L 405,198 L 398,228 L 318,228 L 311,198 Z',
  },
  {
    id: 'horizonte',
    nome: 'Região Horizonte',
    // South — Paraná
    cx: 238, cy: 388,
    path: 'M 198,358 L 278,358 L 285,388 L 278,418 L 198,418 L 191,388 Z',
  },
  {
    id: 'nova_uniao',
    nome: 'Nova União',
    // Southeast — São Paulo / Minas
    cx: 338, cy: 338,
    path: 'M 298,308 L 378,308 L 385,338 L 378,368 L 298,368 L 291,338 Z',
  },
  {
    id: 'vale_verde',
    nome: 'Vale Verde',
    // Center-north — Pará / Tocantins
    cx: 318, cy: 128,
    path: 'M 278,98  L 358,98  L 365,128 L 358,158 L 278,158 L 271,128 Z',
  },
]

interface RegionMapProps {
  selectedRegion: string
  recomendacoes?: Record<string, Recomendacao>
  priorityAlert?: Record<string, boolean>
  onSelectRegion: (id: string) => void
}

export function RegionMap({
  selectedRegion,
  recomendacoes = {},
  priorityAlert = {},
  onSelectRegion,
}: RegionMapProps) {
  const [hovered, setHovered] = useState<string | null>(null)

  const getFill = useCallback(
    (id: string) => {
      const rec = recomendacoes[id]
      if (rec) return REC_COLOR[rec]
      return '#c6c6c6'
    },
    [recomendacoes],
  )

  const getStroke = useCallback(
    (id: string) => {
      if (priorityAlert[id]) return '#da1e28'
      if (id === selectedRegion) return '#161616'
      return '#8d8d8d'
    },
    [selectedRegion, priorityAlert],
  )

  const getOpacity = useCallback(
    (id: string) => {
      if (id === hovered) return 0.95
      if (id === selectedRegion) return 0.85
      return 0.55
    },
    [hovered, selectedRegion],
  )

  // Legend: only show recs that have been calculated
  const legendItems = (Object.keys(REC_LABEL) as Recomendacao[]).filter(
    (r) => Object.values(recomendacoes).includes(r),
  )

  const hoveredRegion = REGIONS.find((r) => r.id === hovered)
  const hoveredRec = hovered ? recomendacoes[hovered] : undefined

  return (
    <div
      style={{
        background: '#ffffff',
        border: '1px solid #e0e0e0',
        borderRadius: '6px',
        overflow: 'hidden',
      }}
    >
      {/* ── SVG map ── */}
      <div style={{ position: 'relative', background: '#f0f4ff' }}>
        <svg
          viewBox="0 0 500 480"
          style={{ width: '100%', height: '300px', display: 'block', cursor: 'default' }}
          aria-label="Mapa das 6 regiões simuladas"
        >
          {/* Brazil background silhouette — simplified path */}
          <path
            d="M 60,60 L 160,40 L 280,35 L 390,55 L 450,100 L 460,170 L 440,240
               L 420,290 L 400,360 L 360,420 L 310,455 L 260,460 L 200,450
               L 150,420 L 110,380 L 80,320 L 55,250 L 45,180 Z"
            fill="#dce8f7"
            stroke="#b0c8e8"
            strokeWidth="1.5"
          />

          {/* State borders hint — subtle lines */}
          <line x1="100" y1="200" x2="420" y2="200" stroke="#c0d4ea" strokeWidth="0.5" strokeDasharray="4 4" />
          <line x1="240" y1="60" x2="240" y2="460" stroke="#c0d4ea" strokeWidth="0.5" strokeDasharray="4 4" />

          {/* Region shapes */}
          {REGIONS.map((region) => {
            const isSelected = region.id === selectedRegion
            const isPriority = priorityAlert[region.id]

            return (
              <g
                key={region.id}
                onClick={() => onSelectRegion(region.id)}
                onMouseEnter={() => setHovered(region.id)}
                onMouseLeave={() => setHovered(null)}
                style={{ cursor: 'pointer' }}
                role="button"
                aria-label={`Selecionar ${region.nome}`}
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && onSelectRegion(region.id)}
              >
                {/* Drop shadow for selected */}
                {isSelected && (
                  <path
                    d={region.path}
                    fill="rgba(0,0,0,0.15)"
                    transform="translate(3,4)"
                  />
                )}

                {/* Region hexagonal shape */}
                <path
                  d={region.path}
                  fill={getFill(region.id)}
                  fillOpacity={getOpacity(region.id)}
                  stroke={getStroke(region.id)}
                  strokeWidth={isPriority || isSelected ? 2.5 : 1.5}
                  strokeDasharray={isPriority ? '5 2' : undefined}
                  style={{ transition: 'fill-opacity 0.15s, stroke-width 0.1s' }}
                />

                {/* Region label */}
                <text
                  x={region.cx}
                  y={region.cy - 4}
                  textAnchor="middle"
                  fontSize="9"
                  fontWeight="600"
                  fill={isSelected ? '#161616' : '#525252'}
                  fontFamily="IBM Plex Sans, sans-serif"
                  style={{ pointerEvents: 'none', userSelect: 'none' }}
                >
                  {region.nome.replace('Região ', '')}
                </text>

                {/* Score badge if analyzed */}
                {recomendacoes[region.id] && (
                  <text
                    x={region.cx}
                    y={region.cy + 10}
                    textAnchor="middle"
                    fontSize="8"
                    fontWeight="400"
                    fill={isSelected ? '#161616' : '#6f6f6f'}
                    fontFamily="IBM Plex Sans, sans-serif"
                    style={{ pointerEvents: 'none', userSelect: 'none' }}
                  >
                    {REC_LABEL[recomendacoes[region.id]]}
                  </text>
                )}

                {/* Priority indicator */}
                {isPriority && (
                  <text
                    x={region.cx + 32}
                    y={region.cy - 18}
                    fontSize="11"
                    style={{ pointerEvents: 'none', userSelect: 'none' }}
                  >
                    ⚠
                  </text>
                )}

                {/* Selection ring */}
                {isSelected && (
                  <path
                    d={region.path}
                    fill="none"
                    stroke="#0f62fe"
                    strokeWidth="2"
                    strokeDasharray="none"
                    opacity="0.6"
                    transform="scale(1.04) translate(-9,-7)"
                  />
                )}
              </g>
            )
          })}

          {/* Compass rose */}
          <g transform="translate(32,430)">
            <text fontSize="10" fill="#8d8d8d" fontFamily="IBM Plex Sans, sans-serif" textAnchor="middle" x="0" y="-12">N</text>
            <line x1="0" y1="-8" x2="0" y2="0" stroke="#8d8d8d" strokeWidth="1"/>
            <circle cx="0" cy="3" r="3" fill="none" stroke="#8d8d8d" strokeWidth="1"/>
          </g>

          {/* "Dados simulados" watermark */}
          <text
            x="250" y="472"
            textAnchor="middle"
            fontSize="9"
            fill="#b0b0b0"
            fontFamily="IBM Plex Sans, sans-serif"
            fontStyle="italic"
          >
            Regiões fictícias · Dados simulados
          </text>
        </svg>

        {/* Hover tooltip */}
        {hoveredRegion && (
          <div
            style={{
              position: 'absolute',
              top: '12px',
              right: '12px',
              background: '#161616',
              color: '#ffffff',
              borderRadius: '4px',
              padding: '8px 12px',
              fontSize: '12px',
              lineHeight: 1.6,
              pointerEvents: 'none',
              maxWidth: '180px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
            }}
          >
            <p style={{ fontWeight: 700, margin: '0 0 4px', fontSize: '13px' }}>
              {hoveredRegion.nome}
            </p>
            {hoveredRec ? (
              <p style={{ margin: 0, color: REC_COLOR[hoveredRec], fontWeight: 600 }}>
                {REC_LABEL[hoveredRec]}
              </p>
            ) : (
              <p style={{ margin: 0, color: '#8d8d8d' }}>Não analisada</p>
            )}
            {priorityAlert[hoveredRegion.id] && (
              <p style={{ margin: '4px 0 0', color: '#da1e28', fontWeight: 700 }}>
                ⚠ Atenção Prioritária
              </p>
            )}
          </div>
        )}
      </div>

      {/* ── Caption + legend ── */}
      <div
        style={{
          background: '#f4f4f4',
          borderTop: '1px solid #e0e0e0',
          padding: '8px 12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '8px',
        }}
      >
        <span style={{ fontSize: '12px', color: '#6f6f6f' }}>
          Clique em uma região para selecioná-la
        </span>

        {legendItems.length > 0 ? (
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
            {legendItems.map((rec) => (
              <div key={rec} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <div style={{ width: 10, height: 10, borderRadius: 2, background: REC_COLOR[rec], flexShrink: 0 }} />
                <span style={{ fontSize: '11px', color: '#525252' }}>{REC_LABEL[rec]}</span>
              </div>
            ))}
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ width: 10, height: 10, borderRadius: 2, background: '#c6c6c6', flexShrink: 0 }} />
              <span style={{ fontSize: '11px', color: '#525252' }}>Não analisada</span>
            </div>
          </div>
        ) : (
          <span style={{ fontSize: '11px', color: '#8d8d8d' }}>
            Execute uma análise para ver as recomendações no mapa
          </span>
        )}
      </div>
    </div>
  )
}
