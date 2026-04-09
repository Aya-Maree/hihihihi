import { Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import PlanEvent from './pages/PlanEvent'
import Artifacts from './pages/Artifacts'
import KnowledgeBase from './pages/KnowledgeBase'

export default function App() {
  const [sessionId, setSessionId] = useState(() => localStorage.getItem('session_id') || null)
  const [eventContext, setEventContext] = useState(null)
  const [workflowState, setWorkflowState] = useState('intake')
  const [artifactsReady, setArtifactsReady] = useState(false)

  useEffect(() => {
    if (sessionId) localStorage.setItem('session_id', sessionId)
  }, [sessionId])

  const handleSessionCreated = (id) => {
    setSessionId(id)
    setEventContext(null)
    setWorkflowState('intake')
    setArtifactsReady(false)
  }

  const sharedProps = {
    sessionId,
    eventContext,
    workflowState,
    artifactsReady,
    onSessionCreated: handleSessionCreated,
    onContextUpdate: setEventContext,
    onWorkflowUpdate: setWorkflowState,
    onArtifactsReady: setArtifactsReady,
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar
        sessionId={sessionId}
        workflowState={workflowState}
        artifactsReady={artifactsReady}
        onNewSession={() => {
          localStorage.removeItem('session_id')
          handleSessionCreated(null)
        }}
      />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Routes>
          <Route path="/" element={<Dashboard {...sharedProps} />} />
          <Route path="/plan" element={<PlanEvent {...sharedProps} />} />
          <Route path="/artifacts" element={<Artifacts {...sharedProps} />} />
          <Route path="/knowledge-base" element={<KnowledgeBase />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
