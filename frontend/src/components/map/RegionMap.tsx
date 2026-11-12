import React, { useState, useCallback } from 'react'
import type { Recomendacao } from '../../types'

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

// ── Brazil states — simplified but geographically faithful paths ─────────────
// ViewBox: 0 0 800 860  (roughly 1:1 proportional to Brazil bounding box)
// Each path is a hand-simplified polygon tracing the actual state border shape.
const STATES: { id: string; d: string }[] = [
  // Norte
  { id: 'AM', d: 'M 90,80 L 200,60 L 280,70 L 310,110 L 320,160 L 290,200 L 260,220 L 200,230 L 150,220 L 110,200 L 80,160 L 75,120 Z' },
  { id: 'PA', d: 'M 280,70 L 380,55 L 460,65 L 490,100 L 480,150 L 450,180 L 400,200 L 350,210 L 310,200 L 290,160 L 310,110 Z' },
  { id: 'RR', d: 'M 160,40 L 220,30 L 250,45 L 260,70 L 220,80 L 180,75 L 155,60 Z' },
  { id: 'AP', d: 'M 430,40 L 470,35 L 490,55 L 480,75 L 450,80 L 430,65 Z' },
  { id: 'RO', d: 'M 160,230 L 210,225 L 250,240 L 260,280 L 230,310 L 180,300 L 155,270 Z' },
  { id: 'AC', d: 'M 75,260 L 120,245 L 155,270 L 150,310 L 110,320 L 75,300 Z' },
  { id: 'TO', d: 'M 400,200 L 450,195 L 460,250 L 440,310 L 400,330 L 370,310 L 365,260 L 380,220 Z' },
  // Nordeste
  { id: 'MA', d: 'M 450,150 L 510,140 L 540,160 L 530,210 L 490,230 L 450,220 L 440,190 L 450,165 Z' },
  { id: 'PI', d: 'M 510,150 L 560,145 L 580,170 L 570,220 L 540,245 L 510,235 L 500,210 L 510,175 Z' },
  { id: 'CE', d: 'M 570,130 L 620,125 L 640,150 L 630,180 L 600,190 L 575,175 L 565,155 Z' },
  { id: 'RN', d: 'M 630,125 L 670,120 L 680,145 L 660,165 L 635,160 L 628,140 Z' },
  { id: 'PB', d: 'M 640,165 L 680,160 L 690,180 L 665,195 L 640,185 Z' },
  { id: 'PE', d: 'M 560,185 L 665,190 L 680,205 L 650,225 L 570,220 L 550,205 Z' },
  { id: 'AL', d: 'M 655,225 L 690,220 L 695,245 L 670,255 L 650,245 Z' },
  { id: 'SE', d: 'M 650,255 L 680,250 L 685,270 L 660,280 L 645,270 Z' },
  { id: 'BA', d: 'M 530,215 L 650,255 L 665,280 L 650,350 L 590,400 L 530,410 L 490,380 L 470,330 L 460,270 L 490,235 Z' },
  // Centro-Oeste
  { id: 'MT', d: 'M 200,280 L 320,270 L 370,300 L 380,370 L 340,420 L 270,430 L 210,410 L 185,360 L 185,310 Z' },
  { id: 'MS', d: 'M 260,430 L 380,420 L 400,470 L 370,510 L 310,520 L 260,500 L 245,465 Z' },
  { id: 'GO', d: 'M 380,330 L 450,320 L 470,370 L 460,430 L 420,450 L 380,445 L 360,405 L 365,360 Z' },
  { id: 'DF', d: 'M 420,385 L 435,382 L 438,398 L 425,402 Z' },
  // Sudeste
  { id: 'MG', d: 'M 460,330 L 540,310 L 590,340 L 600,400 L 570,450 L 510,470 L 460,455 L 430,420 L 440,370 Z' },
  { id: 'ES', d: 'M 600,370 L 630,360 L 640,400 L 620,425 L 598,408 Z' },
  { id: 'RJ', d: 'M 560,455 L 610,445 L 625,465 L 600,485 L 565,475 Z' },
  { id: 'SP', d: 'M 430,460 L 510,470 L 555,480 L 550,540 L 490,560 L 430,545 L 405,505 L 415,470 Z' },
  // Sul
  { id: 'PR', d: 'M 380,545 L 490,545 L 510,575 L 490,610 L 420,620 L 370,600 L 360,570 Z' },
  { id: 'SC', d: 'M 380,615 L 480,610 L 495,640 L 460,660 L 395,655 L 375,635 Z' },
  { id: 'RS', d: 'M 365,660 L 475,655 L 500,695 L 480,740 L 430,760 L 370,745 L 340,710 L 345,675 Z' },
]

// ── 6 fictional regions — each overlaid as a semi-transparent blob ───────────
// Positioned on top of real state groups with smooth polygon shapes
const REGIONS = [
  {
    id: 'aurora',
    nome: 'Região Aurora',
    // Overlaps AM + RO (Northwest Amazon)
    cx: 185, cy: 255,
    d: 'M 120,215 C 145,205 180,200 225,210 C 265,220 280,240 275,270 C 270,300 245,318 210,315 C 175,312 140,295 120,270 C 105,250 105,225 120,215 Z',
    labelX: 185, labelY: 258,
  },
  {
    id: 'central',
    nome: 'Região Central',
    // Overlaps GO + DF (Cerrado center)
    cx: 415, cy: 390,
    d: 'M 368,355 C 390,342 422,340 450,352 C 478,364 490,385 485,410 C 480,435 458,448 430,445 C 402,442 378,428 368,405 C 360,385 358,368 368,355 Z',
    labelX: 415, labelY: 393,
  },
  {
    id: 'esperanca',
    nome: 'Região Esperança',
    // Overlaps PI + CE + MA (Northeast transition)
    cx: 525, cy: 190,
    d: 'M 480,158 C 500,148 530,146 558,155 C 586,164 598,182 593,205 C 588,228 568,240 542,238 C 516,236 492,222 480,202 C 470,185 470,168 480,158 Z',
    labelX: 525, labelY: 193,
  },
  {
    id: 'horizonte',
    nome: 'Região Horizonte',
    // Overlaps PR + SC (South)
    cx: 432, cy: 590,
    d: 'M 372,562 C 395,550 425,547 458,554 C 491,561 510,578 508,600 C 506,622 485,636 455,635 C 425,634 398,620 378,602 C 362,587 360,573 372,562 Z',
    labelX: 432, labelY: 593,
  },
  {
    id: 'nova_uniao',
    nome: 'Nova União',
    // Overlaps SP + RJ (Southeast coast)
    cx: 510, cy: 500,
    d: 'M 462,470 C 484,458 515,456 542,466 C 569,476 582,496 575,518 C 568,540 546,550 518,547 C 490,544 466,530 455,510 C 446,493 448,478 462,470 Z',
    labelX: 510, labelY: 503,
  },
  {
    id: 'vale_verde',
    nome: 'Vale Verde',
    // Overlaps PA + TO (Pará/Tocantins)
    cx: 415, cy: 175,
    d: 'M 368,148 C 388,136 415,133 442,142 C 469,151 482,168 478,190 C 474,212 454,224 428,222 C 402,220 378,206 368,186 C 360,169 360,158 368,148 Z',
    labelX: 415, labelY: 178,
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
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null)

  const getFill = useCallback((id: string) => {
    const rec = recomendacoes[id]
    return rec ? REC_COLOR[rec] : '#4589ff'
  }, [recomendacoes])

  const getOpacity = useCallback((id: string) => {
    if (id === hovered) return 0.82
    if (id === selectedRegion) return 0.75
    return 0.38
  }, [hovered, selectedRegion])

  const legendItems = (Object.keys(REC_LABEL) as Recomendacao[]).filter(
    (r) => Object.values(recomendacoes).includes(r),
  )

  const hoveredRegion = REGIONS.find((r) => r.id === hovered)
  const hoveredRec = hovered ? recomendacoes[hovered] : undefined

  const handleMouseMove = useCallback((e: React.MouseEvent<SVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    setTooltipPos({ x: e.clientX - rect.left, y: e.clientY - rect.top })
  }, [])

  return (
    <div style={{ background: '#ffffff', border: '1px solid #e0e0e0', borderRadius: '6px', overflow: 'hidden' }}>

      {/* ── SVG ── */}
      {/* viewBox recortado para o bounding box real dos estados (x:55–710, y:25–775) */}
      <div style={{ position: 'relative', background: '#dbeafe' }}>
        <svg
          viewBox="55 25 655 755"
          style={{ width: '100%', height: 'auto', display: 'block', maxHeight: '420px' }}
          preserveAspectRatio="xMidYMid meet"
          aria-label="Mapa do Brasil com regiões simuladas"
          onMouseMove={handleMouseMove}
          onMouseLeave={() => { setHovered(null); setTooltipPos(null) }}
        >
          {/* Ocean background — covers the cropped viewBox area */}
          <rect x="55" y="25" width="655" height="755" fill="#dbeafe" />

          {/* ── State fills (base layer) ── */}
          <g>
            {STATES.map((s) => (
              <path
                key={s.id}
                d={s.d}
                fill="#c8daf0"
                stroke="#9ab8d8"
                strokeWidth="0.8"
              />
            ))}
          </g>

          {/* ── Region blobs (interactive layer) ── */}
          {REGIONS.map((region) => {
            const isSelected = region.id === selectedRegion
            const isPriority = priorityAlert[region.id]
            const fill = getFill(region.id)
            const opacity = getOpacity(region.id)

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
                {/* Glow / shadow for selected */}
                {isSelected && (
                  <path
                    d={region.d}
                    fill={fill}
                    opacity={0.25}
                    transform="scale(1.12) translate(-21,-18)"
                    style={{ filter: 'blur(6px)' }}
                  />
                )}

                {/* Main blob */}
                <path
                  d={region.d}
                  fill={fill}
                  fillOpacity={opacity}
                  stroke={isPriority ? '#da1e28' : isSelected ? '#161616' : fill}
                  strokeWidth={isSelected ? 2.5 : 1.5}
                  strokeDasharray={isPriority ? '5 2.5' : undefined}
                  style={{ transition: 'fill-opacity 0.18s ease' }}
                />

                {/* Pin dot */}
                <circle
                  cx={region.cx}
                  cy={region.cy}
                  r={isSelected ? 6 : 4}
                  fill={isSelected ? '#161616' : '#ffffff'}
                  stroke={fill}
                  strokeWidth="2"
                  style={{ transition: 'r 0.15s ease' }}
                />

                {/* Label */}
                <text
                  x={region.labelX}
                  y={region.labelY + 14}
                  textAnchor="middle"
                  fontSize={isSelected ? '9.5' : '8.5'}
                  fontWeight={isSelected ? '700' : '600'}
                  fill={isSelected ? '#161616' : '#1e3a5f'}
                  fontFamily="IBM Plex Sans, sans-serif"
                  style={{ pointerEvents: 'none', userSelect: 'none' }}
                >
                  {region.nome.replace('Região ', '')}
                </text>

                {/* Recommendation label */}
                {recomendacoes[region.id] && (
                  <text
                    x={region.labelX}
                    y={region.labelY + 25}
                    textAnchor="middle"
                    fontSize="7.5"
                    fontWeight="500"
                    fill={fill}
                    fontFamily="IBM Plex Sans, sans-serif"
                    style={{ pointerEvents: 'none', userSelect: 'none' }}
                  >
                    {REC_LABEL[recomendacoes[region.id]]}
                  </text>
                )}

                {/* Priority badge */}
                {isPriority && (
                  <text
                    x={region.cx + 16}
                    y={region.cy - 10}
                    fontSize="12"
                    style={{ pointerEvents: 'none', userSelect: 'none' }}
                    aria-hidden
                  >⚠</text>
                )}
              </g>
            )
          })}

          {/* Compass — positioned inside cropped viewBox (bottom-right corner) */}
          <g transform="translate(690,745)">
            <circle cx="0" cy="0" r="16" fill="rgba(255,255,255,0.75)" stroke="#9ab8d8" strokeWidth="1"/>
            <text x="0" y="-4" textAnchor="middle" fontSize="8" fontWeight="700" fill="#1e3a5f" fontFamily="IBM Plex Sans, sans-serif">N</text>
            <polygon points="0,-12 -3,-2 0,2 3,-2" fill="#1e3a5f" />
            <polygon points="0,12 -3,2 0,-2 3,2" fill="#9ab8d8" />
          </g>

          {/* Attribution — inside cropped viewBox */}
          <text x="382" y="772" textAnchor="middle" fontSize="8.5" fill="#94a9c0" fontFamily="IBM Plex Sans, sans-serif" fontStyle="italic">
            Regiões fictícias simuladas · Conecta Conselho · IBM SkillsBuild 2024
          </text>
        </svg>

        {/* Hover tooltip — follows cursor */}
        {hoveredRegion && tooltipPos && (
          <div
            style={{
              position: 'absolute',
              left: Math.min(tooltipPos.x + 14, 600),
              top: Math.max(tooltipPos.y - 56, 8),
              background: '#161616',
              color: '#ffffff',
              borderRadius: '4px',
              padding: '8px 12px',
              fontSize: '12px',
              lineHeight: 1.6,
              pointerEvents: 'none',
              whiteSpace: 'nowrap',
              boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
              zIndex: 10,
              borderLeft: `3px solid ${getFill(hoveredRegion.id)}`,
            }}
          >
            <p style={{ fontWeight: 700, margin: '0 0 2px', fontSize: '13px' }}>{hoveredRegion.nome}</p>
            {hoveredRec ? (
              <p style={{ margin: 0, color: REC_COLOR[hoveredRec], fontWeight: 600 }}>{REC_LABEL[hoveredRec]}</p>
            ) : (
              <p style={{ margin: 0, color: '#8d8d8d' }}>Não analisada</p>
            )}
            {priorityAlert[hoveredRegion.id] && (
              <p style={{ margin: '2px 0 0', color: '#da1e28', fontWeight: 700, fontSize: '11px' }}>⚠ Atenção Prioritária</p>
            )}
          </div>
        )}
      </div>

      {/* ── Caption + legend ── */}
      <div style={{
        background: '#f4f4f4', borderTop: '1px solid #e0e0e0',
        padding: '8px 14px', display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px',
      }}>
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
              <div style={{ width: 10, height: 10, borderRadius: 2, background: '#4589ff', opacity: 0.5, flexShrink: 0 }} />
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
