import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Download, RefreshCw, ArrowLeft, FileJson } from 'lucide-react'
import toast from 'react-hot-toast'
import ArtifactViewer from '../components/ArtifactViewer'
import { getArtifacts, generateArtifacts } from '../api/client'

export default function Artifacts({ sessionId, onArtifactsReady }) {
  const navigate = useNavigate()
  const [artifacts, setArtifacts] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [enrichSpoonacular, setEnrichSpoonacular] = useState(false)

  useEffect(() => {
    if (sessionId) fetchArtifacts()
  }, [sessionId])

  const fetchArtifacts = async () => {
    setLoading(true)
    try {
      const res = await getArtifacts(sessionId)
      setArtifacts(res.data.artifacts)
      if (res.data.artifacts) onArtifactsReady?.(true)
    } catch {
      toast.error('Failed to load artifacts')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    if (!sessionId) return
    setGenerating(true)
    try {
      const res = await generateArtifacts(sessionId, enrichSpoonacular)
      setArtifacts(res.data.artifacts)
      onArtifactsReady?.(true)
      toast.success('Your plan is ready!')
    } catch {
      toast.error('Failed to generate artifacts')
    } finally {
      setGenerating(false)
    }
  }

  const handleDownloadAll = () => {
    if (!artifacts) return
    const blob = new Blob([JSON.stringify(artifacts, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `event_plan_${sessionId?.slice(0, 8)}_${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Full plan downloaded!')
  }

  if (!sessionId) {
    return (
      <div className="text-center py-20">
        <FileJson className="w-12 h-12 text-gray-300 mx-auto mb-3" />
        <p className="text-gray-500">No active session.</p>
        <button
          onClick={() => navigate('/plan')}
          className="btn-primary mt-4"
        >
          Start Planning
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/plan')}
            className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-4 h-4 text-gray-500" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-gray-900">My Event Plan</h1>
            <p className="text-sm text-gray-500">
              Your checklist, shopping list, and day-of schedule
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1.5 text-xs text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={enrichSpoonacular}
              onChange={(e) => setEnrichSpoonacular(e.target.checked)}
              className="accent-purple-600"
            />
            Include recipes
          </label>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="btn-secondary text-xs flex items-center gap-1"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${generating ? 'animate-spin' : ''}`} />
            {generating ? 'Updating…' : 'Refresh Plan'}
          </button>
          {artifacts && (
            <button
              onClick={handleDownloadAll}
              className="btn-primary text-xs flex items-center gap-1"
            >
              <Download className="w-3.5 h-3.5" />
              Download Plan
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-400">
          <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm">Loading your plan…</p>
        </div>
      ) : artifacts ? (
        <ArtifactViewer artifacts={artifacts} sessionId={sessionId} />
      ) : (
        <div className="card p-12 text-center">
          <FileJson className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Your plan isn't ready yet</h3>
          <p className="text-sm text-gray-400 mb-4">
            Finish chatting with your planner, then tap the button to get your documents.
          </p>
          <div className="flex gap-3 justify-center">
            <button onClick={() => navigate('/plan')} className="btn-secondary">
              Continue Planning
            </button>
            <button onClick={handleGenerate} disabled={generating} className="btn-primary">
              {generating ? 'Creating Your Plan…' : 'Get My Plan Now'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
