"""
RAG Pipeline — Retrieval-Augmented Generation
As specified in Deliverable 1:
  - JSON knowledge base (12+ curated planning documents)
  - sentence-transformers (all-MiniLM-L6-v2) for semantic embeddings
  - ChromaDB (in-memory) as the vector store
  - Top 3–5 chunk retrieval at query time
  - Source citations included in every response
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))

# ─────────────────────────────────────────────────────────────────────────────
# Document Store — loads the JSON knowledge base
# ─────────────────────────────────────────────────────────────────────────────

class DocumentStore:
    """
    Loads and manages the JSON knowledge base.
    Each document is a .json file in backend/knowledge_base/ with a 'chunks' array.
    Chunks are 200–400 token text segments (per Deliverable 1 spec).
    """

    def __init__(self, kb_dir: Optional[str] = None):
        if kb_dir is None:
            kb_dir = Path(__file__).parent / "knowledge_base"
        self.kb_dir = Path(kb_dir)
        self.documents: List[Dict] = []
        self.chunks: List[Dict] = []
        self._loaded = False

    def load(self) -> List[Dict]:
        """Load all JSON documents. Returns flat list of enriched chunk dicts."""
        if self._loaded:
            return self.chunks

        self.documents = []
        self.chunks = []

        for json_file in sorted(self.kb_dir.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    doc = json.load(f)
                    self.documents.append(doc)
                    for chunk in doc.get("chunks", []):
                        # Enrich chunk with source metadata
                        self.chunks.append({
                            "chunk_id": chunk["chunk_id"],
                            "text": chunk["text"],
                            "doc_id": doc["id"],
                            "doc_title": doc["title"],
                            "doc_category": doc.get("category", "general"),
                            "doc_tags": doc.get("tags", []),
                        })
            except Exception as e:
                print(f"Warning: failed to load {json_file.name}: {e}")

        self._loaded = True
        print(f"DocumentStore: loaded {len(self.chunks)} chunks from {len(self.documents)} documents")
        return self.chunks

    def get_document_list(self) -> List[Dict]:
        """Return document metadata list (no chunk text) for UI display."""
        self.load()
        return [
            {
                "id": doc["id"],
                "title": doc["title"],
                "category": doc.get("category", "general"),
                "description": doc.get("description", ""),
                "tags": doc.get("tags", []),
                "chunk_count": len(doc.get("chunks", [])),
            }
            for doc in self.documents
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Semantic Retriever — sentence-transformers + ChromaDB
# As specified in Deliverable 1
# ─────────────────────────────────────────────────────────────────────────────

class SemanticRetriever:
    """
    Semantic retrieval using:
    - sentence-transformers all-MiniLM-L6-v2 for dense vector embeddings
    - ChromaDB (in-memory) as the vector store
    - Cosine similarity for ranking
    """

    COLLECTION_NAME = "household_event_planner_kb"

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name
        self._encoder = None     # lazy-loaded sentence transformer
        self._chroma_client = None
        self._collection = None
        self._fitted = False

    def _get_encoder(self):
        """Lazy-load the sentence transformer model."""
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
                print(f"Loading sentence transformer: {self.model_name}...")
                self._encoder = SentenceTransformer(self.model_name)
                print("Sentence transformer loaded.")
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. Run: pip install sentence-transformers"
                )
        return self._encoder

    def _get_collection(self):
        """Lazy-initialize ChromaDB in-memory client and collection."""
        if self._chroma_client is None:
            try:
                import chromadb
                self._chroma_client = chromadb.Client()  # in-memory, no persistence needed
                # Use cosine similarity (standard for sentence-transformers)
                self._collection = self._chroma_client.get_or_create_collection(
                    name=self.COLLECTION_NAME,
                    metadata={"hnsw:space": "cosine"},
                )
            except ImportError:
                raise ImportError("chromadb not installed. Run: pip install chromadb")
        return self._collection

    def fit(self, chunks: List[Dict]) -> None:
        """
        Embed all knowledge base chunks and store them in ChromaDB.
        This builds the vector index from the JSON documents.
        """
        if not chunks:
            return

        encoder = self._get_encoder()
        collection = self._get_collection()

        # Extract texts for batch encoding
        texts = [c["text"] for c in chunks]
        ids = [c["chunk_id"] for c in chunks]

        # Build metadata dicts for ChromaDB (no nested structures)
        metadatas = [
            {
                "doc_id": c["doc_id"],
                "doc_title": c["doc_title"],
                "doc_category": c["doc_category"],
                "tags": ", ".join(c.get("doc_tags", [])),
            }
            for c in chunks
        ]

        # Generate dense embeddings (384-dim for all-MiniLM-L6-v2)
        print(f"Encoding {len(texts)} chunks with {self.model_name}...")
        embeddings = encoder.encode(texts, show_progress_bar=False).tolist()

        # Upsert into ChromaDB (handles re-initialization gracefully)
        collection.upsert(
            documents=texts,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )

        self._fitted = True
        print(f"ChromaDB collection built: {collection.count()} vectors indexed.")

    def retrieve(self, query: str, top_k: int = RAG_TOP_K) -> List[Dict]:
        """
        Semantically retrieve the top-k most relevant chunks for a query.
        Uses the sentence transformer to embed the query, then queries ChromaDB.

        Returns list of dicts with chunk text, source metadata, and relevance score.
        """
        if not self._fitted:
            return []

        encoder = self._get_encoder()
        collection = self._get_collection()

        # Embed the query with the same model used for indexing
        query_embedding = encoder.encode([query], show_progress_bar=False).tolist()[0]

        # Query ChromaDB — returns results sorted by cosine distance (ascending = most similar)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        for i, (doc_text, meta, dist) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )):
            # ChromaDB cosine distance: 0 = identical, 2 = opposite
            # Convert to similarity score: 1 - (distance / 2)
            similarity = round(1.0 - (dist / 2.0), 4)
            chunks.append({
                "chunk_id": results["ids"][0][i],
                "text": doc_text,
                "doc_id": meta.get("doc_id", ""),
                "doc_title": meta.get("doc_title", ""),
                "doc_category": meta.get("doc_category", ""),
                "relevance_score": similarity,
            })

        return chunks


# ─────────────────────────────────────────────────────────────────────────────
# RAG Pipeline — combines DocumentStore + SemanticRetriever
# ─────────────────────────────────────────────────────────────────────────────

class RAGPipeline:
    """
    Full RAG Pipeline as specified in Deliverable 1:
    1. Load JSON knowledge base documents
    2. Chunk and embed with all-MiniLM-L6-v2
    3. Store embeddings in ChromaDB (in-memory)
    4. At query time: embed query → retrieve top-k chunks → build context for LLM
    5. Include source citations in all responses
    """

    def __init__(self, kb_dir: Optional[str] = None):
        self.store = DocumentStore(kb_dir)
        self.retriever = SemanticRetriever(model_name=EMBEDDING_MODEL)
        self._initialized = False

    def initialize(self) -> int:
        """
        Load documents, encode all chunks, and build the ChromaDB index.
        Must be called once before retrieve().
        Returns number of chunks indexed.
        """
        chunks = self.store.load()
        self.retriever.fit(chunks)
        self._initialized = True
        return len(chunks)

    def retrieve(
        self,
        query: str,
        top_k: int = RAG_TOP_K,
        event_context: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Retrieve top-k semantically relevant chunks for the given query.
        Enriches the query with event context fields (as specified in Deliverable 1)
        so the retrieval is grounded in the current planning state.
        """
        if not self._initialized:
            self.initialize()

        # Enrich query with event context for better retrieval grounding
        enriched_query = query
        if event_context:
            ctx_parts = []
            if event_context.get("event_type"):
                ctx_parts.append(event_context["event_type"])
            if event_context.get("dietary_restrictions"):
                ctx_parts.append("dietary " + " ".join(event_context["dietary_restrictions"]))
            if event_context.get("venue_type"):
                ctx_parts.append(event_context["venue_type"])
            if event_context.get("guest_count_estimated") or event_context.get("guest_count_confirmed"):
                guests = event_context.get("guest_count_estimated") or event_context.get("guest_count_confirmed")
                ctx_parts.append(f"{guests} guests")
            if event_context.get("has_children"):
                ctx_parts.append("children activities")
            if event_context.get("has_elderly"):
                ctx_parts.append("elderly accessibility")
            if ctx_parts:
                enriched_query = f"{query} {' '.join(ctx_parts)}"

        return self.retriever.retrieve(enriched_query, top_k=top_k)

    def build_context_block(self, chunks: List[Dict]) -> str:
        """
        Format retrieved chunks into a context string for the LLM prompt.
        Each chunk is labeled with its source document for citation.
        """
        if not chunks:
            return "No relevant knowledge base documents were retrieved."

        lines = ["=== RETRIEVED KNOWLEDGE BASE CONTEXT ===\n"]
        for i, chunk in enumerate(chunks, 1):
            score_pct = int(chunk.get("relevance_score", 0) * 100)
            lines.append(
                f"[Source {i}: {chunk['doc_title']} | doc_id: {chunk['doc_id']} | similarity: {score_pct}%]"
            )
            lines.append(chunk["text"])
            lines.append("")
        lines.append("=== END OF RETRIEVED CONTEXT ===")
        return "\n".join(lines)

    def get_citations(self, chunks: List[Dict]) -> List[Dict]:
        """Extract unique citation metadata from a list of retrieved chunks."""
        seen = set()
        citations = []
        for chunk in chunks:
            if chunk["doc_id"] not in seen:
                seen.add(chunk["doc_id"])
                citations.append({
                    "doc_id": chunk["doc_id"],
                    "doc_title": chunk["doc_title"],
                    "doc_category": chunk["doc_category"],
                    "relevance_score": chunk.get("relevance_score", 0),
                })
        return citations

    def get_document_list(self) -> List[Dict]:
        """Return metadata list of all knowledge base documents."""
        if not self._initialized:
            self.initialize()
        return self.store.get_document_list()


# ─────────────────────────────────────────────────────────────────────────────
# Global singleton
# ─────────────────────────────────────────────────────────────────────────────

_rag_instance: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    """Get the global RAG pipeline instance, initializing if needed."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGPipeline()
        n_chunks = _rag_instance.initialize()
        n_docs = len(_rag_instance.store.documents)
        print(f"RAG Pipeline ready: {n_chunks} chunks from {n_docs} documents (model: {EMBEDDING_MODEL})")
    return _rag_instance
