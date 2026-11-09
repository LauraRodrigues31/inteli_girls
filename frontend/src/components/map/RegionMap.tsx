import React, { useMemo, useCallback } from 'react'
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet'
import type { Layer } from 'leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { Recomendacao } from '../../types'

// ── Fix Leaflet's broken default icon paths when bundled with Vite ──────────
// Without this, marker icons show as broken images.
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

// ── Fictional region polygons (2×3 grid, centered on Brazil) ────────────────
const REGION_GEOJSON = {
  type: 'FeatureCollection' as const,
  features: [
    {
      type: 'Feature' as const,
      properties: { id: 'aurora', nome: 'Região Aurora' },
      geometry: {
        type: 'Polygon' as const,
        coordinates: [[[-53, -10], [-49, -10], [-49, -13], [-53, -13], [-53, -10]]],
      },
    },
    {
      type: 'Feature' as const,
      properties: { id: 'central', nome: 'Região Central' },
      geometry: {
        type: 'Polygon' as const,
        coordinates: [[[-48, -10], [-44, -10], [-44, -13], [-48, -13], [-48, -10]]],
      },
    },
    {
      type: 'Feature' as const,
      properties: { id: 'esperanca', nome: 'Região Esperança' },
      geometry: {
        type: 'Polygon' as const,
        coordinates: [[[-43, -10], [-39, -10], [-39, -13], [-43, -13], [-43, -10]]],
      },
    },
    {
      type: 'Feature' as const,
      properties: { id: 'horizonte', nome: 'Região Horizonte' },
      geometry: {
        type: 'Polygon' as const,
        coordinates: [[[-53, -14], [-49, -14], [-49, -17], [-53, -17], [-53, -14]]],
      },
    },
    {
      type: 'Feature' as const,
      properties: { id: 'nova_uniao', nome: 'Nova União' },
      geometry: {
        type: 'Polygon' as const,
        coordinates: [[[-48, -14], [-44, -14], [-44, -17], [-48, -17], [-48, -14]]],
      },
    },
    {
      type: 'Feature' as const,
      properties: { id: 'vale_verde', nome: 'Vale Verde' },
      geometry: {
        type: 'Polygon' as const,
        coordinates: [[[-43, -14], [-39, -14], [-39, -17], [-43, -17], [-43, -14]]],
      },
    },
  ],
}

const REC_COLOR: Record<Recomendacao, string> = {
  investir_agora:  '#24a148',
  realizar_piloto: '#0043ce',
  aguardar:        '#f1c21b',
  escalar_humano:  '#da1e28',
}

const REC_LABEL: Record<Recomendacao, string> = {
  investir_agora:  'Investir Agora',
  realizar_piloto: 'Realizar Piloto',
  aguardar:        'Aguardar',
  escalar_humano:  'Escalar a Humano',
}

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

  const getStyle = useCallback(
    (feature?: { properties?: { id?: string } }) => {
      const id = feature?.properties?.id ?? ''
      const rec = recomendacoes[id]
      const isSelected = id === selectedRegion
      const isPriority = priorityAlert[id]
      return {
        fillColor:   rec ? REC_COLOR[rec] : '#c6c6c6',
        fillOpacity: isSelected ? 0.80 : 0.45,
        color:       isPriority ? '#da1e28' : isSelected ? '#161616' : '#8d8d8d',
        weight:      isPriority || isSelected ? 3 : 1.5,
        dashArray:   isPriority ? '6 3' : undefined,
      }
    },
    [recomendacoes, selectedRegion, priorityAlert],
  )

  const onEachFeature = useCallback(
    (feature: { properties?: { id?: string; nome?: string } }, layer: Layer) => {
      const id   = feature.properties?.id   ?? ''
      const nome = feature.properties?.nome ?? id
      const rec  = recomendacoes[id]

      layer.on({
        click: () => onSelectRegion(id),
        mouseover: (e) => {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const l = e.target as any
          l.setStyle({ fillOpacity: 0.9, weight: 3, color: '#161616' })
          l.bringToFront()
        },
        mouseout: (e) => {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const l = e.target as any
          l.setStyle(getStyle(feature))
        },
      })

      const recLabel = rec ? `<br><b style="color:${REC_COLOR[rec]}">${REC_LABEL[rec]}</b>` : '<br><span style="color:#8d8d8d">Não analisada</span>'
      const isPriority = priorityAlert[id]
      const priorityBadge = isPriority ? '<br><span style="color:#da1e28;font-weight:700">⚠ Atenção Prioritária</span>' : ''

      layer.bindTooltip(
        `<div style="font-family:IBM Plex Sans,sans-serif;font-size:13px;padding:2px 4px">
           <b>${nome}</b>${recLabel}${priorityBadge}
         </div>`,
        { sticky: true, direction: 'top', className: 'cc-tooltip' },
      )
    },
    [recomendacoes, priorityAlert, selectedRegion, onSelectRegion, getStyle],
  )

  // Unique key forces GeoJSON re-render when selection or recommendations change
  const geoKey = `${selectedRegion}|${Object.entries(recomendacoes).sort().join(',')}`

  // Which recommendations are present — for legend
  const legendItems = useMemo(() => {
    const seen = new Set(Object.values(recomendacoes))
    return (Object.keys(REC_LABEL) as Recomendacao[]).filter((r) => seen.has(r))
  }, [recomendacoes])

  return (
    <div style={{ position: 'relative', width: '100%', borderRadius: '6px', overflow: 'hidden', border: '1px solid #e0e0e0' }}>
      {/* Map */}
      <div style={{ height: '320px' }}>
        <MapContainer
          center={[-13.5, -46]}
          zoom={5}
          style={{ width: '100%', height: '100%' }}
          zoomControl
          attributionControl={false}
          scrollWheelZoom={false}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; CARTO'
          />
          <GeoJSON
            key={geoKey}
            data={REGION_GEOJSON}
            style={getStyle}
            onEachFeature={onEachFeature}
          />
        </MapContainer>
      </div>

      {/* Caption */}
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

        {/* Dynamic legend — only shows recs that have been calculated */}
        {legendItems.length > 0 && (
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            {legendItems.map((rec) => (
              <div key={rec} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <div
                  style={{
                    width: 12,
                    height: 12,
                    borderRadius: 2,
                    background: REC_COLOR[rec],
                    flexShrink: 0,
                  }}
                />
                <span style={{ fontSize: '11px', color: '#525252' }}>{REC_LABEL[rec]}</span>
              </div>
            ))}
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ width: 12, height: 12, borderRadius: 2, background: '#c6c6c6', flexShrink: 0 }} />
              <span style={{ fontSize: '11px', color: '#525252' }}>Não analisada</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
