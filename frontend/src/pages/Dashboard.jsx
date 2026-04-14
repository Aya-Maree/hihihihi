import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Calendar, Sparkles, ArrowRight, CheckSquare, ShoppingCart, Clock,
  MessageCircle, BookOpen, ListChecks, Star, Globe
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
      icon: BookOpen,
      color: 'text-blue-600 bg-blue-50',
      title: 'Smart Planning Tips',
      desc: 'Your assistant pulls from a library of curated event planning guides to give you advice that actually works.',
    },
    {
      icon: MessageCircle,
      color: 'text-purple-600 bg-purple-50',
      title: 'Conversational Planning',
      desc: 'Just chat naturally — describe your event and answer a few questions. No complicated forms.',
    },
    {
      icon: ListChecks,
      color: 'text-green-600 bg-green-50',
      title: 'Remembers Everything',
      desc: "Keeps track of all your event details as you chat, so you don't have to repeat yourself.",
    },
    {
      icon: Star,
      color: 'text-orange-600 bg-orange-50',
      title: 'Ready-to-Use Documents',
      desc: 'Get a complete task checklist, shopping list, and day-of schedule — all ready to print or share.',
    },
    {
      icon: Globe,
      color: 'text-teal-600 bg-teal-50',
      title: 'Find Local Vendors',
      desc: 'Search the web for rentals, caterers, decorators, and entertainers near you — all in one place.',
      link: '/vendor-search',
    },
  ]

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="bg-gradient-to-br from-purple-600 to-indigo-600 rounded-2xl p-8 text-white">
        <div className="max-w-2xl">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-5 h-5 text-yellow-300" />
            <span className="text-sm text-purple-200">Your personal event planning assistant</span>
          </div>
          <h1 className="text-3xl font-bold mb-3">Plan Your Next Event</h1>
          <p className="text-purple-100 mb-6 leading-relaxed">
            Tell us about your event and we'll guide you through every step — from the guest list
            to the day-of schedule. Birthday parties, dinner parties, holiday gatherings, and more.
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

      {/* Status strip — only show if something needs attention */}
      {health && !health.google_api_key && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl px-4 py-3 flex items-center gap-2 text-sm text-yellow-800">
          <Sparkles className="w-4 h-4 text-yellow-500 flex-shrink-0" />
          <span>
            The AI assistant is running in <strong>demo mode</strong>. Add a Google Gemini API key
            for full responses.
          </span>
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
        <h2 className="text-lg font-semibold text-gray-900 mb-3">How It Works</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {features.map((f) => {
            const inner = (
              <>
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${f.color}`}>
                  <f.icon className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-medium text-sm text-gray-900">{f.title}</p>
                  <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{f.desc}</p>
                  {f.link && <span className="text-xs text-teal-600 font-medium mt-1 block">Open →</span>}
                </div>
              </>
            )
            return f.link ? (
              <button
                key={f.title}
                onClick={() => navigate(f.link)}
                className="card p-4 flex gap-3 text-left hover:shadow-md hover:border-teal-200 transition-all"
              >
                {inner}
              </button>
            ) : (
              <div key={f.title} className="card p-4 flex gap-3">
                {inner}
              </div>
            )
          })}
        </div>
      </div>

      {/* Artifacts preview */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">What You'll Get</h2>
        <div className="grid grid-cols-3 gap-3">
          {[
            { icon: CheckSquare, color: 'text-purple-600 bg-purple-50', title: 'Task Checklist', desc: 'Everything you need to do, organised by how far in advance to do it' },
            { icon: ShoppingCart, color: 'text-blue-600 bg-blue-50', title: 'Shopping List', desc: 'All items with quantities and estimated costs, grouped by category' },
            { icon: Clock, color: 'text-green-600 bg-green-50', title: 'Day-of Schedule', desc: 'A full hour-by-hour timeline so the day runs smoothly' },
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

