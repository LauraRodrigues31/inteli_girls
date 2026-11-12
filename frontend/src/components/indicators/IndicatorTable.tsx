import { StructuredListWrapper, StructuredListHead, StructuredListRow, StructuredListCell, StructuredListBody } from '@carbon/react'

function formatValue(v: unknown, key = ''): string {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'boolean') return v ? 'Sim' : 'Não'
  if (Array.isArray(v)) return v.length > 0 ? v.join(', ') : '—'
  if (typeof v === 'number') {
    // Só campos em reais (chave termina em _reais) recebem o prefixo R$
    if (/_reais$/i.test(key)) {
      return `R$ ${v.toLocaleString('pt-BR', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
    }
    return v.toLocaleString('pt-BR')
  }
  return String(v)
}

function humanizeKey(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/Reais$/i, '(R$)')
    .replace(/Pct$/i, '(%)')
    .replace(/Km$/i, '(km)')
    .replace(/Meses$/i, '(meses)')
}

interface IndicatorTableProps {
  data: Record<string, unknown>
}

export function IndicatorTable({ data }: IndicatorTableProps) {
  const rows = Object.entries(data)

  return (
    <StructuredListWrapper>
      <StructuredListHead>
        <StructuredListRow head>
          <StructuredListCell head>Indicador</StructuredListCell>
          <StructuredListCell head>Valor</StructuredListCell>
        </StructuredListRow>
      </StructuredListHead>
      <StructuredListBody>
        {rows.map(([key, value]) => (
          <StructuredListRow key={key}>
            <StructuredListCell noWrap>{humanizeKey(key)}</StructuredListCell>
            <StructuredListCell>
              {Array.isArray(value) ? (
                <ul style={{ paddingLeft: '18px', margin: 0, fontSize: '13px' }}>
                  {value.map((v, i) => (
                    <li key={i}>{v}</li>
                  ))}
                </ul>
              ) : (
                formatValue(value, key)
              )}
            </StructuredListCell>
          </StructuredListRow>
        ))}
      </StructuredListBody>
    </StructuredListWrapper>
  )
}
