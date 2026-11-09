import React, { useMemo } from 'react'
import { MapContainer, TileLayer, GeoJSON, Tooltip } from 'react-leaflet'
import type { Layer, LeafletMouseEvent } from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { Recomendacao } from '../../types'

// ─── Fictional region polygons arranged in a 2×3 grid centered on Brazil ───

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
  investir_agora: '#24a148',
  realizar_piloto: '#0043ce',
  aguardar: '#f1c21b',
  escalar_humano: '#da1e28',
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
  const style = useMemo(
    () =>
      (feature?: { properties?: { id?: string } }) => {
        const id = feature?.properties?.id ?? ''
        const rec = recomendacoes[id]
        const isSelected = id === selectedRegion
        const isPriority = priorityAlert[id]

        return {
          fillColor: rec ? REC_COLOR[rec] : '#8d8d8d',
          fillOpacity: isSelected ? 0.75 : 0.45,
          color: isPriority ? '#da1e28' : isSelected ? '#161616' : '#525252',
          weight: isPriority || isSelected ? 3 : 1,
          dashArray: isPriority ? '6 3' : undefined,
        }
      },
    [recomendacoes, selectedRegion, priorityAlert],
  )

  function onEachFeature(
    feature: { properties?: { id?: string; nome?: string } },
    layer: Layer,
  ) {
    const id = feature.properties?.id ?? ''
    const nome = feature.properties?.nome ?? id

    layer.on({
      click: () => onSelectRegion(id),
      mouseover: (e: LeafletMouseEvent) => {
        const l = e.target as { setStyle: (s: object) => void }
        l.setStyle({ fillOpacity: 0.85, weight: 2 })
      },
      mouseout: (e: LeafletMouseEvent) => {
        const l = e.target as { setStyle: (s: object) => void; options: object }
        l.setStyle(style(feature))
      },
    })

    // @ts-expect-error leaflet types
    layer.bindTooltip(nome, { permanent: false, direction: 'center', className: 'cc-tooltip' })
  }

  return (
    <div style={{ width: '100%', height: '340px', borderRadius: '4px', overflow: 'hidden' }}>
      <MapContainer
        center={[-13.5, -46]}
        zoom={5}
        style={{ width: '100%', height: '100%' }}
        zoomControl
        attributionControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com">CARTO</a>'
        />
        <GeoJSON
          key={`${selectedRegion}-${JSON.stringify(recomendacoes)}`}
          data={REGION_GEOJSON}
          style={style}
          onEachFeature={onEachFeature}
        />
      </MapContainer>
    </div>
  )
}
