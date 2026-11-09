import React from 'react'
import {
  Header,
  HeaderName,
  HeaderNavigation,
  HeaderMenuItem,
  HeaderGlobalBar,
  HeaderGlobalAction,
  SkipToContent,
  Tag,
} from '@carbon/react'
import { Warning } from '@carbon/icons-react'
import { useNavigate, useLocation } from 'react-router-dom'

export function AppHeader() {
  const navigate = useNavigate()
  const location = useLocation()

  const navItems = [
    { label: 'Como Funciona', path: '/' },
    { label: 'Análise de Região', path: '/analise' },
    { label: 'Simulador', path: '/simulador' },
  ]

  return (
    <Header aria-label="Conecta Conselho">
      <SkipToContent />
      <HeaderName
        href="/"
        prefix=""
        onClick={(e) => {
          e.preventDefault()
          navigate('/')
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* IBM 8-bar logo */}
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
          >
            {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
              <rect
                key={i}
                x={i * 3}
                y={i % 2 === 0 ? 4 : 8}
                width="2"
                height={i % 2 === 0 ? 16 : 8}
                fill="#0f62fe"
              />
            ))}
          </svg>
          Conecta Conselho
        </span>
      </HeaderName>

      <HeaderNavigation aria-label="Navegação principal">
        {navItems.map(({ label, path }) => (
          <HeaderMenuItem
            key={path}
            href={path}
            isActive={location.pathname === path}
            onClick={(e: React.MouseEvent) => {
              e.preventDefault()
              navigate(path)
            }}
          >
            {label}
          </HeaderMenuItem>
        ))}
      </HeaderNavigation>

      <HeaderGlobalBar>
        <HeaderGlobalAction aria-label="Dados simulados" tooltipAlignment="end">
          <Warning size={20} />
        </HeaderGlobalAction>
      </HeaderGlobalBar>
    </Header>
  )
}
