import { Link, useLocation } from 'react-router-dom'
import { Calendar, MessageSquare, FileText, BookOpen, Plus, Home, Globe } from 'lucide-react'
import clsx from 'clsx'

const WORKFLOW_LABELS = {
  intake: 'Getting Started',
  clarification: 'Asking Questions',
  retrieval: 'Gathering Ideas',
  conflict_detection: 'Reviewing Details',
  planning: 'Building Plan',
  validation: 'Finalizing',
  artifact_generation: 'Preparing Docs',
  complete: 'Plan Ready!',
}

const WORKFLOW_COLORS = {
  intake: 'bg-gray-100 text-gray-700',
  clarification: 'bg-blue-100 text-blue-700',
  retrieval: 'bg-indigo-100 text-indigo-700',
  conflict_detection: 'bg-orange-100 text-orange-700',
  planning: 'bg-purple-100 text-purple-700',
  validation: 'bg-yellow-100 text-yellow-700',
  artifact_generation: 'bg-green-100 text-green-700',
  complete: 'bg-green-100 text-green-700',
}

export default function Navbar({ sessionId, workflowState, artifactsReady, onNewSession }) {
  const location = useLocation()

  const navLinks = [
    { to: '/', icon: Home, label: 'Home' },
    { to: '/plan', icon: MessageSquare, label: 'AI Planner' },
    { to: '/artifacts', icon: FileText, label: 'My Plan', badge: artifactsReady },
    { to: '/vendor-search', icon: Globe, label: 'Find Vendors' },
    { to: '/knowledge-base', icon: BookOpen, label: 'Planning Guides' },
  ]

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center">
              <Calendar className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-gray-900 text-sm">Household Event</span>
              <span className="text-purple-600 font-bold text-sm"> Planner</span>
              <span className="text-xs text-gray-400 ml-1">AI</span>
            </div>
          </div>

          {/* Nav Links */}
          <div className="flex items-center gap-1">
            {navLinks.map(({ to, icon: Icon, label, badge }) => (
              <Link
                key={to}
                to={to}
                className={clsx(
                  'flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors relative',
                  location.pathname === to
                    ? 'bg-purple-50 text-purple-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                )}
              >
                <Icon className="w-4 h-4" />
                <span className="hidden sm:inline">{label}</span>
                {badge && (
                  <span className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full" />
                )}
              </Link>
            ))}
          </div>

          {/* Progress badge + Start Over */}
          <div className="flex items-center gap-2">
            {workflowState && workflowState !== 'intake' && (
              <span className={clsx('badge text-xs', WORKFLOW_COLORS[workflowState] || 'bg-gray-100 text-gray-600')}>
                {WORKFLOW_LABELS[workflowState] || workflowState}
              </span>
            )}
            <button
              onClick={onNewSession}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-purple-600 px-2 py-1.5 rounded-lg hover:bg-purple-50 transition-colors"
              title="Start a new event plan"
            >
              <Plus className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Start Over</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}
