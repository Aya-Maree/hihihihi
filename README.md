# Household Event Planner — EventOps AI Application
**SE4471B Course Project | Group 2**

Sara Daher · Aya Maree · Shahed Bitar

---

## Overview

An AI-powered household event planning system that transforms unstructured event requirements into structured, actionable planning artifacts. Built with:

- **Frontend**: React + Vite + Tailwind CSS (chat interface, artifact viewer, workflow progress)
- **Backend**: Python FastAPI
- **RAG**: JSON knowledge base (12 documents) + TF-IDF cosine similarity retrieval (no external vector DB)
- **LLM**: Anthropic Claude API (fallback to template-based responses in demo mode)
- **Memory**: In-memory session state with event context tracking across turns
- **Workflow**: 7-step agentic planning logic (Intake → Clarification → Retrieval → Conflict Detection → Planning → Validation → Artifact Generation)
- **External API (Tier 2)**: Spoonacular Food API for recipe-based ingredient enrichment

---

## System Architecture

```
[React Frontend (Vite + Tailwind)]
    ↓  (REST API)
[FastAPI Backend (Python)]
    ↓
[Session Manager (Memory)]  ←→  [Event Context JSON]
    ↓
[Planning Workflow (7-step)]
    ↓
[RAG Pipeline]
    ├── [Knowledge Base: 12 JSON docs]
    └── [TF-IDF Retriever + Cosine Similarity]
    ↓
[LLM Service (Claude / Demo fallback)]
    ↓
[Artifact Generator]
    ├── Task Checklist (JSON + Markdown)
    ├── Shopping List (JSON + Markdown)
    └── Day-of Schedule (JSON + Markdown)
    ↓
[Spoonacular API (Tier 2 enrichment)]
```

---

## Setup Instructions

### Prerequisites
- Python 3.9+ 
- Node.js 18+ and npm

### 1. Clone and set up the repository

```bash
git clone <repo-url>
cd project-phase-1-group-2-1
```

### 2. Backend Setup

```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Copy and configure environment variables
copy .env.example .env
```

Edit `.env` and add your API keys:
```
ANTHROPIC_API_KEY=your_claude_api_key_here
SPOONACULAR_API_KEY=your_spoonacular_key_here  # optional for Tier 2
```

> **Note**: The system works in **demo mode** without API keys — you'll get template-based responses. For full AI capabilities, add your Anthropic API key.

**Start the backend:**
```bash
python main.py
# OR
uvicorn main:app --reload --port 8000
```

The backend runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The frontend runs at `http://localhost:5173`.

---

## Usage

1. **Open** `http://localhost:5173` in your browser
2. **Start** on the Dashboard and click "Start Planning"
3. **Fill in** the event form (type, date, guests, budget, venue) OR chat directly
4. **Follow** the 7-step workflow guided by the AI
5. **Generate** your complete planning documents (Task Checklist, Shopping List, Day-of Schedule)
6. **Download** artifacts as JSON or view as formatted Markdown

### Example Interaction

```
You: "I'm planning a birthday party for 25 guests on April 20th. 
      Budget is $300, at home. We have 2 vegetarian guests and some children."

AI: [Retrieves birthday_party_guide, dietary_guidelines, shopping_list_templates]
    "I've found some potential conflicts: your budget of $300 for 25 guests is 
     $12/person which is on the budget-tier range. Consider simplifying the menu..."

You: "I'll increase the budget to $350 and focus on simple food"

AI: [Detects no remaining conflicts, moves to planning]
    "Great! Here's your comprehensive plan... [cites sources]"

You: "generate artifacts"

AI: "Your complete plan is ready! 
     - Task Checklist: 20 tasks across 5 time horizons
     - Shopping List: 28 items, estimated $285.50
     - Day-of Schedule: 9 time blocks"
```

---

## Core System Components

### 1. RAG Pipeline (`backend/rag_pipeline.py`)

- **Document Store**: Loads 12 JSON files from `backend/knowledge_base/`
- **Retriever**: TF-IDF vectorization + cosine similarity (pure Python + scikit-learn, no external vector DB)
- **Context Enrichment**: Query is enriched with event context (event type, guest count, dietary restrictions)
- **Citations**: Every response cites the source documents used

**Knowledge Base Documents (12 files):**
1. `birthday_party_guide.json` — Step-by-step birthday planning
2. `dinner_party_guide.json` — Dinner party hosting
3. `holiday_gathering_guide.json` — Holiday event planning
4. `budget_planning_guide.json` — Budget allocation and savings
5. `shopping_list_templates.json` — Quantity templates by guest count
6. `dietary_guidelines.json` — Dietary restrictions and accommodations
7. `accessibility_guide.json` — Accessibility considerations
8. `day_of_schedule_samples.json` — Day-of timeline templates
9. `vendor_decoration_ideas.json` — Vendors and DIY decorations
10. `rsvp_guest_management.json` — RSVP and guest tracking
11. `catering_guidelines.json` — Food quantities and catering
12. `entertainment_ideas.json` — Entertainment options and costs
13. `milestone_celebration_guide.json` — Graduation, baby showers, anniversaries

### 2. Multi-Step Workflow (`backend/workflow.py`)

The system follows 7 conditional steps:

| Step | What Happens |
|------|-------------|
| **1. Intake** | Collect event parameters (type, date, guests, budget, venue) |
| **2. Clarification** | Identify missing/ambiguous info, ask targeted questions |
| **3. Retrieval** | Build query from context, fetch top-k knowledge base chunks |
| **4. Conflict Detection** | Use LLM + KB to detect budget/timeline/dietary conflicts |
| **5. Planning** | Generate comprehensive narrative plan with citations |
| **6. Validation** | Allow adjustments, answer questions, check constraints |
| **7. Artifact Generation** | Generate all 3 structured artifacts |

**Conditional logic examples:**
- If budget < $8/person → flag conflict before planning
- If event date < 7 days away → warn about tight timeline
- If dietary restrictions present → retrieve dietary_guidelines.json
- If children attending → include children's activities in planning

### 3. Memory (`backend/memory.py`)

**EventContext** object tracks:
```json
{
  "event_type": "birthday party",
  "event_date": "2025-04-20",
  "guest_count_estimated": 25,
  "budget_total": 300.00,
  "budget_allocated": 285.50,
  "venue_type": "home",
  "dietary_restrictions": ["vegetarian"],
  "has_children": true,
  "detected_conflicts": [],
  "pending_tasks": [...],
  "shopping_list": [...],
  "schedule_blocks": [...]
}
```

**ChatHistory** stores full conversation with timestamps and citations.
**Session** persists across all workflow steps and multiple turns.

### 4. Structured Artifacts

**Task Checklist** — 5 time horizons, each with:
- Task title + description, owner, estimated time, priority, status

**Shopping List** — 4 categories with:
- Item name, quantity, unit, estimated cost, notes
- Budget tracking (total vs. allocated vs. remaining)

**Day-of Schedule** — 3 sections with:
- Time blocks with start time, duration, activity, responsible party, dependencies

All artifacts output as **JSON** (machine-readable) + **Markdown** (human-readable).

### 5. Spoonacular Integration (Tier 2)

When `SPOONACULAR_API_KEY` is configured:
- Search for event-appropriate recipes
- Get scaled ingredient lists for the confirmed guest count
- Enrich the shopping list with real recipe data
- Suggest ingredient substitutions for dietary restrictions

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/session/create` | Create planning session |
| GET | `/api/session/{id}` | Get full session state |
| GET | `/api/session/{id}/context` | Get event context |
| POST | `/api/chat` | Send message (main chat + RAG) |
| POST | `/api/plan/start` | Start workflow with form data |
| POST | `/api/artifacts/generate` | Generate all 3 artifacts |
| GET | `/api/artifacts/{id}` | Get artifacts |
| GET | `/api/artifacts/{id}/download` | Download JSON package |
| GET | `/api/artifacts/{id}/{type}/markdown` | Get Markdown rendering |
| GET | `/api/rag/documents` | List knowledge base |
| POST | `/api/rag/retrieve` | Test retrieval manually |
| GET | `/api/spoonacular/recipes` | Search recipes (Tier 2) |

Full interactive API docs: `http://localhost:8000/docs`

---

## Target Implementation Tier

**Tier 2 (Tool-Enabled System)** — Includes:
- ✅ Tier 1: Working RAG pipeline, multi-step workflow, context tracking, structured artifacts
- ✅ External API: Spoonacular Food API for recipe-based ingredient enrichment
- ✅ React frontend (beyond Streamlit)

---

## Reliability and Testing

See `docs/Assignment2_Summary.md` for testing strategy and failure cases.

Key testing scenarios:
- Budget conflict detection (low budget for high guest count)
- Dietary restriction handling (vegan, gluten-free, nut allergy)
- Timeline pressure (events < 7 days away)
- Multi-turn context persistence
- RAG retrieval quality for different query types
- Fallback behavior without API key (demo mode)
