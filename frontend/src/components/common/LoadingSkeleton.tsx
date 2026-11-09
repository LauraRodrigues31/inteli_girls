import React from 'react'
import { SkeletonText, SkeletonPlaceholder, Tile } from '@carbon/react'

export function LoadingSkeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <Tile style={{ padding: '24px' }}>
        <SkeletonText heading width="40%" />
        <SkeletonText paragraph lineCount={3} />
      </Tile>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        {[0, 1, 2, 3, 4].map((i) => (
          <Tile key={i} style={{ padding: '20px' }}>
            <SkeletonText heading width="60%" />
            <SkeletonPlaceholder style={{ width: '100%', height: '12px', marginTop: '8px' }} />
            <SkeletonText paragraph lineCount={2} />
          </Tile>
        ))}
      </div>
    </div>
  )
}

export function SkeletonCard() {
  return (
    <Tile style={{ padding: '20px' }}>
      <SkeletonText heading width="50%" />
      <SkeletonPlaceholder style={{ width: '100%', height: '8px', marginTop: '8px' }} />
      <SkeletonText paragraph lineCount={2} />
    </Tile>
  )
}
