# EventOps AI — Household Event Planner
**SE4471B Course Project | Group 2**  
Sara Daher · Aya Maree

---

## What it does

EventOps AI is a conversational AI system that turns a plain-English description of an event into a complete, conflict-checked planning package — in about 2 minutes.

You describe your event in chat ("Birthday party, 25 guests, April 25, $300, at home"), and the system:
1. Extracts all event parameters automatically
2. Retrieves relevant planning knowledge from a 23-document knowledge base
3. Detects conflicts (tight budget, short timeline, dietary issues) before generating any plan
4. Produces a **Task Checklist**, **Shopping List**, and **Day-of Schedule** — downloadable as PDF

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite + Tailwind CSS |
| Backend | Python FastAPI |
| LLM | Google Gemini 2.0 Flash |
| RAG | sentence-transformers (all-MiniLM-L6-v2) + ChromaDB |
| Knowledge Base | 23 curated JSON documents |
| External API | Spoonacular Food API (Tier 2) |
| Session Memory | In-memory EventContext + ChatHistory |

---

## Prerequisites

Before you start, make sure you have:

- **Python 3.9 or higher** — check with `python3 --version`
- **Node.js 18 or higher** — check with `node --version`
- **npm** — check with `npm --version`
- A **Google Gemini API key** (free) — get one at https://aistudio.google.com/app/apikey
- *(Optional)* A **Spoonacular API key** (free) — get one at https://spoonacular.com/food-api

---

## Setup — Step by Step

### Step 1: Get the code

```bash
git clone <repo-url>
cd project-phase-1-group-2-1
```

---

### Step 2: Backend setup

```bash
cd backend
```

**Create and activate a virtual environment:**

```bash
# Create venv
python3 -m venv venv

# Activate it — Mac/Linux:
source venv/bin/activate

# Activate it — Windows:
venv\Scripts\activate
```

**Install dependencies:**

```bash
pip install -r requirements.txt
```

> ⚠️ This will download `sentence-transformers` and other ML packages — it may take 2–3 minutes the first time.

**Configure your API keys:**

```bash
# Mac/Linux:
cp .env.example .env

# Windows:
copy .env.example .env
```

Open `.env` and fill in your keys:

```env
# Required — get a free key at https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=your_gemini_api_key_here

# Which Gemini model to use (this one is free)
GEMINI_MODEL=gemini-2.0-flash

# Optional — enables real recipe suggestions in shopping list
SPOONACULAR_API_KEY=your_spoonacular_key_here
```

> **No API key?** The app still works in demo mode — you'll get template-based responses instead of full AI. Everything else (RAG, workflow, artifacts) still functions.

**Start the backend:**

```bash
# First run — downloads the embedding model from HuggingFace (~90MB):
python main.py

# All subsequent runs — use offline mode (faster, no network needed for the model):
TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 python main.py
```

You should see:
```
✅ RAG Pipeline ready: 23 documents, 164 chunks
✅ Gemini API: Configured
✅ Spoonacular: Configured
INFO: Uvicorn running on http://0.0.0.0:8000
```

The backend runs at **http://localhost:8000**  
Interactive API docs at **http://localhost:8000/docs**

---

### Step 3: Frontend setup

Open a **new terminal** (keep the backend running), then:

```bash
cd frontend
npm install
npm run dev
```

You should see:
```
VITE v5.x  ready in 300ms
➜  Local: http://localhost:5173/
```

---

### Step 4: Open the app

Go to **http://localhost:5173** in your browser.

---

## How to Use

1. **Click "Start Planning"** on the dashboard
2. **Describe your event** in the chat — e.g.:
   > *"Birthday party, 20 guests, April 25 2026, $300 budget, at home. 2 vegetarians."*
3. **Answer any follow-up questions** the AI asks (dietary restrictions, allergies, etc.)
4. **Resolve any conflicts** the system flags (e.g. tight budget) before it generates the plan
5. **Check "Include recipe suggestions"** if you want Spoonacular recipe data in your shopping list
6. **Click "Get My Full Plan"** to generate your 3 planning documents
7. **View, print, or download** your Task Checklist, Shopping List, and Day-of Schedule

> **Tip:** You can give the AI everything in one message — event type, date, guest count, budget, venue, and dietary restrictions all at once.

---

## Example Conversation

```
You:  "Birthday party, 25 guests, April 25 2026, $300, at home. 2 vegetarians and some kids."

AI:   Got it! Here's what I have: Birthday Party · 25 guests · April 25 2026 · $300 · home · vegetarian
      ⚠️ Conflict: $300 for 25 guests is $12/person — tight. Increase budget or simplify menu?

You:  "Increase budget to $350, keep food simple."

AI:   ✅ Plan ready!
      📋 Task Checklist: 20 tasks across 5 time horizons
      🛒 Shopping List: 28 items, estimated $285.50
      📅 Day-of Schedule: 9 time blocks
```

## Project Structure

```
hihihihi/
├── backend/
│   ├── main.py               # FastAPI app + all endpoints
│   ├── workflow.py           # 7-step agentic planning logic
│   ├── rag_pipeline.py       # sentence-transformers + ChromaDB RAG
│   ├── llm_service.py        # Gemini API integration + fallback
│   ├── memory.py             # EventContext + ChatHistory + SessionManager
│   ├── artifact_generator.py # Fallback artifact templates
│   ├── spoonacular.py        # Spoonacular Food API (Tier 2)
│   ├── knowledge_base/       # 23 curated JSON planning documents
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/            # Dashboard, PlanEvent, Artifacts
│   │   ├── components/       # ArtifactViewer, ChatBox, Navbar, etc.
│   │   └── api/client.js     # All backend API calls
│   └── package.json
└── docs/
    └── presentation.html     # Slide deck (open in any browser)
```

---

## API Keys — Where to Get Them

| Key | Where to get it | Required? |
|-----|----------------|-----------|
| `GOOGLE_API_KEY` | https://aistudio.google.com/app/apikey | Yes — for full AI responses |
| `SPOONACULAR_API_KEY` | https://spoonacular.com/food-api | No — enables recipe suggestions |

Both are free tiers. The Gemini free tier allows ~1,500 requests/day.

---

## Architecture

```
[React Frontend — localhost:5173]
    ↓  REST API calls
[FastAPI Backend — localhost:8000]
    ↓
[Session Manager] ←→ [EventContext JSON]
    ↓
[7-Step Workflow Engine]
    ↓
[RAG Pipeline]
    ├── [Knowledge Base: 23 JSON docs]
    └── [sentence-transformers + ChromaDB → top-5 chunks]
    ↓
[Google Gemini 2.0 Flash — LLM]
    ↓
[Artifact Generator]
    ├── Task Checklist  (JSON + Markdown + PDF)
    ├── Shopping List   (JSON + Markdown + PDF)
    └── Day-of Schedule (JSON + Markdown + PDF)
    ↓
[Spoonacular API — recipe enrichment, Tier 2]
```
