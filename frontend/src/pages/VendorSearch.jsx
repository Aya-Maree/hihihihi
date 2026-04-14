import { useState } from 'react'
import { Search, Globe, ExternalLink, Loader2, Sparkles, AlertCircle } from 'lucide-react'
import { webSearch } from '../api/client'

const SUGGESTIONS = [
  'bouncy castle rental near me',
  'outdoor party tent hire',
  'birthday cake bakery near me',
  'party catering services',
  'balloon decoration vendor',
  'DJ hire for birthday party',
  'photo booth rental',
  'wedding florist near me',
]

export default function VendorSearch() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [lastQuery, setLastQuery] = useState('')

  const handleSearch = async (q = query) => {
    const trimmed = q.trim()
    if (!trimmed) return
    setLoading(true)
    setError(null)
    setResults(null)
    setLastQuery(trimmed)
    try {
      const res = await webSearch(trimmed, 6)
      setResults(res.data.results || [])
    } catch {
      setError('Search failed. Make sure the backend is running and try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleSuggestion = (s) => {
    setQuery(s)
    handleSearch(s)
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-br from-teal-600 to-cyan-600 rounded-2xl p-7 text-white">
        <div className="flex items-center gap-2 mb-2">
          <Globe className="w-5 h-5 text-teal-200" />
          <span className="text-sm text-teal-100">Real-time web results</span>
        </div>
        <h1 className="text-2xl font-bold mb-1">Vendor & Supplier Search</h1>
        <p className="text-teal-100 text-sm leading-relaxed">
          Search the web for local vendors, rentals, catering, decorations, and anything else
          you need for your event.
        </p>
      </div>

      {/* Search bar */}
      <div className="card p-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="e.g. bouncy castle rental near me"
              className="w-full pl-9 pr-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-400 focus:border-teal-400"
            />
          </div>
          <button
            onClick={() => handleSearch()}
            disabled={loading || !query.trim()}
            className="flex items-center gap-2 bg-teal-600 text-white font-medium px-5 py-2.5 rounded-lg hover:bg-teal-700 transition-colors disabled:opacity-50 text-sm"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            Search
          </button>
        </div>
      </div>

      {/* Suggestions */}
      {!results && !loading && (
        <div>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2 px-1">
            <Sparkles className="w-3 h-3 inline mr-1" />
            Try searching for
          </p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => handleSuggestion(s)}
                className="text-sm bg-white border border-gray-200 rounded-full px-3 py-1.5 text-gray-600 hover:border-teal-400 hover:text-teal-700 hover:bg-teal-50 transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex flex-col items-center gap-3 py-12 text-gray-400">
          <Loader2 className="w-8 h-8 animate-spin text-teal-500" />
          <p className="text-sm">Searching the web for "{lastQuery}"…</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Results */}
      {results && !loading && (
        <div className="space-y-3">
          <p className="text-sm text-gray-500">
            {results.length > 0
              ? `${results.length} results for "${lastQuery}"`
              : `No results found for "${lastQuery}"`}
          </p>

          {results.length === 0 && (
            <div className="card p-8 text-center text-gray-400">
              <Globe className="w-10 h-10 mx-auto mb-3 opacity-40" />
              <p className="text-sm">Try a different search term or be more specific.</p>
            </div>
          )}

          {results.map((r, i) => (
            <a
              key={i}
              href={r.url || r.href || '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="card p-4 flex gap-3 hover:shadow-md hover:border-teal-200 transition-all group block"
            >
              <div className="w-8 h-8 rounded-lg bg-teal-50 flex items-center justify-center flex-shrink-0 mt-0.5 group-hover:bg-teal-100 transition-colors">
                <Globe className="w-4 h-4 text-teal-600" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-medium text-sm text-gray-900 group-hover:text-teal-700 transition-colors leading-snug">
                    {r.title || 'Untitled'}
                  </p>
                  <ExternalLink className="w-3.5 h-3.5 text-gray-300 group-hover:text-teal-400 flex-shrink-0 mt-0.5 transition-colors" />
                </div>
                {(r.body || r.snippet) && (
                  <p className="text-xs text-gray-500 mt-1 leading-relaxed line-clamp-3">
                    {r.body || r.snippet}
                  </p>
                )}
                <p className="text-xs text-teal-600 mt-1.5 truncate opacity-70">
                  {r.url || r.href}
                </p>
              </div>
            </a>
          ))}

          <button
            onClick={() => handleSearch()}
            className="w-full text-sm text-gray-400 hover:text-teal-600 py-2 transition-colors"
          >
            Search again
          </button>
        </div>
      )}
    </div>
  )
}
