import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, Settings, PanelLeft } from 'lucide-react'
import toast from 'react-hot-toast'
import ChatBox from '../components/ChatBox'
import WorkflowProgress from '../components/WorkflowProgress'
import EventContextPanel from '../components/EventContextPanel'
import { createSession, sendChat, getChatHistory, getEventContext, startPlanning, generateArtifacts } from '../api/client'

const INTAKE_FORM_FIELDS = [
  { key: 'event_type', label: 'Event Type', placeholder: 'e.g. Birthday Party', required: true },
  { key: 'event_date', label: 'Event Date', type: 'date', required: true },
  { key: 'event_time', label: 'Event Time', type: 'time' },
  { key: 'guest_count', label: 'Guest Count', type: 'number', placeholder: '20', required: true },
  { key: 'budget', label: 'Total Budget ($)', type: 'number', placeholder: '300', required: true },
  { key: 'venue_type', label: 'Venue Type', placeholder: 'home / rented hall / outdoor' },
  { key: 'theme', label: 'Theme (optional)', placeholder: 'e.g. Tropical, Vintage, Sports' },
  { key: 'dietary_restrictions', label: 'Dietary Restrictions', placeholder: 'vegetarian, vegan, nut-free…' },
  { key: 'event_duration_hours', label: 'Duration (hours)', type: 'number', placeholder: '3' },
]

export default function PlanEvent({
  sessionId,
  onSessionCreated,
  onContextUpdate,
  onWorkflowUpdate,
  onArtifactsReady,
  workflowState,
}) {
  const navigate = useNavigate()
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [eventContext, setEventContext] = useState(null)
  const [localWorkflowState, setLocalWorkflowState] = useState(workflowState || 'intake')
  const [showForm, setShowForm] = useState(true)
  const [showSidebar, setShowSidebar] = useState(true)
  const [formData, setFormData] = useState({})
  const [generatingArtifacts, setGeneratingArtifacts] = useState(false)
  const [enrichSpoonacular, setEnrichSpoonacular] = useState(false)

  // Initialize session if needed
  useEffect(() => {
    const init = async () => {
      let sid = sessionId
      if (!sid) {
        try {
          const res = await createSession(null)
          sid = res.data.session_id
          onSessionCreated(sid)
        } catch {
          toast.error('Backend not reachable. Start the server first.')
          return
        }
      }
      loadHistory(sid)
      loadContext(sid)
    }
    init()
  }, [])

  const loadHistory = async (sid) => {
    try {
      const res = await getChatHistory(sid, 50)
      const msgs = res.data.messages.map((m) => ({
        role: m.role,
        content: m.content,
        timestamp: m.timestamp,
        citations: m.metadata?.citations || [],
        conflicts: m.metadata?.conflicts || [],
      }))
      setMessages(msgs)
    } catch {}
  }

  const loadContext = async (sid) => {
    try {
      const res = await getEventContext(sid)
      setEventContext(res.data.event_context)
      setLocalWorkflowState(res.data.workflow_state)
      onContextUpdate?.(res.data.event_context)
      onWorkflowUpdate?.(res.data.workflow_state)
    } catch {}
  }

  const handleSend = async (message) => {
    if (!sessionId) {
      toast.error('No active session')
      return
    }
    setMessages((prev) => [...prev, { role: 'user', content: message, timestamp: new Date().toISOString() }])
    setLoading(true)

    try {
      const res = await sendChat(sessionId, message)
      const data = res.data

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.response,
          timestamp: new Date().toISOString(),
          citations: data.citations || [],
          conflicts: data.conflicts || [],
        },
      ])

      setEventContext(data.event_context)
      setLocalWorkflowState(data.workflow_state)
      onContextUpdate?.(data.event_context)
      onWorkflowUpdate?.(data.workflow_state)

      if (data.artifacts_ready) {
        onArtifactsReady?.(true)
        toast.success('Artifacts are ready! Check the Artifacts tab.', { duration: 4000 })
      }
    } catch (err) {
      toast.error('Failed to get response. Check backend.')
      setMessages((prev) => prev.slice(0, -1))
    } finally {
      setLoading(false)
    }
  }

  const handleFormSubmit = async (e) => {
    e.preventDefault()
    if (!sessionId) {
      toast.error('No active session')
      return
    }
    setLoading(true)

    const payload = {
      event_type: formData.event_type || undefined,
      event_date: formData.event_date || undefined,
      event_time: formData.event_time || undefined,
      guest_count: formData.guest_count ? parseInt(formData.guest_count) : undefined,
      budget: formData.budget ? parseFloat(formData.budget) : undefined,
      venue_type: formData.venue_type || undefined,
      theme: formData.theme || undefined,
      dietary_restrictions: formData.dietary_restrictions
        ? formData.dietary_restrictions.split(',').map((s) => s.trim()).filter(Boolean)
        : undefined,
      event_duration_hours: formData.event_duration_hours ? parseFloat(formData.event_duration_hours) : undefined,
      has_children: formData.has_children || false,
      has_elderly: formData.has_elderly || false,
    }

    try {
      const res = await startPlanning(sessionId, payload)
      const data = res.data

      setMessages([
        { role: 'user', content: `I want to plan a ${formData.event_type || 'event'}.`, timestamp: new Date().toISOString() },
        {
          role: 'assistant',
          content: data.response,
          timestamp: new Date().toISOString(),
          citations: data.citations || [],
          conflicts: data.conflicts || [],
        },
      ])

      setEventContext(data.event_context)
      setLocalWorkflowState(data.workflow_state)
      onContextUpdate?.(data.event_context)
      onWorkflowUpdate?.(data.workflow_state)
      setShowForm(false)

      toast.success('Planning started!')
    } catch (err) {
      toast.error('Failed to start planning.')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateArtifacts = async () => {
    if (!sessionId) return
    setGeneratingArtifacts(true)
    try {
      const res = await generateArtifacts(sessionId, enrichSpoonacular)
      onArtifactsReady?.(true)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.data.message,
          timestamp: new Date().toISOString(),
          citations: res.data.citations || [],
        },
      ])
      toast.success('Artifacts generated!')
      navigate('/artifacts')
    } catch {
      toast.error('Failed to generate artifacts.')
    } finally {
      setGeneratingArtifacts(false)
    }
  }

  return (
    <div className="flex gap-4 h-[calc(100vh-120px)]">
      {/* Sidebar */}
      {showSidebar && (
        <div className="w-64 flex-shrink-0 space-y-3 overflow-y-auto">
          <WorkflowProgress currentStep={localWorkflowState} />
          <EventContextPanel context={eventContext} />

          {/* Generate artifacts button */}
          {(localWorkflowState === 'validation' || localWorkflowState === 'complete' || localWorkflowState === 'planning') && (
            <div className="card p-3 space-y-2">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Generate Plan</h3>
              <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enrichSpoonacular}
                  onChange={(e) => setEnrichSpoonacular(e.target.checked)}
                  className="accent-purple-600"
                />
                Enrich with Spoonacular recipes
              </label>
              <button
                onClick={handleGenerateArtifacts}
                disabled={generatingArtifacts}
                className="btn-primary w-full text-xs flex items-center justify-center gap-1"
              >
                <FileText className="w-3 h-3" />
                {generatingArtifacts ? 'Generating…' : 'Generate All Artifacts'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Main chat panel */}
      <div className="flex-1 card flex flex-col overflow-hidden">
        {/* Chat header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <PanelLeft className="w-4 h-4 text-gray-400" />
            </button>
            <h2 className="font-semibold text-gray-900 text-sm">AI Event Planner</h2>
            <span className="text-xs text-gray-400">
              {sessionId ? `Session: ${sessionId.slice(0, 8)}` : 'No session'}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {showForm && (
              <button
                onClick={() => setShowForm(!showForm)}
                className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1"
              >
                <Settings className="w-3.5 h-3.5" />
                Form
              </button>
            )}
          </div>
        </div>

        {/* Intake Form overlay */}
        {showForm && (
          <div className="flex-1 overflow-y-auto p-4">
            <div className="max-w-xl mx-auto">
              <h3 className="font-semibold text-gray-900 mb-1">Plan Your Event</h3>
              <p className="text-sm text-gray-500 mb-4">
                Fill in the form to start planning, or skip to chat directly.
              </p>
              <form onSubmit={handleFormSubmit} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  {INTAKE_FORM_FIELDS.map((field) => (
                    <div key={field.key} className={field.key === 'dietary_restrictions' ? 'col-span-2' : ''}>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        {field.label}
                        {field.required && <span className="text-red-500 ml-0.5">*</span>}
                      </label>
                      <input
                        type={field.type || 'text'}
                        placeholder={field.placeholder}
                        value={formData[field.key] || ''}
                        onChange={(e) => setFormData((p) => ({ ...p, [field.key]: e.target.value }))}
                        className="input"
                      />
                    </div>
                  ))}
                  <div className="col-span-2 flex gap-4">
                    <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.has_children || false}
                        onChange={(e) => setFormData((p) => ({ ...p, has_children: e.target.checked }))}
                        className="accent-purple-600"
                      />
                      Children attending
                    </label>
                    <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.has_elderly || false}
                        onChange={(e) => setFormData((p) => ({ ...p, has_elderly: e.target.checked }))}
                        className="accent-purple-600"
                      />
                      Elderly guests
                    </label>
                  </div>
                </div>

                <div className="flex gap-2 pt-2">
                  <button type="submit" className="btn-primary flex-1" disabled={loading}>
                    {loading ? 'Starting…' : 'Start Planning →'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    className="btn-secondary"
                  >
                    Chat Instead
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Chat */}
        {!showForm && (
          <div className="flex-1 overflow-hidden">
            <ChatBox
              messages={messages}
              onSend={handleSend}
              loading={loading}
              workflowState={localWorkflowState}
            />
          </div>
        )}
      </div>
    </div>
  )
}
