import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Calendar, Sparkles, ArrowRight, CheckSquare, ShoppingCart, Clock,
  Brain, Database, GitBranch, Layers
} from 'lucide-react'
import { createSession, getHealth } from '../api/client'
import toast from 'react-hot-toast'

export default function Dashboard({ onSessionCreated }) {
  const navigate = useNavigate()
  const [health, setHealth] = useState(null)
  const [creating, setCreating] = useState(false)
  const [hostName, setHostName] = useState('')

  useEffect(() => {
    getHealth().then((r) => setHealth(r.data)).catch(() => {})
  }, [])

  const handleStart = async () => {
    setCreating(true)
    try {
      const res = await createSession(hostName || null)
      onSessionCreated(res.data.session_id)
      toast.success('Planning session started!')
      navigate('/plan')
    } catch (err) {
      toast.error('Failed to create session. Is the backend running?')
    } finally {
      setCreating(false)
    }
  }

  const examples = [
    { type: 'Birthday Party', icon: '🎂', desc: '20 guests · $300 budget · at home' },
    { type: 'Dinner Party', icon: '🍽️', desc: '8 guests · $150 budget · formal' },
    { type: 'Holiday Gathering', icon: '🎄', desc: '30 guests · potluck style' },
    { type: 'Graduation Party', icon: '🎓', desc: '25 guests · backyard · casual' },
  ]

  const features = [
    {
      icon: Database,
      color: 'text-blue-600 bg-blue-50',
      title: 'RAG Knowledge Base',
      desc: '12 curated planning documents · sentence-transformers (all-MiniLM-L6-v2) · ChromaDB vector store · semantic retrieval with citations',
    },
    {
      icon: GitBranch,
      color: 'text-purple-600 bg-purple-50',
      title: '7-Step Planning Workflow',
      desc: 'Intake → Clarification → Retrieval → Conflict Detection → Planning → Validation → Artifacts',
    },
    {
      icon: Brain,
      color: 'text-green-600 bg-green-50',
      title: 'Persistent Memory',
      desc: 'Full session state · chat history · event context object persisted across turns',
    },
    {
      icon: Layers,
      color: 'text-orange-600 bg-orange-50',
      title: 'Structured Artifacts',
      desc: 'Task Checklist · Itemized Shopping List · Day-of Schedule — in JSON + Markdown',
    },
  ]

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="bg-gradient-to-br from-purple-600 to-indigo-600 rounded-2xl p-8 text-white">
        <div className="max-w-2xl">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-5 h-5 text-yellow-300" />
            <span className="text-sm text-purple-200">EventOps AI · SE4471B Course Project</span>
          </div>
          <h1 className="text-3xl font-bold mb-3">Household Event Planner</h1>
          <p className="text-purple-100 mb-6 leading-relaxed">
            AI-powered planning for birthday parties, dinner parties, holiday gatherings, and more.
            Generates complete task checklists, shopping lists, and day-of schedules — grounded in
            a curated knowledge base with citations.
          </p>

          <div className="flex gap-3 items-end flex-wrap">
            <div className="flex-1 min-w-[200px] max-w-xs">
              <label className="text-xs text-purple-200 mb-1 block">Your name (optional)</label>
              <input
                value={hostName}
                onChange={(e) => setHostName(e.target.value)}
                placeholder="e.g. Sara"
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-purple-300 text-sm focus:outline-none focus:ring-2 focus:ring-white/30"
                onKeyDown={(e) => e.key === 'Enter' && handleStart()}
              />
            </div>
            <button
              onClick={handleStart}
              disabled={creating}
              className="flex items-center gap-2 bg-white text-purple-600 font-semibold px-6 py-2 rounded-lg hover:bg-purple-50 transition-colors disabled:opacity-70"
            >
              {creating ? 'Starting…' : 'Start Planning'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* System status */}
      {health && (
        <div className="card p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">System Status</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatusItem
              label="Knowledge Base"
              value={`${health.rag_documents} docs`}
              ok={health.rag_documents > 0}
            />
            <StatusItem
              label="Gemini AI"
              value={health.google_api_key ? health.gemini_model : 'Demo Mode'}
              ok={health.google_api_key}
              warnText="Set GOOGLE_API_KEY in .env"
            />
            <StatusItem
              label="Spoonacular"
              value={health.spoonacular_api_key ? 'Connected' : 'Not configured'}
              ok={health.spoonacular_api_key}
              warnText="Set SPOONACULAR_API_KEY (optional)"
            />
            <StatusItem
              label="Active Sessions"
              value={health.active_sessions}
              ok={true}
            />
          </div>
        </div>
      )}

      {/* Event type quick-starts */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Plan Your Event</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {examples.map((ex) => (
            <button
              key={ex.type}
              onClick={handleStart}
              className="card p-4 text-left hover:shadow-md hover:border-purple-200 transition-all group"
            >
              <span className="text-2xl mb-2 block">{ex.icon}</span>
              <p className="font-medium text-sm text-gray-900 group-hover:text-purple-700">{ex.type}</p>
              <p className="text-xs text-gray-400 mt-0.5">{ex.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Features */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">System Capabilities</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {features.map((f) => (
            <div key={f.title} className="card p-4 flex gap-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${f.color}`}>
                <f.icon className="w-5 h-5" />
              </div>
              <div>
                <p className="font-medium text-sm text-gray-900">{f.title}</p>
                <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Artifacts preview */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Generated Artifacts</h2>
        <div className="grid grid-cols-3 gap-3">
          {[
            { icon: CheckSquare, color: 'text-purple-600 bg-purple-50', title: 'Task Checklist', desc: 'Prioritized by timeline: 4+ weeks, 2-4 weeks, 1 week, day-before, day-of' },
            { icon: ShoppingCart, color: 'text-blue-600 bg-blue-50', title: 'Shopping List', desc: 'Itemized with quantities, costs, categories, and budget tracking' },
            { icon: Clock, color: 'text-green-600 bg-green-50', title: 'Day-of Schedule', desc: 'Time-blocked with setup, event, and cleanup sections' },
          ].map(({ icon: Icon, color, title, desc }) => (
            <div key={title} className="card p-4">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center mb-2 ${color}`}>
                <Icon className="w-4 h-4" />
              </div>
              <p className="font-medium text-sm text-gray-900">{title}</p>
              <p className="text-xs text-gray-400 mt-1 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function StatusItem({ label, value, ok, warnText }) {
  return (
    <div className="text-center">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <div className="flex items-center justify-center gap-1">
        <span className={`w-2 h-2 rounded-full ${ok ? 'bg-green-400' : 'bg-yellow-400'}`} />
        <span className="text-sm font-medium text-gray-800">{value}</span>
      </div>
      {!ok && warnText && (
        <p className="text-xs text-yellow-600 mt-0.5">{warnText}</p>
      )}
    </div>
  )
}
