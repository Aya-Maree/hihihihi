"""
LLM Service — Google Gemini API integration.
All LLM interactions use Gemini (gemini-1.5-flash by default).
Falls back to template-based responses if no API key is configured (demo mode).
"""

import os
import json
import re
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ─────────────────────────────────────────────────────────────────────────────
# Gemini client helper (google-genai SDK)
# ─────────────────────────────────────────────────────────────────────────────

def _call_gemini(
    messages: List[Dict],
    system_prompt: str,
    max_tokens: int = 2048,
) -> Optional[str]:
    """
    Call Gemini using the google-genai SDK.
    Accepts a list of {role, content} messages and a system prompt.
    Returns response text, or None if unavailable (triggers template fallback).
    """
    if not GOOGLE_API_KEY:
        return None
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GOOGLE_API_KEY)

        # Build chat history (all messages except the last/current one)
        history = []
        for msg in messages[:-1]:
            role = "model" if msg["role"] == "assistant" else "user"
            history.append(
                types.Content(role=role, parts=[types.Part(text=msg["content"])])
            )

        current_message = messages[-1]["content"] if messages else ""

        chat = client.chats.create(
            model=GEMINI_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
                temperature=0.7,
            ),
            history=history,
        )

        response = chat.send_message(current_message)
        return response.text
    except ImportError:
        print("google-genai not installed. Run: pip install google-genai")
        return None
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# System prompt
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_BASE = """You are an expert household event planning assistant with access to a curated knowledge base.
Your role is to help users plan events (birthday parties, dinner parties, holiday gatherings, graduations, etc.)
by providing structured, actionable planning advice grounded in the retrieved knowledge base.

Core behaviors:
- Base ALL recommendations on the provided knowledge base context
- Cite your sources explicitly using the format [Source: document_name] 
- Track the event context (budget, guests, dietary restrictions, venue, etc.) throughout the conversation
- Be specific: give concrete quantities, costs, and timelines from the knowledge base
- Ask targeted clarifying questions when critical information is missing
- Detect and flag conflicts (e.g., budget too low for guest count, timeline too tight)
- Generate structured, actionable outputs, not vague advice
- Never fabricate costs or quantities — use the retrieved documents as your reference"""


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def chat_with_context(
    user_message: str,
    chat_history: List[Dict],
    event_context: Dict,
    retrieved_chunks: List[Dict],
    workflow_state: str,
) -> Dict:
    """
    Main chat function: generates a Gemini response given:
    - user message (current turn)
    - chat history (memory across turns)
    - event context (planning state)
    - retrieved chunks (RAG context from knowledge base)
    - current workflow state

    Returns: {response, citations, context_updates, workflow_advance, detected_conflicts}
    """
    rag_context = _build_rag_context(retrieved_chunks)
    event_summary = _summarize_context(event_context)

    system_prompt = f"""{SYSTEM_PROMPT_BASE}

CURRENT EVENT CONTEXT (JSON state):
{event_summary}

CURRENT WORKFLOW STEP: {workflow_state}

{rag_context}

Response instructions:
- Ground your response in the knowledge base context above
- Cite sources using [Source: doc_id] format
- If you detect any context updates (new info from the user), include them in a JSON block at the END of your response using exactly this format:
```json
{{
  "context_updates": {{"field_name": "value"}},
  "workflow_advance": false,
  "detected_conflicts": []
}}
```
- Only include the JSON block if there are meaningful updates. Keep it minimal."""

    # Build message list: history + current user message
    messages_for_llm = [m for m in chat_history[-10:] if m["role"] in ("user", "assistant")]
    messages_for_llm.append({"role": "user", "content": user_message})

    response_text = _call_gemini(messages_for_llm, system_prompt, max_tokens=1500)

    if response_text is None:
        response_text = _fallback_chat_response(user_message, event_context, workflow_state, retrieved_chunks)

    return _parse_chat_response(response_text, retrieved_chunks)


def extract_event_context_from_intake(user_message: str, current_context: Dict) -> Dict:
    """
    Extract structured event fields from a user's natural language message.
    Returns a dict of field updates to apply to the event context.
    """
    system_prompt = """Extract structured event planning information from the user message.
Return ONLY a valid JSON object containing only the fields explicitly mentioned or clearly implied.

Valid field names and types:
- event_type: string (e.g. "birthday party", "dinner party", "holiday gathering", "graduation party", "baby shower")
- event_date: string (YYYY-MM-DD if date given, else omit)
- event_time: string (HH:MM 24h format if time given, else omit)
- event_duration_hours: number
- guest_count_estimated: integer
- guest_count_confirmed: integer
- budget_total: number (dollar amount, no $ sign)
- venue_type: string ("home", "backyard", "rented hall", "outdoor", "restaurant")
- location: string
- theme: string
- dietary_restrictions: array of strings (e.g. ["vegetarian", "gluten-free"])
- accessibility_needs: array of strings
- has_children: boolean
- has_elderly: boolean
- entertainment_preferences: array of strings
- host_name: string
- special_notes: string

Return ONLY the JSON object. Omit fields not present in the message. No explanation."""

    messages = [{"role": "user", "content": user_message}]
    response = _call_gemini(messages, system_prompt, max_tokens=400)

    if response is None:
        return _fallback_context_extraction(user_message)

    try:
        # Strip markdown code fences if present
        clean = re.sub(r'```(?:json)?\s*', '', response).strip().strip('`').strip()
        # Find the first { ... } block
        match = re.search(r'\{.*\}', clean, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(clean)
    except Exception:
        return _fallback_context_extraction(user_message)


def generate_clarification_questions(event_context: Dict, detected_issues: List[str]) -> List[str]:
    """Generate 2–4 targeted clarification questions based on gaps in the event context."""
    system_prompt = """You are an event planning assistant identifying missing or ambiguous information.
Based on the event context and detected issues provided, generate 2–4 focused clarification questions.
Return ONLY a JSON array of question strings. Be direct and specific."""

    context_text = json.dumps({k: v for k, v in event_context.items() if v}, indent=2)
    issues_text = "\n".join(detected_issues) if detected_issues else "None"
    user_content = f"Event context:\n{context_text}\n\nIssues/gaps:\n{issues_text}"

    messages = [{"role": "user", "content": user_content}]
    response = _call_gemini(messages, system_prompt, max_tokens=300)

    if response is None:
        return _fallback_clarification_questions(event_context)

    try:
        clean = re.sub(r'```(?:json)?\s*', '', response).strip().strip('`').strip()
        match = re.search(r'\[.*\]', clean, re.DOTALL)
        if match:
            questions = json.loads(match.group())
            return questions if isinstance(questions, list) else []
        return json.loads(clean)
    except Exception:
        return _fallback_clarification_questions(event_context)


def detect_conflicts(event_context: Dict, retrieved_chunks: List[Dict]) -> List[str]:
    """
    Use Gemini + retrieved knowledge base to detect conflicts and planning risks.
    Returns a list of conflict strings, each specific and actionable.
    """
    rag_context = _build_rag_context(retrieved_chunks)
    system_prompt = f"""You are a household event planning expert analyzing a plan for conflicts and risks.
Compare the event context against the knowledge base guidelines below.

{rag_context}

Identify specific conflicts such as:
- Budget too low for guest count (compare to KB cost-per-person ranges)
- Timeline too tight for specific tasks (e.g., custom cake needs 2-week lead time)
- Missing critical planning elements (venue not specified, dietary needs not addressed)
- Guest experience risks (no children's activities when children are attending)

Return ONLY a JSON array of conflict strings. Each conflict must be specific with numbers.
Example: ["Budget of $150 for 25 guests is $6/person, below the $8-15/person minimum recommended range."]
If no conflicts, return []"""

    context_text = json.dumps({k: v for k, v in event_context.items() if v}, indent=2)
    messages = [{"role": "user", "content": f"Event context:\n{context_text}"}]
    response = _call_gemini(messages, system_prompt, max_tokens=500)

    if response is None:
        return _fallback_conflict_detection(event_context)

    try:
        clean = re.sub(r'```(?:json)?\s*', '', response).strip().strip('`').strip()
        match = re.search(r'\[.*\]', clean, re.DOTALL)
        if match:
            conflicts = json.loads(match.group())
            return conflicts if isinstance(conflicts, list) else []
        return json.loads(clean) if clean.startswith('[') else []
    except Exception:
        return _fallback_conflict_detection(event_context)


def generate_planning_response(
    event_context: Dict,
    retrieved_chunks: List[Dict],
    request: str = "Generate a comprehensive event plan",
) -> str:
    """Generate a detailed narrative planning response grounded in retrieved chunks."""
    rag_context = _build_rag_context(retrieved_chunks)
    context_summary = _summarize_context(event_context)

    system_prompt = f"""{SYSTEM_PROMPT_BASE}

CURRENT EVENT CONTEXT:
{context_summary}

{rag_context}

Generate a comprehensive, structured planning response. Requirements:
- Use specific quantities, costs, and timelines from the knowledge base sources
- Cite each recommendation with [Source: doc_id]
- Use markdown formatting (headers, bullet lists, bold key points)
- Cover: overview, key tasks, food/drinks, decorations, timeline, budget notes"""

    messages = [{"role": "user", "content": request}]
    response = _call_gemini(messages, system_prompt, max_tokens=2000)

    if response is None:
        return _fallback_planning_response(event_context, retrieved_chunks)

    return response


def generate_artifact_json(
    artifact_type: str,
    event_context: Dict,
    retrieved_chunks: List[Dict],
) -> Dict:
    """
    Generate one of three structured JSON artifacts using Gemini.
    Falls back to template generator if Gemini is unavailable.
    """
    rag_context = _build_rag_context(retrieved_chunks)
    context_summary = _summarize_context(event_context)
    schema = _get_artifact_schema(artifact_type)

    system_prompt = f"""{SYSTEM_PROMPT_BASE}

CURRENT EVENT CONTEXT:
{context_summary}

{rag_context}

Generate a complete {artifact_type} JSON artifact following this schema EXACTLY:
{json.dumps(schema, indent=2)}

Critical requirements:
- Every field must be populated based on the event context and knowledge base
- Use specific quantities and costs from the retrieved sources
- Include citations (list of doc_ids used)
- The artifact must reflect the actual event parameters, not generic templates
- Return ONLY the JSON object — no markdown fences, no explanation"""

    messages = [{"role": "user", "content": f"Generate {artifact_type} for this event."}]
    response = _call_gemini(messages, system_prompt, max_tokens=3000)

    if response is None:
        from artifact_generator import generate_fallback_artifact
        return generate_fallback_artifact(artifact_type, event_context)

    try:
        # Strip any markdown code fences
        clean = re.sub(r'```(?:json)?\s*', '', response).strip().strip('`').strip()
        match = re.search(r'\{.*\}', clean, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(clean)
    except Exception:
        from artifact_generator import generate_fallback_artifact
        return generate_fallback_artifact(artifact_type, event_context)


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_rag_context(chunks: List[Dict]) -> str:
    if not chunks:
        return "KNOWLEDGE BASE CONTEXT: No documents retrieved for this query."

    local_chunks = [c for c in chunks if c.get("source_type") != "web"]
    web_chunks = [c for c in chunks if c.get("source_type") == "web"]

    lines = ["KNOWLEDGE BASE CONTEXT (ground your response in these sources):"]
    for i, chunk in enumerate(local_chunks, 1):
        score_pct = int(chunk.get("relevance_score", 0) * 100)
        lines.append(
            f"\n[{i}. Source: {chunk.get('doc_title', 'Unknown')} | "
            f"doc_id: {chunk.get('doc_id', '?')} | similarity: {score_pct}%]"
        )
        lines.append(chunk.get("text", ""))

    if web_chunks:
        lines.append("\nWEB SEARCH RESULTS (live supplementary data — cite URL when referencing):")
        for i, chunk in enumerate(web_chunks, 1):
            url = chunk.get("url", "")
            lines.append(f"\n[Web {i}: {chunk.get('doc_title', 'Web Result')} | URL: {url}]")
            lines.append(chunk.get("text", ""))

    return "\n".join(lines)


def _summarize_context(ctx: Dict) -> str:
    parts = []
    mapping = {
        "event_type": "Event type",
        "event_date": "Date",
        "event_time": "Start time",
        "event_duration_hours": "Duration (hours)",
        "guest_count_confirmed": "Confirmed guests",
        "guest_count_estimated": "Estimated guests",
        "budget_total": "Total budget ($)",
        "budget_allocated": "Budget allocated ($)",
        "venue_type": "Venue",
        "location": "Location",
        "theme": "Theme",
        "dietary_restrictions": "Dietary restrictions",
        "accessibility_needs": "Accessibility needs",
        "has_children": "Children attending",
        "has_elderly": "Elderly guests",
        "entertainment_preferences": "Entertainment",
        "special_notes": "Special notes",
        "detected_conflicts": "Known conflicts",
    }
    for field, label in mapping.items():
        val = ctx.get(field)
        if val is not None and val != [] and val != "" and val is not False:
            if isinstance(val, list):
                val = ", ".join(str(v) for v in val)
            parts.append(f"- {label}: {val}")
    return "\n".join(parts) if parts else "No event details collected yet."


def _parse_chat_response(response_text: str, retrieved_chunks: List[Dict]) -> Dict:
    """Parse Gemini response, extracting embedded JSON metadata block if present."""
    context_updates = {}
    workflow_advance = False
    detected_conflicts = []

    # Look for trailing JSON block
    json_match = re.search(
        r'```json\s*(\{[^```]+\})\s*```|(\{[^{}]*"context_updates"[^{}]*\})',
        response_text,
        re.DOTALL,
    )
    if json_match:
        raw_json = json_match.group(1) or json_match.group(2)
        try:
            meta = json.loads(raw_json)
            context_updates = meta.get("context_updates", {})
            workflow_advance = meta.get("workflow_advance", False)
            detected_conflicts = meta.get("detected_conflicts", [])
            display_text = response_text[:json_match.start()].strip()
        except Exception:
            display_text = response_text
    else:
        display_text = response_text

    # Build citation list from retrieved chunks (local KB + web)
    citations = []
    seen = set()
    for chunk in retrieved_chunks:
        if chunk.get("doc_id") not in seen:
            seen.add(chunk["doc_id"])
            citations.append({
                "doc_id": chunk["doc_id"],
                "doc_title": chunk["doc_title"],
                "relevance_score": chunk.get("relevance_score", 0),
                "url": chunk.get("url", ""),
                "source_type": chunk.get("source_type", "kb"),
            })

    return {
        "response": display_text,
        "citations": citations,
        "context_updates": context_updates,
        "workflow_advance": workflow_advance,
        "detected_conflicts": detected_conflicts,
    }


def _get_artifact_schema(artifact_type: str) -> Dict:
    schemas = {
        "task_checklist": {
            "artifact_type": "task_checklist",
            "event_title": "string",
            "event_date": "string",
            "generated_at": "ISO datetime string",
            "total_tasks": "integer",
            "completed_tasks": 0,
            "citations": ["list of doc_id strings used"],
            "categories": [
                {
                    "name": "4+ Weeks Before",
                    "tasks": [
                        {
                            "task_id": "t1",
                            "title": "task title",
                            "description": "specific actionable description",
                            "owner": "Host",
                            "status": "pending",
                            "estimated_time": "e.g. 1 hour",
                            "priority": "high",
                        }
                    ],
                },
                {"name": "2–4 Weeks Before", "tasks": []},
                {"name": "1 Week Before", "tasks": []},
                {"name": "Day Before", "tasks": []},
                {"name": "Day Of", "tasks": []},
            ],
        },
        "shopping_list": {
            "artifact_type": "shopping_list",
            "event_title": "string",
            "event_date": "string",
            "generated_at": "ISO datetime string",
            "guest_count": "number",
            "budget_total": "number",
            "budget_allocated": "number",
            "budget_remaining": "number",
            "notes": "string (budget warnings, dietary notes)",
            "citations": ["list of doc_id strings used"],
            "categories": [
                {
                    "name": "Food",
                    "items": [
                        {
                            "item": "item name",
                            "quantity": "number",
                            "unit": "string (lbs, cans, packs, etc.)",
                            "estimated_cost": "number",
                            "notes": "optional tip or substitution",
                        }
                    ],
                    "subtotal": "number",
                },
                {"name": "Beverages", "items": [], "subtotal": 0},
                {"name": "Decorations", "items": [], "subtotal": 0},
                {"name": "Tableware & Supplies", "items": [], "subtotal": 0},
            ],
            "total_cost": "number",
        },
        "day_of_schedule": {
            "artifact_type": "day_of_schedule",
            "event_title": "string",
            "event_date": "string",
            "event_start_time": "HH:MM",
            "event_duration_hours": "number",
            "generated_at": "ISO datetime string",
            "citations": ["list of doc_id strings used"],
            "setup_blocks": [
                {
                    "block_id": "s1",
                    "start_time": "HH:MM",
                    "duration_minutes": "number",
                    "activity": "activity name",
                    "responsible": "Host",
                    "details": "what to do in detail",
                    "dependencies": [],
                }
            ],
            "event_blocks": [
                {
                    "block_id": "e1",
                    "start_time": "HH:MM",
                    "duration_minutes": "number",
                    "activity": "activity name",
                    "responsible": "Host",
                    "details": "description",
                    "dependencies": [],
                }
            ],
            "cleanup_blocks": [
                {
                    "block_id": "c1",
                    "start_time": "HH:MM",
                    "duration_minutes": "number",
                    "activity": "cleanup task",
                    "responsible": "Host + helpers",
                    "details": "cleanup instructions",
                    "dependencies": [],
                }
            ],
        },
    }
    return schemas.get(artifact_type, {})


# ─────────────────────────────────────────────────────────────────────────────
# Fallback responses (demo mode — no API key)
# ─────────────────────────────────────────────────────────────────────────────

def _fallback_chat_response(
    user_message: str,
    event_context: Dict,
    workflow_state: str,
    chunks: List[Dict],
) -> str:
    event_type = event_context.get("event_type", "your event")
    guests = event_context.get("guest_count_estimated") or event_context.get("guest_count_confirmed", "?")
    budget = event_context.get("budget_total")

    sources = list({c.get("doc_id", "") for c in chunks if c.get("doc_id")})
    citation_text = f"\n\n*[Sources: {', '.join(sources)}]*" if sources else ""

    if workflow_state == "intake":
        return (
            f"I'd love to help you plan {event_type}! To get started, I need:\n\n"
            "1. **Event type** (birthday party, dinner party, holiday gathering...)\n"
            "2. **Date** of the event\n"
            "3. **Guest count** (estimated)\n"
            "4. **Total budget** in dollars\n"
            "5. **Venue** (at home, rented hall, outdoor)\n\n"
            "You can also use the form on the left to fill in these details!\n\n"
            "> 🔔 *Demo mode — set `GOOGLE_API_KEY` in `.env` for full Gemini AI responses.*"
        )

    msg = user_message.lower()
    if any(w in msg for w in ["budget", "cost", "money", "price", "spend"]):
        resp = (
            f"Based on your budget of **${budget or 'TBD'}** for **{guests} guests**:\n\n"
            "**Recommended budget allocation:**\n"
            "- 🍽️ Food & Beverages: **40–50%**\n"
            "- 🎨 Decorations: **15–20%**\n"
            "- 🎵 Entertainment: **10–15%**\n"
            "- 🍽️ Tableware: **8–12%**\n"
            "- 🔒 Contingency: **10%**\n\n"
            "Always reserve 10% for unexpected costs!"
        )
    elif any(w in msg for w in ["food", "eat", "menu", "catering", "cook"]):
        resp = (
            f"For {guests} guests at a {event_type}, here's a food plan:\n\n"
            "- **Protein**: 6–8 oz per person (chicken, beef, or plant-based option)\n"
            "- **Salad**: 2–3 oz dressed greens per person\n"
            "- **Sides**: 2–3 dishes for variety\n"
            "- **Dessert**: 1.5 servings per person\n\n"
            "**Tip**: Make 70% of dishes ahead of time to reduce day-of stress."
        )
    elif any(w in msg for w in ["generate", "artifact", "checklist", "shopping", "schedule"]):
        resp = (
            "**Generating your planning documents!** Your complete plan includes:\n\n"
            f"✅ **Task Checklist** — prioritized across 5 time horizons\n"
            f"🛒 **Shopping List** — itemized for {guests} guests with cost estimates\n"
            f"📅 **Day-of Schedule** — time-blocked with setup, event, and cleanup\n\n"
            "Check the **Artifacts** tab to view and download your plan."
        )
    else:
        resp = (
            f"I'm planning your **{event_type}** for **{guests} guests**"
            f"{(' with a $' + str(budget) + ' budget') if budget else ''}.\n\n"
            "What would you like to focus on?\n"
            "- 📋 Task checklist\n- 🛒 Shopping list\n- 📅 Day-of schedule\n"
            "- 🍽️ Menu planning\n- 💰 Budget breakdown\n- 🎨 Decorations"
        )

    return resp + citation_text


def _fallback_context_extraction(user_message: str) -> Dict:
    """Simple regex-based extraction as fallback."""
    updates = {}
    msg = user_message.lower()

    for etype in [
        "birthday party", "dinner party", "holiday gathering", "graduation party",
        "baby shower", "anniversary", "retirement party", "bridal shower",
        "housewarming", "farewell party", "barbecue", "bbq",
    ]:
        if etype in msg:
            updates["event_type"] = etype
            break

    guest_match = re.search(r'(\d+)\s*(?:guests?|people|persons?|attendees?)', msg)
    if guest_match:
        updates["guest_count_estimated"] = int(guest_match.group(1))

    budget_match = re.search(r'\$\s*(\d+(?:\.\d{2})?)', msg)
    if budget_match:
        updates["budget_total"] = float(budget_match.group(1))

    for venue in ["home", "backyard", "outdoor", "rented hall", "restaurant", "park", "garden"]:
        if venue in msg:
            updates["venue_type"] = venue
            break

    restrictions = []
    for r in ["vegetarian", "vegan", "gluten-free", "nut allergy", "nut-free",
              "dairy-free", "kosher", "halal", "lactose"]:
        if r in msg:
            restrictions.append(r)
    if restrictions:
        updates["dietary_restrictions"] = restrictions

    if any(w in msg for w in ["kid", "child", "children", "toddler"]):
        updates["has_children"] = True
    if any(w in msg for w in ["elderly", "senior", "grandparent", "grandma", "grandpa"]):
        updates["has_elderly"] = True

    return updates


def _fallback_clarification_questions(event_context: Dict) -> List[str]:
    questions = []
    if not event_context.get("event_type"):
        questions.append("What type of event are you planning? (e.g., birthday party, dinner party, holiday gathering)")
    if not event_context.get("event_date"):
        questions.append("What date are you planning for the event?")
    if not event_context.get("guest_count_estimated") and not event_context.get("guest_count_confirmed"):
        questions.append("How many guests are you expecting?")
    if not event_context.get("budget_total"):
        questions.append("What is your total budget for this event?")
    if not event_context.get("venue_type"):
        questions.append("Will this be at home, a rented venue, or outdoors?")
    if not event_context.get("dietary_restrictions"):
        questions.append("Do any guests have dietary restrictions? (vegetarian, gluten-free, nut allergy, etc. — or 'none')")
    return questions[:4]


def _fallback_conflict_detection(event_context: Dict) -> List[str]:
    conflicts = []
    budget = event_context.get("budget_total")
    guests = event_context.get("guest_count_estimated") or event_context.get("guest_count_confirmed")

    if budget and guests:
        per_person = budget / guests
        if per_person < 8:
            conflicts.append(
                f"Budget of ${budget:.0f} for {guests} guests is ${per_person:.1f}/person — "
                "below the $8–15/person minimum for a budget-tier party (per knowledge base guidelines)."
            )
        elif per_person < 12:
            conflicts.append(
                f"Budget of ${budget:.0f} for {guests} guests is ${per_person:.1f}/person — "
                "tight but manageable. Consider a simplified menu or DIY decorations."
            )

    from datetime import date
    event_date_str = event_context.get("event_date")
    if event_date_str:
        try:
            event_dt = date.fromisoformat(event_date_str)
            days_until = (event_dt - date.today()).days
            if 0 < days_until < 7:
                conflicts.append(
                    f"Only {days_until} days until the event — "
                    "some tasks require immediate action: grocery shopping, cake order, and decoration setup."
                )
            elif 7 <= days_until < 14:
                conflicts.append(
                    f"{days_until} days until the event — "
                    "if you need a custom bakery cake, order it now (requires 1-2 week lead time)."
                )
        except ValueError:
            pass

    if event_context.get("dietary_restrictions") and not event_context.get("shopping_list"):
        restrictions = event_context["dietary_restrictions"]
        if "nut allergy" in restrictions or "nut-free" in restrictions:
            conflicts.append(
                "Nut allergy guests require a fully nut-free menu and separate serving utensils. "
                "Check ALL ingredient labels including sauces, dressings, and desserts."
            )

    return conflicts


def _fallback_planning_response(event_context: Dict, chunks: List[Dict]) -> str:
    event_type = event_context.get("event_type", "event")
    guests = event_context.get("guest_count_estimated") or event_context.get("guest_count_confirmed", 20)
    budget = event_context.get("budget_total", 250)
    venue = event_context.get("venue_type", "home")

    sources = list({c.get("doc_id", "") for c in chunks if c.get("doc_id")})

    return (
        f"## Planning Overview: {event_type.title()}\n\n"
        f"**{guests} guests · ${budget:.0f} budget · {venue}**\n\n"
        "### Key Recommendations\n\n"
        f"**Budget allocation** (${budget:.0f} total):\n"
        f"- Food & Beverages: ~${budget * 0.45:.0f} (45%)\n"
        f"- Decorations: ~${budget * 0.18:.0f} (18%)\n"
        f"- Entertainment: ~${budget * 0.12:.0f} (12%)\n"
        f"- Tableware: ~${budget * 0.10:.0f} (10%)\n"
        f"- Contingency: ~${budget * 0.10:.0f} (10%)\n\n"
        f"**Food planning** (for {guests} guests):\n"
        f"- Protein: {max(3, guests // 4)} lbs\n"
        f"- Sides: 2–3 dishes\n"
        f"- Cake/dessert: serves {guests}\n\n"
        "Type **'generate artifacts'** to get your complete checklist, shopping list, and schedule.\n\n"
        + (f"*[Sources: {', '.join(sources)}]*" if sources else "")
    )
