import React, { useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import { Content, ToastNotification, ToastNotificationProps } from '@carbon/react'
import { AppHeader } from './components/layout/AppHeader'
import { SimulatedDataBanner } from './components/layout/SimulatedDataBanner'
import { AppProvider, useApp } from './context/AppContext'
import ComoFunciona from './pages/ComoFunciona'
import Analise from './pages/Analise'
import Simulador from './pages/Simulador'

function ToastStack() {
  const { state, removeToast } = useApp()
  return (
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
      }}
    >
      {state.toasts.map((toast) => (
        <ToastNotification
          key={toast.id}
          kind={toast.kind as ToastNotificationProps['kind']}
          title={toast.title}
          subtitle={toast.subtitle}
          onClose={() => removeToast(toast.id)}
          timeout={5000}
        />
      ))}
    </div>
  )
}

function AppInner() {
  return (
    <>
      <AppHeader />
      <SimulatedDataBanner />
      <Content style={{ paddingTop: 0, paddingLeft: 0, paddingRight: 0, paddingBottom: 0 }}>
        <Routes>
          <Route path="/" element={<ComoFunciona />} />
          <Route path="/analise" element={<Analise />} />
          <Route path="/simulador" element={<Simulador />} />
          <Route path="*" element={<ComoFunciona />} />
        </Routes>
      </Content>
      <ToastStack />
    </>
  )
}

export default function App() {
  return (
    <AppProvider>
      <AppInner />
    </AppProvider>
  )
}
