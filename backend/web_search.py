"""
Web Search Module — DuckDuckGo integration for live web RAG.
No API key required (uses duckduckgo-search package).

Supplements the local knowledge base with real-time web results when:
  - Local KB relevance scores are low (below threshold)
  - The query contains keywords that imply live/external info (prices, vendors, etc.)
  - The user explicitly asks to search the web
"""

import os
from typing import List, Dict

WEB_SEARCH_MAX_RESULTS = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "4"))
WEB_SEARCH_SCORE_THRESHOLD = float(os.getenv("WEB_SEARCH_SCORE_THRESHOLD", "0.50"))

# Keywords that suggest the user wants live/external data rather than curated KB info
_WEB_TRIGGER_KEYWORDS = [
    "current", "today", "latest", "near me", "where to buy", "where can i",
    "vendor", "hire", "book", "rent", "how much does", "average cost",
    "recommend", "best", "top rated", "review", "2024", "2025", "2026",
    "local", "find", "store", "delivery", "price", "cheap",
    "search web", "search online", "look up", "look online", "find online",
    "google", "search for",
]


def web_search(query: str, max_results: int = WEB_SEARCH_MAX_RESULTS) -> List[Dict]:
    """
    Search DuckDuckGo for the given query.
    Returns a list of chunk-format dicts compatible with the RAG pipeline
    (same shape as local KB chunks, with extra url and source_type fields).
    """
    try:
        from ddgs import DDGS
    except ImportError:
        print("ddgs not installed. Run: pip install ddgs")
        return []

    try:
        results = []
        with DDGS() as ddgs:
            for i, r in enumerate(ddgs.text(query, max_results=max_results)):
                title = r.get("title", "Web Result")
                body = r.get("body", "")
                url = r.get("href", "")
                results.append({
                    "chunk_id": f"web_{i}",
                    "text": f"{title}\n{body}",
                    "doc_id": f"web_{i}",
                    "doc_title": title,
                    "doc_category": "web",
                    "url": url,
                    "relevance_score": round(0.72 - (i * 0.04), 2),
                    "source_type": "web",
                })
        print(f"Web search: '{query}' → {len(results)} results")
        return results
    except Exception as e:
        print(f"Web search error: {e}")
        return []


def should_web_search(query: str, local_chunks: List[Dict]) -> bool:
    """
    Return True if web search should supplement local KB results.

    Triggers when:
    - No local results were found
    - Top local relevance score is below the threshold
    - Query contains keywords implying live/external info
    """
    query_lower = query.lower()
    if any(kw in query_lower for kw in _WEB_TRIGGER_KEYWORDS):
        return True
    if not local_chunks:
        return True
    top_score = max((c.get("relevance_score", 0) for c in local_chunks), default=0)
    return top_score < WEB_SEARCH_SCORE_THRESHOLD
