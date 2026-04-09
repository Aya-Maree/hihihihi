import { useState, useEffect } from 'react'
import { BookOpen, Search, FileText, Tag, Layers } from 'lucide-react'
import { listDocuments, retrieveDocuments } from '../api/client'
import toast from 'react-hot-toast'

const CATEGORY_COLORS = {
  event_planning: 'bg-purple-100 text-purple-700',
  budget: 'bg-green-100 text-green-700',
  shopping: 'bg-blue-100 text-blue-700',
  dietary: 'bg-orange-100 text-orange-700',
  accessibility: 'bg-pink-100 text-pink-700',
  scheduling: 'bg-yellow-100 text-yellow-700',
  vendors_decor: 'bg-indigo-100 text-indigo-700',
  guest_management: 'bg-teal-100 text-teal-700',
  catering: 'bg-red-100 text-red-700',
  entertainment: 'bg-cyan-100 text-cyan-700',
}

export default function KnowledgeBase() {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [searching, setSearching] = useState(false)
  const [expandedDoc, setExpandedDoc] = useState(null)

  useEffect(() => {
    listDocuments()
      .then((r) => setDocuments(r.data.documents))
      .catch(() => toast.error('Failed to load documents'))
      .finally(() => setLoading(false))
  }, [])

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setSearching(true)
    try {
      const res = await retrieveDocuments(query, null, 8)
      setResults(res.data)
    } catch {
      toast.error('Search failed')
    } finally {
      setSearching(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-purple-600" />
          Planning Guides
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          {documents.length} guides covering everything from budgeting to day-of logistics
        </p>
      </div>

      {/* Search */}
      <div className="card p-4">
        <h2 className="text-sm font-semibold text-gray-700 mb-2">Search Planning Tips</h2>
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder='Try: "budget for 25 guests" or "vegetarian options" or "day-of schedule"'
            className="input flex-1"
          />
          <button type="submit" disabled={searching} className="btn-primary flex items-center gap-1">
            <Search className="w-4 h-4" />
            {searching ? 'Searching…' : 'Search'}
          </button>
        </form>

        {results && (
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-700">
                Top tips for: "{results.query}"
              </h3>
              <button onClick={() => setResults(null)} className="text-xs text-gray-400 hover:text-gray-600">
                Clear
              </button>
            </div>
            {results.retrieved_chunks.map((chunk, i) => (
              <div key={i} className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold text-purple-700">{chunk.doc_title}</span>
                </div>
                <p className="text-xs text-gray-700 leading-relaxed">{chunk.text}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Document list */}
      {loading ? (
        <div className="text-center py-8 text-gray-400">Loading…</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="card p-4 cursor-pointer hover:shadow-md transition-all"
              onClick={() => setExpandedDoc(expandedDoc === doc.id ? null : doc.id)}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <FileText className="w-4 h-4 text-gray-500" />
                </div>
                <span
                  className={`badge text-xs ${
                    CATEGORY_COLORS[doc.category] || 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {doc.category?.replace(/_/g, ' ')}
                </span>
              </div>

              <h3 className="font-semibold text-sm text-gray-900 mt-2">{doc.title}</h3>
              <p className="text-xs text-gray-500 mt-1 leading-relaxed">{doc.description}</p>

              <div className="flex items-center gap-2 mt-2">
                <Layers className="w-3 h-3 text-gray-400" />
                <span className="text-xs text-gray-400">{doc.chunk_count} sections</span>
              </div>

              {expandedDoc === doc.id && doc.tags?.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <div className="flex items-center gap-1 flex-wrap">
                    <Tag className="w-3 h-3 text-gray-400" />
                    {doc.tags.map((t) => (
                      <span key={t} className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
