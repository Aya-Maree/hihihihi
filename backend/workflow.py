"""
Multi-Step Planning Workflow (Agentic Logic).
Orchestrates 7 conditional workflow steps:
  1. intake → 2. clarification → 3. retrieval → 4. conflict_detection
  → 5. planning → 6. validation → 7. artifact_generation → 8. complete

Each step is conditionally structured: the system responds differently
based on event context, conflicts detected, and user inputs.
"""

from typing import Dict, List, Tuple, Optional
from memory import PlanningSession, EventContext
from rag_pipeline import get_rag_pipeline
from web_search import web_search, should_web_search
import llm_service as llm
import artifact_generator as ag
from datetime import datetime


class WorkflowResult:
    """Result of a workflow step execution."""

    def __init__(
        self,
        step: str,
        message: str,
        citations: List[Dict] = None,
        requires_input: bool = False,
        questions: List[str] = None,
        context_updated: bool = False,
        conflicts: List[str] = None,
        next_step: Optional[str] = None,
        artifacts_ready: bool = False,
    ):
        self.step = step
        self.message = message
        self.citations = citations or []
        self.requires_input = requires_input
        self.questions = questions or []
        self.context_updated = context_updated
        self.conflicts = conflicts or []
        self.next_step = next_step
        self.artifacts_ready = artifacts_ready

    def to_dict(self) -> Dict:
        return {
            "step": self.step,
            "message": self.message,
            "citations": self.citations,
            "requires_input": self.requires_input,
            "questions": self.questions,
            "context_updated": self.context_updated,
            "conflicts": self.conflicts,
            "next_step": self.next_step,
            "artifacts_ready": self.artifacts_ready,
        }


class PlanningWorkflow:
    """
    Orchestrates the full 7-step event planning workflow.
    Each step is conditional — the system selects actions based on
    what it knows and what gaps or conflicts exist.
    """

    def __init__(self):
        self.rag = get_rag_pipeline()

    def _maybe_add_web_results(self, query: str, local_chunks: List[Dict]) -> List[Dict]:
        """Supplement local KB chunks with web search results if warranted."""
        if should_web_search(query, local_chunks):
            web_results = web_search(query)
            if web_results:
                return local_chunks + web_results
        return local_chunks

    def process_message(self, session: PlanningSession, user_message: str) -> WorkflowResult:
        """
        Main entry point: process a user message in the context of the current workflow step.
        Routes to the appropriate step handler.
        """
        step = session.workflow_state

        # Add user message to history
        session.chat_history.add("user", user_message)

        # Extract and update event context from the user's message
        context_updates = llm.extract_event_context_from_intake(
            user_message, session.event_context.to_dict()
        )
        if context_updates:
            session.update_context(context_updates)

        # Route based on current workflow step
        if step == "intake":
            result = self._handle_intake(session, user_message)
        elif step == "clarification":
            result = self._handle_clarification(session, user_message)
        elif step == "retrieval":
            result = self._handle_retrieval(session)
        elif step == "conflict_detection":
            result = self._handle_conflict_detection(session)
        elif step == "planning":
            result = self._handle_planning(session, user_message)
        elif step == "validation":
            result = self._handle_validation(session, user_message)
        elif step == "artifact_generation":
            result = self._handle_artifact_generation(session)
        elif step == "complete":
            result = self._handle_complete(session, user_message)
        else:
            result = self._handle_intake(session, user_message)

        # Add assistant response to chat history
        session.chat_history.add(
            "assistant",
            result.message,
            metadata={
                "step": result.step,
                "citations": result.citations,
                "conflicts": result.conflicts,
            },
        )

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # Step 1: Intake — Collect event parameters
    # ─────────────────────────────────────────────────────────────────────────

    def _handle_intake(self, session: PlanningSession, user_message: str) -> WorkflowResult:
        ctx = session.event_context
        is_complete, missing = ctx.is_complete_for_planning()

        if is_complete:
            # Enough info collected — move to clarification
            session.set_workflow_step("clarification")
            result = self._handle_clarification(session, user_message)
            result.context_updated = True
            return result

        # RAG retrieval based on whatever context we have so far, so even
        # early responses are grounded in the knowledge base
        query_parts = [ctx.event_type or "event planning"]
        if ctx.venue_type:
            query_parts.append(ctx.venue_type)
        if ctx.dietary_restrictions:
            query_parts.append("dietary " + " ".join(ctx.dietary_restrictions))
        if ctx.guest_count_estimated or ctx.guest_count_confirmed:
            guests = ctx.guest_count_estimated or ctx.guest_count_confirmed
            query_parts.append(f"{guests} guests")
        if ctx.has_children:
            query_parts.append("children activities")
        if ctx.has_elderly:
            query_parts.append("elderly accessibility")
        # Also include any keywords from the user's current message
        query_parts.append(user_message[:120])

        query = " ".join(query_parts)
        chunks = self.rag.retrieve(query, top_k=4, event_context=ctx.to_dict())
        session.retrieved_docs = chunks
        citations = self.rag.get_citations(chunks)

        # Generate clarification questions for the missing fields
        questions = llm.generate_clarification_questions(ctx.to_dict(), [f"Missing: {m}" for m in missing])

        # Use chat_with_context so the KB grounds the response, while the
        # system prompt instructs it to also ask for the missing fields
        missing_prompt = (
            f"\n\nBefore you can build the full plan, you still need these details from the user: "
            f"{', '.join(missing)}. "
            f"Answer any specific questions the user just asked using the knowledge base above, "
            f"then ask for the missing information in a friendly, numbered list."
        )

        chat_result = llm.chat_with_context(
            user_message=user_message + missing_prompt,
            chat_history=session.chat_history.get_for_llm()[-6:],
            event_context=ctx.to_dict(),
            retrieved_chunks=chunks,
            workflow_state="intake",
        )

        message = chat_result["response"]
        # Append questions as a fallback footer if LLM didn't surface them
        if questions and not any(q[:30].lower() in message.lower() for q in questions):
            message += "\n\n**To build your plan I still need:**\n"
            for i, q in enumerate(questions, 1):
                message += f"{i}. {q}\n"

        message += "\n\n*You can provide all this information in one message or answer step by step.*"

        return WorkflowResult(
            step="intake",
            message=message,
            citations=citations,
            requires_input=True,
            questions=questions,
            context_updated=bool(chat_result.get("context_updates")),
            next_step="clarification",
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Step 2: Clarification — Identify ambiguities and ask targeted questions
    # ─────────────────────────────────────────────────────────────────────────

    def _handle_clarification(self, session: PlanningSession, user_message: str) -> WorkflowResult:
        ctx = session.event_context
        is_complete, missing = ctx.is_complete_for_planning()

        if not is_complete:
            return self._handle_intake(session, user_message)

        # If the user is responding to previously detected conflicts, go straight to
        # planning — do NOT re-run retrieval→conflict_detection or they'll loop forever
        # on unresolvable conflicts (e.g. a date that is already close).
        if ctx.detected_conflicts:
            session.set_workflow_step("planning")
            return self._handle_planning(session, user_message)

        # Check for dietary/accessibility gaps
        clarification_needed = []
        if not ctx.dietary_restrictions and not any(
            word in user_message.lower() for word in ["no restriction", "no dietary", "none"]
        ):
            clarification_needed.append(
                "Do any guests have dietary restrictions (vegetarian, vegan, gluten-free, nut allergy)? "
                "If none, just say 'no restrictions'."
            )

        if session.clarification_questions and clarification_needed:
            # Use the already-retrieved docs (or do a fresh retrieval) so the
            # clarification message is grounded in the knowledge base
            chunks = session.retrieved_docs
            if not chunks:
                query = (ctx.event_type or "event planning") + " dietary restrictions accessibility"
                chunks = self.rag.retrieve(query, top_k=4, event_context=ctx.to_dict())
                session.retrieved_docs = chunks
            citations = self.rag.get_citations(chunks)

            chat_result = llm.chat_with_context(
                user_message=(
                    "Almost there! One more quick question before building the plan: "
                    + " ".join(clarification_needed)
                ),
                chat_history=session.chat_history.get_for_llm()[-6:],
                event_context=ctx.to_dict(),
                retrieved_chunks=chunks,
                workflow_state="clarification",
            )

            return WorkflowResult(
                step="clarification",
                message=chat_result["response"],
                citations=citations,
                requires_input=True,
                questions=clarification_needed,
                next_step="retrieval",
            )

        # Mark clarification done — move to retrieval
        session.clarification_questions = []
        session.set_workflow_step("retrieval")
        return self._handle_retrieval(session)

    # ─────────────────────────────────────────────────────────────────────────
    # Step 3: Retrieval — Fetch relevant knowledge base documents
    # ─────────────────────────────────────────────────────────────────────────

    def _handle_retrieval(self, session: PlanningSession) -> WorkflowResult:
        ctx = session.event_context

        # Build retrieval query from event context
        query_parts = [ctx.event_type or "party planning"]
        if ctx.dietary_restrictions:
            query_parts.append("dietary restrictions " + " ".join(ctx.dietary_restrictions))
        if ctx.has_children:
            query_parts.append("children activities entertainment")
        if ctx.venue_type:
            query_parts.append(ctx.venue_type)
        if ctx.budget_total:
            query_parts.append(f"budget ${ctx.budget_total:.0f}")
        if ctx.guest_count_estimated or ctx.guest_count_confirmed:
            guests = ctx.guest_count_estimated or ctx.guest_count_confirmed
            query_parts.append(f"{guests} guests shopping catering")

        query = " ".join(query_parts)

        # Retrieve from knowledge base
        chunks = self.rag.retrieve(query, top_k=6, event_context=ctx.to_dict())
        session.retrieved_docs = chunks
        citations = self.rag.get_citations(chunks)

        # Move to conflict detection
        session.set_workflow_step("conflict_detection")
        result = self._handle_conflict_detection(session)
        result.citations = citations
        return result

    # ─────────────────────────────────────────────────────────────────────────
    # Step 4: Conflict Detection — Check for planning issues
    # ─────────────────────────────────────────────────────────────────────────

    def _handle_conflict_detection(self, session: PlanningSession) -> WorkflowResult:
        ctx = session.event_context
        chunks = session.retrieved_docs

        # Detect conflicts using LLM + knowledge base context
        conflicts = llm.detect_conflicts(ctx.to_dict(), chunks)
        session.event_context.detected_conflicts = conflicts

        citations = self.rag.get_citations(chunks)

        if conflicts:
            # Ask targeted resolution questions
            questions = []
            for conflict in conflicts[:3]:
                if "budget" in conflict.lower():
                    questions.append(
                        f"⚠️ {conflict}\n   → Would you like to adjust your budget, reduce the guest list, or simplify the menu?"
                    )
                elif "date" in conflict.lower() or "time" in conflict.lower():
                    questions.append(
                        f"⚠️ {conflict}\n   → Can you adjust the date or start tasks immediately?"
                    )
                else:
                    questions.append(f"⚠️ {conflict}\n   → How would you like to address this?")

            session.set_workflow_step("clarification")

            msg = (
                "**I've analyzed your event plan against our knowledge base and found some things to address:**\n\n"
                + "\n\n".join(questions)
                + "\n\n*Please respond to these issues so I can generate an accurate plan. "
                "Reply with your preferred resolutions (e.g., 'increase budget to $400', 'reduce guests to 15').*"
            )

            return WorkflowResult(
                step="conflict_detection",
                message=msg,
                citations=citations,
                requires_input=True,
                questions=questions,
                conflicts=conflicts,
                next_step="planning",
            )

        # No conflicts — proceed to planning
        session.set_workflow_step("planning")
        return self._handle_planning(session, "")

    # ─────────────────────────────────────────────────────────────────────────
    # Step 5: Planning — Generate comprehensive event plan
    # ─────────────────────────────────────────────────────────────────────────

    def _handle_planning(self, session: PlanningSession, user_message: str) -> WorkflowResult:
        ctx = session.event_context
        chunks = session.retrieved_docs

        # If user resolved conflicts, re-detect
        if user_message and ctx.detected_conflicts:
            # Update context from resolution message
            updates = llm.extract_event_context_from_intake(user_message, ctx.to_dict())
            if updates:
                session.update_context(updates)
                ctx = session.event_context
            ctx.detected_conflicts = []
            # Re-retrieve with updated context
            query = (ctx.event_type or "party") + " planning schedule budget shopping"
            chunks = self.rag.retrieve(query, top_k=6, event_context=ctx.to_dict())
            session.retrieved_docs = chunks

        citations = self.rag.get_citations(chunks)
        response = llm.generate_planning_response(
            ctx.to_dict(),
            chunks,
            "Generate a comprehensive event planning overview with key recommendations.",
        )

        session.set_workflow_step("validation")

        message = (
            response
            + "\n\n---\n"
            "**I've reviewed your plan against the knowledge base guidelines.** "
            "You can now:\n"
            "- Type **'generate artifacts'** to get your complete Task Checklist, Shopping List, and Day-of Schedule\n"
            "- Ask any specific planning questions\n"
            "- Type **'adjust'** followed by any change you'd like to make\n"
        )

        return WorkflowResult(
            step="planning",
            message=message,
            citations=citations,
            requires_input=True,
            next_step="validation",
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Step 6: Validation — Check final constraints before artifact generation
    # ─────────────────────────────────────────────────────────────────────────

    def _handle_validation(self, session: PlanningSession, user_message: str) -> WorkflowResult:
        ctx = session.event_context
        chunks = session.retrieved_docs

        # Check if user asked for artifacts
        trigger_words = ["generate", "artifact", "checklist", "shopping", "schedule", "download", "create plan"]
        if any(word in user_message.lower() for word in trigger_words):
            session.set_workflow_step("artifact_generation")
            return self._handle_artifact_generation(session)

        # Handle adjustment requests
        if "adjust" in user_message.lower() or "change" in user_message.lower():
            updates = llm.extract_event_context_from_intake(user_message, ctx.to_dict())
            if updates:
                session.update_context(updates)
            # Re-retrieve and re-plan
            query = (ctx.event_type or "party") + " planning"
            chunks = self.rag.retrieve(query, top_k=6, event_context=ctx.to_dict())
            session.retrieved_docs = chunks
            session.set_workflow_step("planning")
            return self._handle_planning(session, user_message)

        # General chat during validation — answer using RAG + web search
        query = user_message
        specific_chunks = self.rag.retrieve(query, top_k=4, event_context=ctx.to_dict())
        specific_chunks = self._maybe_add_web_results(query, specific_chunks)
        if specific_chunks:
            chunks = specific_chunks
        citations = self.rag.get_citations(chunks) + [
            c for c in chunks if c.get("source_type") == "web"
            and c.get("doc_id") not in {x.get("doc_id") for x in self.rag.get_citations(chunks)}
        ]

        chat_result = llm.chat_with_context(
            user_message=user_message,
            chat_history=session.chat_history.get_for_llm()[-8:],
            event_context=ctx.to_dict(),
            retrieved_chunks=chunks,
            workflow_state="validation",
        )

        # Apply any context updates from chat
        if chat_result.get("context_updates"):
            session.update_context(chat_result["context_updates"])

        message = (
            chat_result["response"]
            + "\n\n*When you're ready, type **'generate artifacts'** to create your complete planning documents.*"
        )

        return WorkflowResult(
            step="validation",
            message=message,
            citations=citations,
            requires_input=True,
            context_updated=bool(chat_result.get("context_updates")),
            conflicts=chat_result.get("detected_conflicts", []),
            next_step="artifact_generation",
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Step 7: Artifact Generation — Generate all 3 structured outputs
    # ─────────────────────────────────────────────────────────────────────────

    def _handle_artifact_generation(self, session: PlanningSession) -> WorkflowResult:
        ctx = session.event_context
        chunks = session.retrieved_docs

        # Ensure we have recent retrieval for artifact context
        if not chunks:
            query = (ctx.event_type or "event") + " planning checklist shopping schedule"
            chunks = self.rag.retrieve(query, top_k=8, event_context=ctx.to_dict())
            session.retrieved_docs = chunks

        citations = self.rag.get_citations(chunks)

        # Generate all 3 artifacts
        checklist = llm.generate_artifact_json("task_checklist", ctx.to_dict(), chunks)
        shopping_list = llm.generate_artifact_json("shopping_list", ctx.to_dict(), chunks)
        schedule = llm.generate_artifact_json("day_of_schedule", ctx.to_dict(), chunks)

        session.artifacts = {
            "task_checklist": checklist,
            "shopping_list": shopping_list,
            "day_of_schedule": schedule,
            "generated_at": datetime.now().isoformat(),
        }

        # Update budget allocation from shopping list
        if shopping_list.get("total_cost"):
            session.event_context.budget_allocated = shopping_list["total_cost"]

        # Update pending tasks from checklist
        if checklist.get("categories"):
            all_tasks = []
            for cat in checklist["categories"]:
                for task in cat.get("tasks", []):
                    all_tasks.append({
                        "title": task.get("title"),
                        "status": "pending",
                        "category": cat.get("name"),
                        "priority": task.get("priority", "medium"),
                    })
            session.event_context.pending_tasks = all_tasks

        session.set_workflow_step("complete")

        total_cost = shopping_list.get("total_cost", 0)
        budget = ctx.budget_total or 0
        budget_line = (
            f"\n💰 **Estimated Total Cost: ${total_cost:.2f}** "
            f"({'Within budget!' if total_cost <= budget else f'Over budget by ${total_cost - budget:.2f} — review shopping list.'})"
            if budget else ""
        )

        task_count = sum(len(c.get("tasks", [])) for c in checklist.get("categories", []))
        schedule_blocks = (
            len(schedule.get("setup_blocks", []))
            + len(schedule.get("event_blocks", []))
            + len(schedule.get("cleanup_blocks", []))
        )

        message = (
            f"✅ **Your complete event plan is ready!**\n\n"
            f"I've generated **3 structured planning documents** based on your event details and "
            f"{len(citations)} knowledge base sources:\n\n"
            f"📋 **Task Checklist** — {task_count} tasks across 5 time horizons\n"
            f"🛒 **Shopping List** — {sum(len(c.get('items', [])) for c in shopping_list.get('categories', []))} items organized by category{budget_line}\n"
            f"📅 **Day-of Schedule** — {schedule_blocks} time blocks covering setup, event, and cleanup\n\n"
            f"Use the **Artifacts** tab to view and download your planning documents.\n"
            f"You can still ask questions or request changes — I'll update the plan accordingly."
        )

        return WorkflowResult(
            step="artifact_generation",
            message=message,
            citations=citations,
            artifacts_ready=True,
            context_updated=True,
            next_step="complete",
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Step 8: Complete — Ongoing Q&A with memory
    # ─────────────────────────────────────────────────────────────────────────

    def _handle_complete(self, session: PlanningSession, user_message: str) -> WorkflowResult:
        ctx = session.event_context
        chunks = session.retrieved_docs

        # Check if user wants to regenerate artifacts
        if any(word in user_message.lower() for word in ["regenerate", "update artifacts", "new plan", "redo"]):
            session.set_workflow_step("artifact_generation")
            return self._handle_artifact_generation(session)

        # Retrieve relevant chunks for the specific question, supplement with web if needed
        specific_chunks = self.rag.retrieve(user_message, top_k=4, event_context=ctx.to_dict())
        specific_chunks = self._maybe_add_web_results(user_message, specific_chunks)
        if specific_chunks:
            chunks = specific_chunks

        kb_citations = self.rag.get_citations([c for c in chunks if c.get("source_type") != "web"])
        web_citations = [c for c in chunks if c.get("source_type") == "web"]
        citations = kb_citations + web_citations

        chat_result = llm.chat_with_context(
            user_message=user_message,
            chat_history=session.chat_history.get_for_llm()[-10:],
            event_context=ctx.to_dict(),
            retrieved_chunks=chunks,
            workflow_state="complete",
        )

        # Apply context updates
        if chat_result.get("context_updates"):
            session.update_context(chat_result["context_updates"])

        return WorkflowResult(
            step="complete",
            message=chat_result["response"],
            citations=citations,
            context_updated=bool(chat_result.get("context_updates")),
            conflicts=chat_result.get("detected_conflicts", []),
            requires_input=True,
            artifacts_ready=bool(session.artifacts),
        )


# Global workflow instance
_workflow: Optional[PlanningWorkflow] = None


def get_workflow() -> PlanningWorkflow:
    global _workflow
    if _workflow is None:
        _workflow = PlanningWorkflow()
    return _workflow
