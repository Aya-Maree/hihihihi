"""
Household Event Planner — FastAPI Backend
EventOps AI Application | SE4471 Course Project

Provides all API endpoints for:
- Session management (memory/state tracking)
- Chat (multi-turn conversation with RAG)
- Planning workflow (7-step agentic logic)
- Event context retrieval
- Artifact generation and download
- Knowledge base inspection
- Spoonacular integration (Tier 2)
"""

import os
import sys
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# App Init
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Household Event Planner API",
    description="AI-powered household event planning system with RAG, multi-step workflow, and memory.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Import services (after app init so errors show clearly)
# ─────────────────────────────────────────────────────────────────────────────

from memory import get_session_manager, EventContext
from rag_pipeline import get_rag_pipeline
from workflow import get_workflow
from artifact_generator import render_artifact_markdown
import llm_service as llm
import spoonacular as spoon

# ─────────────────────────────────────────────────────────────────────────────
# Startup
# ─────────────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    rag = get_rag_pipeline()
    docs = rag.get_document_list()
    total_chunks = sum(d["chunk_count"] for d in docs)
    print(f"✅ RAG Pipeline ready: {len(docs)} documents, {total_chunks} chunks (sentence-transformers + ChromaDB)")
    print(f"✅ Gemini API: {'Configured' if os.getenv('GOOGLE_API_KEY') else 'Not set (demo mode)'}")
    print(f"✅ Spoonacular: {'Configured' if os.getenv('SPOONACULAR_API_KEY') else 'Not set (Tier 2 disabled)'}")


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────────────────────────────────────

class SessionCreateRequest(BaseModel):
    host_name: Optional[str] = None


class ChatRequest(BaseModel):
    session_id: str
    message: str


class EventContextUpdateRequest(BaseModel):
    session_id: str
    updates: Dict[str, Any]


class PlanStartRequest(BaseModel):
    session_id: str
    event_type: Optional[str] = None
    event_date: Optional[str] = None
    guest_count: Optional[int] = None
    budget: Optional[float] = None
    venue_type: Optional[str] = None
    theme: Optional[str] = None
    dietary_restrictions: Optional[List[str]] = None
    has_children: Optional[bool] = None
    has_elderly: Optional[bool] = None
    event_time: Optional[str] = None
    event_duration_hours: Optional[float] = None
    special_notes: Optional[str] = None


class ArtifactRequest(BaseModel):
    session_id: str
    enrich_with_spoonacular: Optional[bool] = False


class RetrievalRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    session_id: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "app": "Household Event Planner API",
        "version": "2.0.0",
        "status": "running",
        "llm": "Google Gemini",
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        "rag": "sentence-transformers (all-MiniLM-L6-v2) + ChromaDB",
        "ai_enabled": bool(os.getenv("GOOGLE_API_KEY")),
        "spoonacular_enabled": bool(os.getenv("SPOONACULAR_API_KEY")),
    }


@app.get("/api/health")
async def health():
    rag = get_rag_pipeline()
    docs = rag.get_document_list()
    sessions = get_session_manager().list_sessions()
    return {
        "status": "healthy",
        "rag_documents": len(docs),
        "rag_chunks": sum(d["chunk_count"] for d in docs),
        "embedding_model": os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        "active_sessions": len(sessions),
        "google_api_key": bool(os.getenv("GOOGLE_API_KEY")),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        "spoonacular_api_key": bool(os.getenv("SPOONACULAR_API_KEY")),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Session Management
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/session/create")
async def create_session(req: SessionCreateRequest):
    """Create a new planning session. Returns session_id for tracking."""
    manager = get_session_manager()
    session = manager.create()
    if req.host_name:
        session.event_context.host_name = req.host_name
    manager.save(session)
    return {
        "session_id": session.session_id,
        "created_at": session.created_at,
        "workflow_state": session.workflow_state,
        "message": "Planning session created. Tell me about the event you're planning!",
    }


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get full session state including event context and chat history."""
    manager = get_session_manager()
    session = manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@app.get("/api/session/{session_id}/context")
async def get_event_context(session_id: str):
    """Get current event context (planning state) for a session."""
    manager = get_session_manager()
    session = manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    ctx = session.event_context.to_dict()
    ctx["summary"] = session.event_context.get_summary()
    ctx["is_complete_for_planning"] = session.event_context.is_complete_for_planning()[0]
    return {
        "session_id": session_id,
        "workflow_state": session.workflow_state,
        "event_context": ctx,
    }


@app.patch("/api/session/{session_id}/context")
async def update_event_context(session_id: str, req: EventContextUpdateRequest):
    """Directly update event context fields."""
    manager = get_session_manager()
    session = manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.update_context(req.updates)
    manager.save(session)
    return {
        "session_id": session_id,
        "updated": True,
        "event_context": session.event_context.to_dict(),
    }


@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions."""
    manager = get_session_manager()
    return {"sessions": manager.list_sessions()}


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a planning session."""
    manager = get_session_manager()
    deleted = manager.delete(session_id)
    return {"deleted": deleted, "session_id": session_id}


# ─────────────────────────────────────────────────────────────────────────────
# Chat (multi-turn, with memory + RAG)
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat(req: ChatRequest):
    """
    Main chat endpoint.
    Processes user message through the multi-step workflow with:
    - RAG retrieval from knowledge base
    - Event context/state tracking (memory)
    - Agentic workflow orchestration
    - Citation of knowledge base sources
    """
    manager = get_session_manager()
    session = manager.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Please create a session first.")

    workflow = get_workflow()
    result = workflow.process_message(session, req.message)
    manager.save(session)

    return {
        "session_id": req.session_id,
        "workflow_state": session.workflow_state,
        "response": result.message,
        "citations": result.citations,
        "requires_input": result.requires_input,
        "questions": result.questions,
        "context_updated": result.context_updated,
        "conflicts": result.conflicts,
        "artifacts_ready": result.artifacts_ready,
        "event_context": session.event_context.to_dict(),
        "event_summary": session.event_context.get_summary(),
    }


@app.get("/api/chat/{session_id}/history")
async def get_chat_history(session_id: str, limit: int = 20):
    """Get recent chat messages for a session."""
    manager = get_session_manager()
    session = manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = session.chat_history.get_last_n(limit)
    return {
        "session_id": session_id,
        "messages": messages,
        "total_messages": len(session.chat_history.messages),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Planning Workflow
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/plan/start")
async def start_planning(req: PlanStartRequest):
    """
    Start or reset the planning workflow with initial event parameters.
    Automatically processes through available steps.
    """
    manager = get_session_manager()
    session = manager.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Apply all provided fields to event context
    updates = {}
    if req.event_type:
        updates["event_type"] = req.event_type
    if req.event_date:
        updates["event_date"] = req.event_date
    if req.guest_count:
        updates["guest_count_estimated"] = req.guest_count
    if req.budget:
        updates["budget_total"] = req.budget
    if req.venue_type:
        updates["venue_type"] = req.venue_type
    if req.theme:
        updates["theme"] = req.theme
    if req.dietary_restrictions is not None:
        updates["dietary_restrictions"] = req.dietary_restrictions
    if req.has_children is not None:
        updates["has_children"] = req.has_children
    if req.has_elderly is not None:
        updates["has_elderly"] = req.has_elderly
    if req.event_time:
        updates["event_time"] = req.event_time
    if req.event_duration_hours:
        updates["event_duration_hours"] = req.event_duration_hours
    if req.special_notes:
        updates["special_notes"] = req.special_notes

    if updates:
        session.update_context(updates)

    # Reset workflow to intake
    session.set_workflow_step("intake")
    manager.save(session)

    # Now process with a trigger message
    trigger_msg = f"I want to plan a {req.event_type or 'event'}."
    if updates:
        parts = []
        if req.event_type:
            parts.append(f"It's a {req.event_type}")
        if req.event_date:
            parts.append(f"on {req.event_date}")
        if req.guest_count:
            parts.append(f"for {req.guest_count} guests")
        if req.budget:
            parts.append(f"with a ${req.budget:.0f} budget")
        if req.venue_type:
            parts.append(f"at {req.venue_type}")
        trigger_msg = "I want to plan " + " ".join(parts) + "."

    workflow = get_workflow()
    result = workflow.process_message(session, trigger_msg)
    manager.save(session)

    return {
        "session_id": req.session_id,
        "workflow_state": session.workflow_state,
        "response": result.message,
        "citations": result.citations,
        "requires_input": result.requires_input,
        "questions": result.questions,
        "conflicts": result.conflicts,
        "event_context": session.event_context.to_dict(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Artifacts
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/artifacts/generate")
async def generate_artifacts(req: ArtifactRequest):
    """
    Trigger artifact generation for a session.
    Generates: Task Checklist, Shopping List, Day-of Schedule.
    Optionally enriches with Spoonacular recipe data (Tier 2).
    """
    manager = get_session_manager()
    session = manager.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    workflow = get_workflow()
    session.set_workflow_step("artifact_generation")
    result = workflow.process_message(session, "generate artifacts")
    manager.save(session)

    artifacts = session.artifacts

    # Enrich shopping list with Spoonacular if requested
    if req.enrich_with_spoonacular and artifacts.get("shopping_list"):
        ctx = session.event_context
        enriched = await spoon.enrich_shopping_list(
            shopping_list=artifacts["shopping_list"],
            event_type=ctx.event_type or "party",
            dietary_restrictions=ctx.dietary_restrictions or [],
            guest_count=ctx.guest_count_estimated or ctx.guest_count_confirmed or 20,
        )
        artifacts["shopping_list"] = enriched
        manager.save(session)

    return {
        "session_id": req.session_id,
        "artifacts": artifacts,
        "message": result.message,
        "citations": result.citations,
    }


@app.get("/api/artifacts/{session_id}")
async def get_artifacts(session_id: str):
    """Get all generated artifacts for a session."""
    manager = get_session_manager()
    session = manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.artifacts:
        return {
            "session_id": session_id,
            "artifacts": None,
            "message": "No artifacts generated yet. Complete the planning workflow first.",
        }

    return {
        "session_id": session_id,
        "artifacts": session.artifacts,
        "generated_at": session.artifacts.get("generated_at"),
    }


@app.get("/api/artifacts/{session_id}/{artifact_type}/markdown")
async def get_artifact_markdown(session_id: str, artifact_type: str):
    """Get a specific artifact rendered as Markdown text."""
    manager = get_session_manager()
    session = manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.artifacts:
        raise HTTPException(status_code=404, detail="No artifacts generated yet")

    artifact = session.artifacts.get(artifact_type)
    if not artifact:
        raise HTTPException(status_code=404, detail=f"Artifact '{artifact_type}' not found")

    markdown = render_artifact_markdown(artifact)
    return PlainTextResponse(content=markdown, media_type="text/markdown")


@app.get("/api/artifacts/{session_id}/download")
async def download_all_artifacts(session_id: str):
    """Download all artifacts as a combined JSON package."""
    manager = get_session_manager()
    session = manager.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.artifacts:
        raise HTTPException(status_code=404, detail="No artifacts generated yet")

    package = {
        "session_id": session_id,
        "event_summary": session.event_context.get_summary(),
        "event_context": session.event_context.to_dict(),
        "generated_at": session.artifacts.get("generated_at"),
        "task_checklist": session.artifacts.get("task_checklist"),
        "shopping_list": session.artifacts.get("shopping_list"),
        "day_of_schedule": session.artifacts.get("day_of_schedule"),
    }

    return JSONResponse(
        content=package,
        headers={"Content-Disposition": f"attachment; filename=event_plan_{session_id[:8]}.json"},
    )


# ─────────────────────────────────────────────────────────────────────────────
# RAG / Knowledge Base
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/rag/documents")
async def list_documents():
    """List all knowledge base documents available for retrieval."""
    rag = get_rag_pipeline()
    docs = rag.get_document_list()
    return {
        "documents": docs,
        "total": len(docs),
        "total_chunks": sum(d["chunk_count"] for d in docs),
    }


@app.post("/api/rag/retrieve")
async def retrieve_documents(req: RetrievalRequest):
    """
    Manually trigger RAG retrieval for a query.
    Returns top-k most relevant knowledge base chunks with citations.
    """
    rag = get_rag_pipeline()

    event_context = None
    if req.session_id:
        session = get_session_manager().get(req.session_id)
        if session:
            event_context = session.event_context.to_dict()

    chunks = rag.retrieve(req.query, top_k=req.top_k or 5, event_context=event_context)
    citations = rag.get_citations(chunks)

    return {
        "query": req.query,
        "retrieved_chunks": chunks,
        "citations": citations,
        "total_retrieved": len(chunks),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Spoonacular (Tier 2)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/spoonacular/recipes")
async def get_recipes(
    event_type: str = "birthday party",
    servings: int = 20,
    dietary: Optional[str] = None,
):
    """Search for recipes appropriate for the event type (Spoonacular Tier 2)."""
    restrictions = [r.strip() for r in dietary.split(",")] if dietary else []
    recipes = await spoon.search_recipes_for_event(event_type, restrictions, servings)
    return {
        "event_type": event_type,
        "servings": servings,
        "dietary_restrictions": restrictions,
        "recipes": recipes,
        "spoonacular_enabled": bool(os.getenv("SPOONACULAR_API_KEY")),
    }


@app.get("/api/spoonacular/ingredients/{recipe_id}")
async def get_ingredients(recipe_id: int, servings: int = 20):
    """Get scaled ingredient list for a recipe (Spoonacular Tier 2)."""
    ingredients = await spoon.get_recipe_ingredients(recipe_id, servings)
    return {
        "recipe_id": recipe_id,
        "servings": servings,
        "ingredients": ingredients,
        "spoonacular_enabled": bool(os.getenv("SPOONACULAR_API_KEY")),
    }


@app.get("/api/spoonacular/substitute/{ingredient}")
async def get_substitutions(ingredient: str):
    """Get substitution suggestions for an ingredient."""
    subs = await spoon.get_ingredient_substitutions(ingredient)
    return {"ingredient": ingredient, "substitutions": subs}


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", 8000))
    host = os.getenv("APP_HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "true").lower() == "true"
    uvicorn.run("main:app", host=host, port=port, reload=debug)
