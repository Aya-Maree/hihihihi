"""
Session Memory and Event Context Management.
Tracks multi-turn chat history, event planning state, and workflow progress.
"""

import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict


@dataclass
class EventContext:
    """
    Structured event context object — the core state that persists across
    all planning steps and chat turns.
    """
    event_type: Optional[str] = None          # "birthday party", "dinner party", etc.
    event_date: Optional[str] = None          # ISO date string YYYY-MM-DD
    event_time: Optional[str] = None          # "14:00" 24h format
    event_duration_hours: Optional[float] = None  # Duration in hours
    guest_count_estimated: Optional[int] = None
    guest_count_confirmed: Optional[int] = None
    budget_total: Optional[float] = None      # Total budget in dollars
    budget_allocated: float = 0.0             # Running allocated budget
    venue_type: Optional[str] = None          # "home", "rented hall", "outdoor", etc.
    location: Optional[str] = None            # Address or description
    theme: Optional[str] = None               # Party theme
    dietary_restrictions: List[str] = field(default_factory=list)
    accessibility_needs: List[str] = field(default_factory=list)
    has_children: bool = False
    has_elderly: bool = False
    entertainment_preferences: List[str] = field(default_factory=list)
    confirmed_vendors: List[Dict] = field(default_factory=list)
    confirmed_tasks: List[Dict] = field(default_factory=list)
    pending_tasks: List[Dict] = field(default_factory=list)
    shopping_list: List[Dict] = field(default_factory=list)
    schedule_blocks: List[Dict] = field(default_factory=list)
    detected_conflicts: List[str] = field(default_factory=list)
    special_notes: Optional[str] = None
    host_name: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "EventContext":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def get_summary(self) -> str:
        """Return a concise text summary of the current event context."""
        parts = []
        if self.event_type:
            parts.append(f"Event: {self.event_type}")
        if self.event_date:
            parts.append(f"Date: {self.event_date}")
        if self.event_time:
            parts.append(f"Time: {self.event_time}")
        if self.guest_count_confirmed or self.guest_count_estimated:
            count = self.guest_count_confirmed or self.guest_count_estimated
            label = "confirmed" if self.guest_count_confirmed else "estimated"
            parts.append(f"Guests: {count} ({label})")
        if self.budget_total:
            remaining = self.budget_total - self.budget_allocated
            parts.append(f"Budget: ${self.budget_total:.0f} total, ${remaining:.0f} remaining")
        if self.venue_type:
            parts.append(f"Venue: {self.venue_type}")
        if self.theme:
            parts.append(f"Theme: {self.theme}")
        if self.dietary_restrictions:
            parts.append(f"Dietary needs: {', '.join(self.dietary_restrictions)}")
        if self.detected_conflicts:
            parts.append(f"⚠ Conflicts detected: {len(self.detected_conflicts)}")
        return " | ".join(parts) if parts else "No event details collected yet."

    def is_complete_for_planning(self) -> Tuple[bool, List[str]]:
        """Check whether the context has enough info to start planning."""
        missing = []
        if not self.event_type:
            missing.append("event type")
        if not self.event_date:
            missing.append("event date")
        if not self.guest_count_estimated and not self.guest_count_confirmed:
            missing.append("guest count")
        if not self.budget_total:
            missing.append("total budget")
        if not self.venue_type:
            missing.append("venue type (home / rented hall / outdoor)")
        return len(missing) == 0, missing


@dataclass
class ChatMessage:
    """A single chat message."""
    role: str           # "user" or "assistant" or "system"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


class ChatHistory:
    """Manages the conversation history for a session."""

    MAX_HISTORY = 50  # Keep last 50 messages to avoid token overflow

    def __init__(self):
        self.messages: List[ChatMessage] = []

    def add(self, role: str, content: str, metadata: Optional[Dict] = None) -> ChatMessage:
        msg = ChatMessage(role=role, content=content, metadata=metadata or {})
        self.messages.append(msg)
        if len(self.messages) > self.MAX_HISTORY:
            # Keep system messages + last (MAX_HISTORY - 10) messages
            system_msgs = [m for m in self.messages if m.role == "system"]
            other_msgs = [m for m in self.messages if m.role != "system"]
            self.messages = system_msgs + other_msgs[-(self.MAX_HISTORY - len(system_msgs)):]
        return msg

    def get_for_llm(self, include_system: bool = False) -> List[Dict]:
        """Return messages in LLM-compatible format (role + content dicts)."""
        return [
            {"role": m.role, "content": m.content}
            for m in self.messages
            if include_system or m.role != "system"
        ]

    def get_last_n(self, n: int) -> List[Dict]:
        """Return last n messages."""
        return [m.to_dict() for m in self.messages[-n:]]

    def to_list(self) -> List[Dict]:
        return [m.to_dict() for m in self.messages]

    @classmethod
    def from_list(cls, data: List[Dict]) -> "ChatHistory":
        h = cls()
        for item in data:
            h.messages.append(ChatMessage(**item))
        return h


class PlanningSession:
    """
    Complete planning session: combines chat history, event context,
    workflow state, and generated artifacts.
    """

    WORKFLOW_STEPS = [
        "intake",
        "clarification",
        "retrieval",
        "conflict_detection",
        "planning",
        "validation",
        "artifact_generation",
        "complete",
    ]

    def __init__(self, session_id: Optional[str] = None):
        self.session_id: str = session_id or str(uuid.uuid4())
        self.created_at: str = datetime.now().isoformat()
        self.updated_at: str = datetime.now().isoformat()
        self.chat_history: ChatHistory = ChatHistory()
        self.event_context: EventContext = EventContext()
        self.workflow_state: str = "intake"
        self.retrieved_docs: List[Dict] = []
        self.artifacts: Dict[str, Any] = {}
        self.clarification_questions: List[str] = []
        self.resolved_conflicts: List[str] = []

    def advance_workflow(self) -> str:
        """Move to the next workflow step."""
        current_idx = self.WORKFLOW_STEPS.index(self.workflow_state)
        if current_idx < len(self.WORKFLOW_STEPS) - 1:
            self.workflow_state = self.WORKFLOW_STEPS[current_idx + 1]
        self.updated_at = datetime.now().isoformat()
        return self.workflow_state

    def set_workflow_step(self, step: str) -> None:
        if step in self.WORKFLOW_STEPS:
            self.workflow_state = step
            self.updated_at = datetime.now().isoformat()

    def update_context(self, updates: Dict) -> None:
        """Update event context fields from a dict."""
        ctx = self.event_context.to_dict()
        for key, value in updates.items():
            if key in ctx or hasattr(self.event_context, key):
                setattr(self.event_context, key, value)
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "workflow_state": self.workflow_state,
            "event_context": self.event_context.to_dict(),
            "chat_history": self.chat_history.to_list(),
            "retrieved_docs": self.retrieved_docs,
            "artifacts": self.artifacts,
            "clarification_questions": self.clarification_questions,
            "resolved_conflicts": self.resolved_conflicts,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "PlanningSession":
        session = cls(session_id=data["session_id"])
        session.created_at = data.get("created_at", session.created_at)
        session.updated_at = data.get("updated_at", session.updated_at)
        session.workflow_state = data.get("workflow_state", "intake")
        session.event_context = EventContext.from_dict(data.get("event_context", {}))
        session.chat_history = ChatHistory.from_list(data.get("chat_history", []))
        session.retrieved_docs = data.get("retrieved_docs", [])
        session.artifacts = data.get("artifacts", {})
        session.clarification_questions = data.get("clarification_questions", [])
        session.resolved_conflicts = data.get("resolved_conflicts", [])
        return session


class SessionManager:
    """In-memory session store with optional JSON file persistence."""

    def __init__(self, persist_dir: Optional[str] = None):
        self._sessions: Dict[str, PlanningSession] = {}
        self.persist_dir = persist_dir

    def create(self) -> PlanningSession:
        """Create a new planning session."""
        session = PlanningSession()
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Optional[PlanningSession]:
        """Retrieve a session by ID."""
        return self._sessions.get(session_id)

    def save(self, session: PlanningSession) -> None:
        """Update session in store."""
        session.updated_at = datetime.now().isoformat()
        self._sessions[session.session_id] = session

    def delete(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def list_sessions(self) -> List[Dict]:
        """Return summary of all active sessions."""
        return [
            {
                "session_id": s.session_id,
                "workflow_state": s.workflow_state,
                "event_summary": s.event_context.get_summary(),
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "message_count": len(s.chat_history.messages),
            }
            for s in self._sessions.values()
        ]


# Global session manager
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
