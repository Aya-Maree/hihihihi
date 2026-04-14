# EventOps AI — Reliability and Evaluation Report
**SE4471B Course Project | Assignment 3**  
Sara Daher · Aya Maree  
April 2026

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Testing Strategy](#2-testing-strategy)
3. [Failure Cases and Limitations](#3-failure-cases-and-limitations)
4. [Prompt and Workflow Design Decisions](#4-prompt-and-workflow-design-decisions)
5. [Evidence of Retrieval Grounding](#5-evidence-of-retrieval-grounding)

---

## 1. System Overview

EventOps AI is a conversational AI event planning system that transforms unstructured natural-language event requirements into a complete, conflict-checked planning package. The final system achieves **Tier 2** (Tool-Enabled System), incorporating:

- A semantic RAG pipeline (sentence-transformers + ChromaDB) over a 23-document knowledge base
- A 7-step agentic planning workflow with conditional logic
- In-memory session state (`EventContext`, `ChatHistory`, `PlanningSession`)
- Google Gemini 2.0 Flash as the LLM, with a comprehensive template-based fallback
- Spoonacular Food API integration for recipe-based shopping list enrichment
- A React + Vite + Tailwind CSS frontend with live workflow progress tracking

---

## 2. Testing Strategy

### 2.1 Manual End-to-End Testing

The primary testing approach was **scenario-based end-to-end testing** — running complete planning workflows and verifying the system's behavior at each step. The following scenarios were tested:

| Scenario | Expected Behavior | Outcome |
|----------|------------------|---------|
| Complete intake in one message | System extracts all 5 fields, skips to retrieval | ✅ Pass |
| Intake across multiple turns | Context accumulates incrementally across messages | ✅ Pass |
| Budget conflict: < $8/person | Conflict detection fires, halts planning, asks for resolution | ✅ Pass |
| Tight timeline: event < 7 days away | Timeline conflict flagged with specific actionable warning | ✅ Pass |
| Vegetarian + gluten-free guests | `dietary_restrictions` extracted, retrieves `dietary_guidelines.json` | ✅ Pass |
| Children attending | `has_children = true`, retrieves entertainment/activities content | ✅ Pass |
| Artifact generation | All 3 artifacts produced (checklist, shopping list, schedule) | ✅ Pass |
| Recipe suggestions (Spoonacular on) | Shopping list enriched with real recipe ingredients | ✅ Pass |
| Recipe suggestions (Spoonacular off) | Fallback recipes with `fallback_ingredients` used instead | ✅ Pass |
| Post-artifact adjustments | User can modify context and regenerate after plan is complete | ✅ Pass |

### 2.2 Context Extraction Testing

Context extraction was tested by providing information in various natural-language phrasings to verify that the extraction regex and Gemini-based parsing handled them correctly:

| Input Phrase | Field Tested | Extracted Correctly |
|-------------|-------------|-------------------|
| "20 guests" | `guest_count_estimated` | ✅ |
| "guests to 15" | `guest_count_estimated` | ✅ (after regex fix) |
| "$300" | `budget_total` | ✅ |
| "budget to 400" | `budget_total` | ✅ (after regex fix) |
| "2026-04-25" | `event_date` (ISO) | ✅ |
| "April 25" | `event_date` (written) | ✅ (after date parser added) |
| "at home" | `venue_type` | ✅ |
| "birthday party" | `event_type` | ✅ |
| "2 vegetarians" | `dietary_restrictions` | ✅ |

### 2.3 RAG Retrieval Quality Testing

Retrieval was tested by issuing queries and verifying that semantically relevant documents ranked highest. Sample results:

| Query | Top Retrieved Document | Relevance Score |
|-------|----------------------|----------------|
| "birthday party planning" | `birthday_party_guide.json` | 0.81 |
| "dietary vegetarian gluten-free" | `dietary_guidelines.json` | 0.78 |
| "shopping 20 guests food quantities" | `shopping_list_templates.json` | 0.75 |
| "day of schedule timeline setup" | `day_of_schedule_samples.json` | 0.77 |
| "children entertainment activities" | `entertainment_ideas.json` | 0.72 |
| "outdoor venue accessibility" | `accessibility_guide.json` | 0.68 |

### 2.4 Fallback Mode Testing (Demo Mode)

The system was deliberately tested without a valid `GOOGLE_API_KEY` to verify that:
- Template-based responses are coherent and collect missing fields correctly
- Context extraction using regex (not LLM) correctly parses all required fields
- The workflow still advances through all 7 steps to artifact generation
- Artifacts are generated using `artifact_generator.py` templates

Fallback mode produces a functional — though less nuanced — planning experience, which is by design.

### 2.5 API Failure Testing

| Failure Injected | System Behavior |
|-----------------|----------------|
| No `GOOGLE_API_KEY` | Falls back to template responses; workflow still completes |
| Invalid/expired Gemini key (404) | Falls back to template responses |
| Gemini quota exceeded (429) | Falls back to template responses |
| No `SPOONACULAR_API_KEY` | Uses `_fallback_recipes` with pre-defined ingredient lists |
| Spoonacular search returns 0 results | Uses fallback; randomized subset prevents repetition |
| Backend restart mid-session | Session lost (in-memory); user must start a new session |

---

## 3. Failure Cases and Limitations

### 3.1 Known Failure Cases

#### F1 — Session Loss on Backend Restart
**Description**: All session data (event context, chat history, workflow state, artifacts) is stored in Python process memory. If the backend server restarts or crashes, all active sessions are lost.  
**Impact**: Users must start a new planning session from scratch.  
**Mitigation**: The `PlanningSession.to_dict()` and `from_dict()` serialization methods exist and the `SessionManager` accepts an optional `persist_dir`, but file-based persistence was not activated in this implementation.  
**Recommendation**: Enable the `persist_dir` option in `SessionManager` to write sessions to disk as JSON files.

#### F2 — Context Extraction Failures in Complex Phrasing
**Description**: The fallback regex-based context extractor (`_fallback_context_extraction` in `llm_service.py`) handles common phrasings but can miss unusual constructions (e.g., "we'll have roughly two dozen people" for guest count, or implied budgets like "my budget is tight, maybe two fifty").  
**Impact**: In demo/fallback mode, the user may be asked to re-enter information they already provided.  
**Mitigation**: When Gemini is available, the LLM handles these gracefully. The regex patterns were iteratively expanded to cover the most common phrasings encountered in testing.

#### F3 — Conflict Detection Loops
**Description**: If a detected conflict cannot be resolved (e.g., a date that is already past), the system can get stuck asking the user to resolve it repeatedly.  
**Impact**: The planning workflow stalls at the `clarification` step.  
**Mitigation**: A bypass was added — if `ctx.detected_conflicts` is already set when the user sends a message, the system routes directly to `planning` and clears the conflict list, allowing the workflow to proceed even if the user simply acknowledges rather than resolves the issue.

#### F4 — Spoonacular API Zero-Result Queries
**Description**: Overly specific search queries (e.g., "birthday party vegetarian finger food appetizers for 20 guests") frequently returned 0 results from the Spoonacular API.  
**Impact**: The enrichment step silently fails, and the shopping list contains no recipe suggestions.  
**Mitigation**: Search queries were simplified to core food terms (e.g., "birthday cake dessert"), random offsets were added to increase variety across calls, and `_fallback_recipes` with complete ingredient lists ensures recipe suggestions always appear.

#### F5 — Artifact Overgeneration / Undergeneration
**Description**: The LLM may occasionally produce JSON artifacts that are valid but either minimal (too few tasks/items) or excessively verbose depending on how the context is described.  
**Impact**: Artifacts may not reflect the full scope of the event if context is sparse.  
**Mitigation**: `artifact_generator.py` provides template-based fallback artifacts calibrated to the event type, guest count, and budget to ensure a reasonable baseline output.

#### F6 — No Cross-Session Knowledge
**Description**: Each planning session is completely isolated. The system has no memory of previous users, previous events, or commonly requested event types.  
**Impact**: No personalization or learning from past sessions.  
**Mitigation**: By design for this implementation. Could be addressed with a user account system and persistent session logs.

### 3.2 System Limitations

| Limitation | Notes |
|-----------|-------|
| **In-memory only** | Sessions lost on server restart |
| **Single concurrent user per session** | Sessions are isolated; no collaborative planning |
| **No real-time conflict checking** | Conflicts are only checked at the `conflict_detection` workflow step, not on every update |
| **No calendar integration** | Dates are tracked as strings; no iCal, Google Calendar, or reminder integration |
| **Gemini rate limits** | Free tier limits at ~1,500 requests/day; heavy use triggers 429 errors and fallback mode |
| **English only** | Context extraction regex and prompts are English-specific |
| **Knowledge base is static** | Documents are authored at build time; no live web content (except optional web search) |

---

## 4. Prompt and Workflow Design Decisions

### 4.1 System Prompt Design

The base system prompt (`SYSTEM_PROMPT_BASE` in `llm_service.py`) was designed around four constraints:

**1. Force grounding in the knowledge base**  
> *"Base ALL recommendations on the provided knowledge base context"*  
> *"Never fabricate costs or quantities — use the retrieved documents as your reference"*

This was the single most important constraint. Without it, Gemini tends to produce confident but hallucinated numbers (e.g., "$8/person for a 3-course dinner") that contradict the knowledge base.

**2. Explicit citation requirement**  
> *"Cite your sources explicitly using the format [Source: document_name]"*

Citations serve two purposes: they make the system's reasoning auditable, and they provide the frontend with structured metadata to display alongside responses.

**3. Conflict detection as a first-class responsibility**  
> *"Detect and flag conflicts (e.g., budget too low for guest count, timeline too tight)"*

By framing conflict detection as a core behavior rather than an optional feature, the LLM surfaces budget/timeline/dietary conflicts consistently without needing a separate prompt for each scenario.

**4. Context injection at every call**  
Each LLM call includes the current `EventContext` as a JSON summary and the current workflow state. This means the LLM always has the full planning state, not just the current message. This is essential for multi-turn coherence — without it, the LLM "forgets" previously collected information.

### 4.2 Workflow State Machine Design

The 7-step workflow was designed as a **conditional state machine** rather than a fixed linear sequence. Key design decisions:

#### Why Not a Simple Chain-of-Thought?
A simple prompt asking "plan this event" produces a single response with no mechanism to handle missing information, detect conflicts before generating artifacts, or update the plan when the user changes their mind. The state machine ensures each concern is handled in the correct order.

#### Intake → Auto-Advance
When all 5 required fields are collected (event type, date, guest count, budget, venue), the system automatically advances to the next step without requiring the user to explicitly ask. This avoids friction and keeps the conversation flowing naturally.

#### RAG in Intake (not just Retrieval)
A common design would only retrieve KB documents at the dedicated "retrieval" step. Instead, this system retrieves relevant chunks even during intake so that early responses (before all parameters are known) are still grounded. For example, if a user says "birthday party" but hasn't given a budget yet, the system can still reference `birthday_party_guide.json` for helpful framing.

#### Conflict Detection Gate
Artifacts cannot be generated until conflicts are resolved (or the user overrides). This was a deliberate guardrail — generating a shopping list for a $5/person budget without flagging the issue would produce a plan the user cannot realistically execute. The gate forces the LLM to surface issues before committing to a plan.

#### Validation Step as a Free-Chat Zone
Between planning and artifact generation, the `validation` step allows open-ended questions, adjustments, and refinements. It triggers a fresh RAG retrieval for whatever the user asks (plus optional web search), so answers remain grounded even in this open-ended phase.

#### Adjustment Keyword Detection
In validation, the system checks for adjustment-intent keywords before deciding whether to return a free-form chat response or re-run the full planning pipeline. This handles the case where a user says "change the budget to $500" — the system detects the intent, updates `EventContext`, re-retrieves, and re-generates the planning response rather than just acknowledging the change in chat.

Keywords detected:
```python
["adjust", "change", "update", "modify", "set", "reduce", "increase",
 "lower", "raise", "bump", "fewer", "more guests", "less guests"]
```

### 4.3 Context Accumulation Design

The `EventContext` object was designed to accumulate across turns rather than reset. Every user message is processed through `extract_event_context_from_intake()` before routing to the workflow step handler. This means:

- A user who says "birthday party" in turn 1, "20 guests" in turn 2, and "$300" in turn 3 gets the same result as a user who says everything in turn 1.
- The `is_complete_for_planning()` check runs after every context update, so the workflow advances as soon as enough data is collected regardless of which turn it arrives.

The `get_summary()` method on `EventContext` serializes the current state into a compact string that is injected into every LLM call, ensuring the model always has the full planning context even when only the last few messages of history are passed.

### 4.4 Fallback Design Philosophy

The fallback (demo mode) was not treated as a degraded experience but as a distinct, functional mode. Key decisions:

- **Dynamic responses**: The fallback response for intake acknowledges already-collected fields and lists only the remaining missing ones — rather than repeating the same boilerplate regardless of how much information was already provided.
- **Regex breadth**: Multiple regex patterns cover the most common phrasings for each field, including edge cases found during testing (e.g., "guests to 15", "budget of 300", "April 25th").
- **Template artifacts**: `artifact_generator.py` generates structured artifacts calibrated to the event context (type, guest count, budget) so the fallback produces a meaningful — not empty — planning document.

---

## 5. Evidence of Retrieval Grounding

### 5.1 How Retrieval Grounding Works

At every workflow step where the LLM generates a response, the system first retrieves 4–8 semantically relevant chunks from the knowledge base using the sentence-transformers model (`all-MiniLM-L6-v2`) and ChromaDB vector store. These chunks are formatted into a structured context block and injected into the LLM prompt before the user message:

```
=== RETRIEVED KNOWLEDGE BASE CONTEXT ===

[Source 1: Birthday Party Planning Guide | doc_id: birthday_party_guide | similarity: 81%]
<chunk text>

[Source 2: Event Budget Planning Guide | doc_id: budget_planning_guide | similarity: 74%]
<chunk text>

[Source 3: Shopping List Templates | doc_id: shopping_list_templates | similarity: 72%]
<chunk text>
...
=== END OF RETRIEVED CONTEXT ===
```

The system prompt explicitly instructs the LLM: *"Base ALL recommendations on the provided knowledge base context"* and *"Never fabricate costs or quantities — use the retrieved documents as your reference."*

### 5.2 Query Enrichment for Better Grounding

The retrieval query is enriched with the current event context before being embedded, improving relevance:

```python
enriched_query = f"{query} {event_type} {venue_type} dietary {restrictions} {guest_count} guests"
```

For example, a query of "shopping list" for a vegetarian birthday party with 20 guests becomes:
```
shopping list birthday party home dietary vegetarian 20 guests
```
This yields higher relevance scores for `shopping_list_templates.json` and `dietary_guidelines.json` than the bare query would.

### 5.3 Citations in Responses

Every response carries a `citations` array that is displayed in the UI alongside the AI message. This makes retrieval grounding visible to the user — not just an internal mechanism. During testing, citations consistently matched the query context:

**Example — Birthday Party (20 guests, $300, vegetarian):**

| Workflow Step | Documents Retrieved |
|--------------|-------------------|
| Intake | Birthday Party Planning Guide, Event Budget Planning Guide |
| Retrieval | Birthday Party Planning Guide, Shopping List Templates, Dietary Guidelines, Budget Planning Guide, Day-of Schedule Samples |
| Conflict Detection | Event Budget Planning Guide (flagged: $15/person is low for sit-down meal) |
| Planning | Birthday Party Planning Guide, Catering Guidelines, Vendor & Decoration Ideas |
| Artifact Generation | Shopping List Templates, Day-of Schedule Samples, Catering Guidelines |

### 5.4 Conflict Detection Grounded in KB

Conflict detection is not rule-based — it uses the LLM with retrieved KB context. The system passes the current `EventContext` and retrieved chunks to `detect_conflicts()`, and the LLM is asked to identify issues against knowledge-base guidelines. This means conflicts like:

- *"Your budget of $300 for 20 guests is $15/person. The knowledge base recommends $20–35/person for a home birthday party with a sit-down meal."*
- *"The event is 12 days away. Custom bakery cakes typically require 1–2 weeks lead time."*

...are sourced from the knowledge base, not from hardcoded thresholds. The system adapts to different event types because the retrieved chunks differ — what constitutes a budget conflict for a formal dinner party differs from a casual birthday party.

### 5.5 Spoonacular as a Second-Layer Grounding Source

For shopping list enrichment, the Spoonacular Food API provides a second grounding layer beyond the static knowledge base:

1. The system identifies the event type from `EventContext`
2. A targeted recipe search query is constructed (e.g., "birthday cake dessert", "pasta dinner party")
3. Spoonacular returns real recipe data including per-serving ingredient quantities scaled to the guest count
4. These ingredients are merged into the shopping list with estimated costs

This grounds the shopping list in real recipe data rather than generic food categories, and the ingredient quantities are numerically scaled to the specific guest count (e.g., 1.5 cups of flour × 20 servings).

### 5.6 Sample Retrieved Content Driving a Planning Response

For a birthday party with 20 guests, $300 budget, vegetarian guests, planning retrieved the following from `dietary_guidelines.json`:

> *"For vegetarian guests, ensure at least 30% of food options are vegetarian-friendly. Label all items clearly at the buffet. Consider vegetarian protein sources: hummus, cheese platters, stuffed mushrooms, vegetarian pasta."*

The resulting planning response included: *"Since you have vegetarian guests, the knowledge base recommends dedicating at least 30% of your food options to vegetarian choices — hummus and veggie platters, stuffed mushrooms, and vegetarian pasta work well for 20 guests at this budget [Source: Dietary Guidelines]."*

This demonstrates the chain from retrieval → context injection → grounded generation → cited response.

---

## Appendix — System Architecture Summary

```
User Message
    ↓
extract_event_context_from_intake()     ← Gemini JSON extraction + regex fallback
    ↓
EventContext updated
    ↓
Route to workflow step handler
    ↓
RAG retrieve (sentence-transformers + ChromaDB)
    enriched_query = user_message + event context fields
    top-k = 4 to 8 chunks
    ↓
_build_rag_context() → context string for LLM prompt
    ↓
chat_with_context() → Gemini API call (or fallback)
    system_prompt: SYSTEM_PROMPT_BASE + event context + RAG context
    messages: last 6–10 turns of chat history
    ↓
Response + citations returned to frontend
    ↓
(At artifact_generation step):
generate_artifact_json() × 3 → Task Checklist, Shopping List, Day-of Schedule
    ↓
(If Spoonacular enabled):
enrich_shopping_list() → recipe search → ingredient scaling → merged shopping list
```

---

*Report prepared for SE4471B Course Project, Assignment 3.*  
*Group 2 — Sara Daher · Aya Maree*
