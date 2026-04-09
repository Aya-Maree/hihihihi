import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { CheckSquare, ShoppingCart, Clock, Download, ChevronDown, ChevronUp, BookOpen } from 'lucide-react'
import clsx from 'clsx'
import { getArtifactMarkdown } from '../api/client'
import toast from 'react-hot-toast'

const TABS = [
  { id: 'task_checklist', label: 'Task Checklist', icon: CheckSquare, color: 'text-purple-600' },
  { id: 'shopping_list', label: 'Shopping List', icon: ShoppingCart, color: 'text-blue-600' },
  { id: 'day_of_schedule', label: 'Day-of Schedule', icon: Clock, color: 'text-green-600' },
]

export default function ArtifactViewer({ artifacts, sessionId }) {
  const [activeTab, setActiveTab] = useState('task_checklist')
  const [markdownCache, setMarkdownCache] = useState({})
  const [viewMode, setViewMode] = useState('structured') // 'structured' | 'markdown'
  const [loading, setLoading] = useState(false)

  if (!artifacts) {
    return (
      <div className="text-center py-16 text-gray-400">
        <CheckSquare className="w-10 h-10 mx-auto mb-3 opacity-40" />
        <p className="text-sm">No artifacts generated yet.</p>
        <p className="text-xs mt-1">Complete the planning workflow to generate your plan.</p>
      </div>
    )
  }

  const loadMarkdown = async (artifactType) => {
    if (markdownCache[artifactType]) return
    setLoading(true)
    try {
      const res = await getArtifactMarkdown(sessionId, artifactType)
      setMarkdownCache((prev) => ({ ...prev, [artifactType]: res.data }))
    } catch {
      toast.error('Failed to load markdown')
    } finally {
      setLoading(false)
    }
  }

  const handleViewModeChange = (mode) => {
    setViewMode(mode)
    if (mode === 'markdown') loadMarkdown(activeTab)
  }

  const handleTabChange = (tab) => {
    setActiveTab(tab)
    if (viewMode === 'markdown') loadMarkdown(tab)
  }

  const handleDownload = () => {
    const artifact = artifacts[activeTab]
    if (!artifact) return
    const blob = new Blob([JSON.stringify(artifact, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${activeTab}_${sessionId?.slice(0, 8)}.json`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Downloaded!')
  }

  const artifact = artifacts[activeTab]

  return (
    <div className="space-y-4">
      {/* Tab header */}
      <div className="flex items-center justify-between">
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
          {TABS.map(({ id, label, icon: Icon, color }) => (
            <button
              key={id}
              onClick={() => handleTabChange(id)}
              className={clsx(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all',
                activeTab === id
                  ? 'bg-white shadow-sm text-gray-900'
                  : 'text-gray-500 hover:text-gray-700'
              )}
            >
              <Icon className={clsx('w-3.5 h-3.5', activeTab === id ? color : '')} />
              {label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => handleViewModeChange('structured')}
              className={clsx(
                'px-2 py-1 rounded text-xs',
                viewMode === 'structured' ? 'bg-white shadow-sm' : 'text-gray-500'
              )}
            >
              Visual
            </button>
            <button
              onClick={() => handleViewModeChange('markdown')}
              className={clsx(
                'px-2 py-1 rounded text-xs',
                viewMode === 'markdown' ? 'bg-white shadow-sm' : 'text-gray-500'
              )}
            >
              Markdown
            </button>
          </div>
          <button onClick={handleDownload} className="btn-secondary text-xs flex items-center gap-1">
            <Download className="w-3.5 h-3.5" />
            JSON
          </button>
        </div>
      </div>

      {/* Artifact Content */}
      <div className="card overflow-hidden">
        {viewMode === 'markdown' ? (
          <div className="p-4 prose-sm max-h-[600px] overflow-y-auto">
            {loading ? (
              <p className="text-sm text-gray-400 animate-pulse">Loading...</p>
            ) : markdownCache[activeTab] ? (
              <ReactMarkdown>{markdownCache[activeTab]}</ReactMarkdown>
            ) : (
              <p className="text-sm text-gray-400">Click Markdown to load.</p>
            )}
          </div>
        ) : (
          <StructuredView artifact={artifact} type={activeTab} />
        )}
      </div>

      {/* Citations */}
      {artifact?.citations?.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <BookOpen className="w-3.5 h-3.5 text-gray-400" />
          <span className="text-xs text-gray-400">Sources:</span>
          {artifact.citations.map((c, i) => (
            <span key={i} className="text-xs bg-purple-50 text-purple-700 px-2 py-0.5 rounded-full border border-purple-100">
              {typeof c === 'string' ? c.replace(/_/g, ' ') : c}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Structured Views ────────────────────────────────────────────────────────

function StructuredView({ artifact, type }) {
  if (!artifact) return <div className="p-8 text-center text-gray-400 text-sm">No data</div>

  if (type === 'task_checklist') return <ChecklistView artifact={artifact} />
  if (type === 'shopping_list') return <ShoppingListView artifact={artifact} />
  if (type === 'day_of_schedule') return <ScheduleView artifact={artifact} />
  return <pre className="p-4 text-xs overflow-auto">{JSON.stringify(artifact, null, 2)}</pre>
}

function ChecklistView({ artifact }) {
  const [expanded, setExpanded] = useState({})
  const toggle = (name) => setExpanded((p) => ({ ...p, [name]: !p[name] }))

  return (
    <div>
      {/* Header */}
      <div className="p-4 border-b border-gray-100 flex justify-between items-start">
        <div>
          <h3 className="font-semibold text-gray-900">{artifact.event_title}</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            {artifact.total_tasks} tasks · {artifact.completed_tasks} completed
          </p>
        </div>
        <span className="text-xs text-gray-400">{artifact.event_date}</span>
      </div>

      <div className="divide-y divide-gray-50 max-h-[520px] overflow-y-auto">
        {artifact.categories?.map((cat) => (
          <div key={cat.name}>
            <button
              onClick={() => toggle(cat.name)}
              className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm text-gray-800">{cat.name}</span>
                <span className="badge bg-gray-100 text-gray-600">{cat.tasks?.length || 0}</span>
              </div>
              {expanded[cat.name] !== false
                ? <ChevronUp className="w-4 h-4 text-gray-400" />
                : <ChevronDown className="w-4 h-4 text-gray-400" />
              }
            </button>

            {expanded[cat.name] !== false && (
              <div className="px-4 pb-3 space-y-2">
                {cat.tasks?.map((task) => (
                  <div key={task.task_id} className="flex items-start gap-2.5 py-1.5">
                    <input type="checkbox" className="mt-0.5 accent-purple-600" defaultChecked={task.status === 'completed'} />
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-medium text-gray-800">{task.title}</span>
                        <PriorityBadge priority={task.priority} />
                      </div>
                      {task.description && (
                        <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{task.description}</p>
                      )}
                      <div className="flex items-center gap-3 mt-1">
                        {task.owner && <span className="text-xs text-gray-400">👤 {task.owner}</span>}
                        {task.estimated_time && <span className="text-xs text-gray-400">⏱ {task.estimated_time}</span>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function ShoppingListView({ artifact }) {
  const overBudget = artifact.budget_remaining < 0

  return (
    <div>
      {/* Header */}
      <div className="p-4 border-b border-gray-100">
        <h3 className="font-semibold text-gray-900">{artifact.event_title}</h3>
        <div className="flex gap-4 mt-2">
          <StatChip label="Guests" value={artifact.guest_count} />
          <StatChip label="Budget" value={`$${(artifact.budget_total || 0).toFixed(0)}`} />
          <StatChip
            label="Est. Total"
            value={`$${(artifact.total_cost || 0).toFixed(2)}`}
            danger={overBudget}
          />
          <StatChip
            label="Remaining"
            value={`$${(artifact.budget_remaining || 0).toFixed(2)}`}
            danger={overBudget}
          />
        </div>
        {overBudget && (
          <p className="text-xs text-red-600 mt-2 font-medium">
            ⚠️ Over budget by ${Math.abs(artifact.budget_remaining).toFixed(2)} — consider simplifying the menu.
          </p>
        )}
        {artifact.notes && (
          <p className="text-xs text-gray-500 mt-1 italic">{artifact.notes}</p>
        )}
      </div>

      <div className="max-h-[480px] overflow-y-auto">
        {artifact.categories?.map((cat) => (
          <div key={cat.name} className="border-b border-gray-50">
            <div className="flex justify-between items-center px-4 py-2 bg-gray-50">
              <span className="text-xs font-semibold text-gray-700 uppercase tracking-wide">{cat.name}</span>
              <span className="text-xs font-semibold text-gray-600">${(cat.subtotal || 0).toFixed(2)}</span>
            </div>
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-400 border-b border-gray-100">
                  <th className="px-4 py-1.5 text-left font-medium">Item</th>
                  <th className="px-2 py-1.5 text-right font-medium">Qty</th>
                  <th className="px-2 py-1.5 text-left font-medium">Unit</th>
                  <th className="px-2 py-1.5 text-right font-medium">Cost</th>
                </tr>
              </thead>
              <tbody>
                {cat.items?.map((item, i) => (
                  <tr key={i} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-2">
                      <span className="font-medium text-gray-800">{item.item}</span>
                      {item.notes && <span className="block text-gray-400">{item.notes}</span>}
                    </td>
                    <td className="px-2 py-2 text-right text-gray-700">{item.quantity}</td>
                    <td className="px-2 py-2 text-gray-500">{item.unit}</td>
                    <td className="px-2 py-2 text-right font-medium text-gray-800">
                      ${(item.estimated_cost || 0).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>

      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 flex justify-between items-center">
        <span className="text-sm font-semibold text-gray-700">Total Estimated Cost</span>
        <span className={clsx('text-sm font-bold', overBudget ? 'text-red-600' : 'text-green-600')}>
          ${(artifact.total_cost || 0).toFixed(2)}
        </span>
      </div>
    </div>
  )
}

function ScheduleView({ artifact }) {
  const allBlocks = [
    { section: '🔧 Setup', blocks: artifact.setup_blocks || [], color: 'bg-blue-50 border-blue-200' },
    { section: '🎉 Event', blocks: artifact.event_blocks || [], color: 'bg-purple-50 border-purple-200' },
    { section: '🧹 Cleanup', blocks: artifact.cleanup_blocks || [], color: 'bg-gray-50 border-gray-200' },
  ]

  return (
    <div>
      <div className="p-4 border-b border-gray-100">
        <h3 className="font-semibold text-gray-900">{artifact.event_title}</h3>
        <p className="text-xs text-gray-500 mt-0.5">
          {artifact.event_date} · Starts {artifact.event_start_time} · {artifact.event_duration_hours}h
        </p>
      </div>

      <div className="max-h-[520px] overflow-y-auto p-4 space-y-4">
        {allBlocks.map(({ section, blocks, color }) => (
          blocks.length > 0 && (
            <div key={section}>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">{section}</h4>
              <div className="space-y-2">
                {blocks.map((block) => (
                  <div key={block.block_id} className={clsx('border rounded-lg p-3', color)}>
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-semibold text-sm text-gray-900">{block.start_time}</span>
                          <span className="text-sm text-gray-700">{block.activity}</span>
                          <span className="text-xs text-gray-400">{block.duration_minutes} min</span>
                        </div>
                        {block.details && (
                          <p className="text-xs text-gray-600 mt-1">{block.details}</p>
                        )}
                        {block.dependencies?.length > 0 && (
                          <p className="text-xs text-gray-400 mt-1">
                            Depends on: {block.dependencies.join(', ')}
                          </p>
                        )}
                      </div>
                      {block.responsible && (
                        <span className="badge bg-white text-gray-600 border border-gray-200 flex-shrink-0">
                          {block.responsible}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        ))}
      </div>
    </div>
  )
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function PriorityBadge({ priority }) {
  const colors = {
    high: 'bg-red-100 text-red-700',
    medium: 'bg-yellow-100 text-yellow-700',
    low: 'bg-green-100 text-green-700',
  }
  if (!priority) return null
  return (
    <span className={clsx('badge text-xs', colors[priority.toLowerCase()] || 'bg-gray-100 text-gray-600')}>
      {priority}
    </span>
  )
}

function StatChip({ label, value, danger }) {
  return (
    <div className="text-center">
      <p className="text-xs text-gray-400">{label}</p>
      <p className={clsx('text-sm font-bold', danger ? 'text-red-600' : 'text-gray-900')}>{value}</p>
    </div>
  )
}
