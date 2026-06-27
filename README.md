# Job Hunter — AI-Powered Job Search Assistant

A 7-agent AI system with a CLI, FastAPI backend, and Next.js dashboard. Agents find jobs, analyze your resume, score matches, tailor application materials, and prepare you for interviews — all observable in real time.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Next.js Dashboard :3000                       │
│         Dashboard · Jobs · Applications · Live Agent Streams     │
└───────────────────────────┬─────────────────────────────────────┘
                            │ REST + SSE
┌───────────────────────────▼─────────────────────────────────────┐
│                    FastAPI Backend :8000                          │
│  /api/agents/{hunt,analyze,score,tailor,cover-letter,interview}  │
│  /api/events/{task_id}  ·  /api/jobs  ·  /api/applications      │
└──────────┬──────────────────────────────────────────────────────┘
           │ ThreadPoolExecutor (non-blocking)
┌──────────▼──────────────────────────────────────────────────────┐
│                      TaskManager + EventBand                     │
│  EventBand subclasses Band — forwards every agent message to     │
│  a per-task queue.Queue, which the SSE generator drains async.   │
│  Zero changes to the 7 existing agents.                          │
└──────────┬──────────────────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────────┐
│                        7 Agents (unchanged)                      │
│  Job Hunter · Resume Analyzer · Match Scorer · Resume Tailor     │
│  Cover Letter Writer · Interview Coach · Application Tracker     │
└──────────┬──────────────────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────────┐
│              SQLite (dev)  /  PostgreSQL (prod)                  │
│                    Band message bus (core)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agents

| # | Agent | Purpose | Output |
|---|-------|---------|--------|
| 1 | **Job Hunter** | Searches job boards for matching listings | Ranked job list |
| 2 | **Resume Analyzer** | Parses your resume into a structured profile | Skills, experience, education |
| 3 | **Match Scorer** | Scores each job against your profile (0–100) | Match score + skill gap analysis |
| 4 | **Resume Tailor** | Rewrites your resume for a specific job (ATS-optimized) | Tailored resume |
| 5 | **Cover Letter Writer** | Generates cover letter, recruiter email, LinkedIn message | 3 application documents |
| 6 | **Interview Coach** | Creates technical + behavioral Q&A and prep tips | Interview preparation kit |
| 7 | **Application Tracker** | Tracks pipeline status and metrics | Dashboard + statistics |

---

## Project Structure

```
job-hunter/
├── agents/                         # The 7 agents (unchanged by web layer)
│   ├── base_agent.py               # Shared LLM client + helpers
│   ├── job_hunter.py
│   ├── resume_analyzer.py
│   ├── match_scorer.py
│   ├── resume_tailor.py
│   ├── cover_letter_writer.py
│   ├── interview_coach.py
│   └── application_tracker.py
│
├── core/
│   ├── band.py                     # Agent pub/sub message bus
│   ├── database.py                 # SQLite persistence (shared by CLI + backend)
│   └── models.py                   # Data models (Job, Profile, MatchResult, …)
│
├── tools/
│   ├── job_scraper.py              # RemoteOK API fetcher
│   └── pdf_parser.py               # PDF / DOCX / TXT resume parser
│
├── backend/                        # FastAPI backend
│   ├── main.py                     # App entry point, CORS, OTel, lifespan
│   ├── config.py                   # Settings loaded from .env
│   ├── api/
│   │   ├── agents.py               # POST endpoints to trigger each agent
│   │   ├── events.py               # GET /api/events/{task_id}  (SSE stream)
│   │   ├── jobs.py                 # GET /api/jobs
│   │   └── applications.py        # GET + PATCH /api/applications
│   ├── db/
│   │   ├── models.py               # SQLAlchemy TaskRecord model
│   │   └── session.py              # Async engine + session factory
│   ├── queue/
│   │   ├── manager.py              # TaskManager + TaskState (in-memory)
│   │   └── tasks.py                # Agent wrappers + EventBand
│   ├── telemetry/
│   │   └── otel.py                 # OpenTelemetry setup (console / OTLP)
│   └── requirements.txt
│
├── frontend/                       # Next.js 14 dashboard
│   ├── app/
│   │   ├── layout.tsx              # Root layout + nav
│   │   ├── page.tsx                # Dashboard — trigger agents, live stream
│   │   ├── globals.css
│   │   └── jobs/
│   │       └── page.tsx            # Jobs table with per-job action buttons
│   ├── components/
│   │   ├── AgentStatusCard.tsx     # Task status card with progress bar
│   │   └── TaskStream.tsx          # SSE consumer — live event log
│   ├── lib/
│   │   ├── api.ts                  # Typed API client
│   │   └── types.ts                # TypeScript types
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── next.config.js              # Proxies /api/* → FastAPI :8000
│   └── tsconfig.json
│
├── data/                           # SQLite DB lives here (auto-created, gitignored)
├── outputs/                        # Generated resumes / cover letters (gitignored)
├── docker-compose.yml              # PostgreSQL + Jaeger (optional)
├── main.py                         # CLI entry point (still works independently)
├── requirements.txt                # CLI dependencies
├── .env                            # Your secrets (never committed)
└── .env.example                    # Template
```

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com) *(separate from Claude Pro)*

---

## Setup

### 1. Clone and configure

```bash
git clone https://github.com/mrprogrammingx/job-hunter
cd job-hunter
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY
```

### 2. Install Python dependencies

```bash
# CLI
pip install -r requirements.txt

# Backend
pip install -r backend/requirements.txt
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
```

---

## Running

### Option A — CLI only

```bash
cd job-hunter
python3 main.py
```

### Option B — FastAPI backend + Next.js dashboard

```bash
# Terminal 1 — backend
cd job-hunter
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — frontend
cd job-hunter/frontend
npm run dev
```

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

### Option C — With PostgreSQL + distributed tracing (Jaeger)

```bash
docker-compose up -d
```

Then update `.env`:

```env
DATABASE_URL=postgresql+asyncpg://jobhunter:jobhunter@localhost:5432/jobhunter
OTEL_ENABLED=true
OTEL_ENDPOINT=http://localhost:4317
```

| Service | URL |
|---------|-----|
| Jaeger traces UI | http://localhost:16686 |
| PostgreSQL | localhost:5432 |

---

## API Reference

### Trigger an agent

All agent endpoints return immediately with a `task_id`. Use the SSE stream to follow progress.

```
POST /api/agents/hunt
POST /api/agents/analyze
POST /api/agents/score
POST /api/agents/tailor/{job_id}
POST /api/agents/cover-letter/{job_id}
POST /api/agents/interview/{job_id}
```

**Example — trigger Job Hunter:**

```bash
curl -X POST http://localhost:8000/api/agents/hunt \
  -H "Content-Type: application/json" \
  -d '{"roles": ["Data Engineer"], "keywords": ["Python", "Airflow"], "location": "Remote", "experience_level": "mid"}'
```

```json
{
  "task_id": "3f2a1b4c-...",
  "agent": "hunt",
  "stream_url": "/api/events/3f2a1b4c-..."
}
```

### Stream agent progress (SSE)

```
GET /api/events/{task_id}
```

```bash
curl -N http://localhost:8000/api/events/3f2a1b4c-...
```

```
data: {"status": "running", "progress": 10, "message": "Searching job boards...", "done": false}
data: {"type": "band_event", "sender": "JobHunter", "msg_type": "jobs.found", "done": false}
data: {"status": "done", "progress": 100, "message": "Found 13 jobs", "result": [...], "done": true}
```

### Other endpoints

```
GET  /api/jobs                      # List all stored jobs
GET  /api/jobs/{id}                 # Get one job
GET  /api/applications              # List all applications + pipeline status
PATCH /api/applications/{job_id}    # Update application status
GET  /api/agents/tasks              # List all agent task runs
GET  /api/agents/tasks/{task_id}    # Get one task
```

---

## How the real-time streaming works

```
POST /api/agents/hunt
      │
      ▼
TaskManager.create("hunt")  →  task_id + empty queue.Queue
      │
      ▼
ThreadPoolExecutor.run(run_hunt, task_id, ...)   ← non-blocking, returns immediately
      │
      │  (in background thread)
      ▼
EventBand.publish(message)
      │  ← intercepts every agent-to-agent Band message
      ▼
task.event_queue.put_nowait(event)   ← thread-safe
      │
      ▼
GET /api/events/{task_id}  (SSE)
      │  ← async generator drains queue every 300ms
      ▼
Browser EventSource receives events → TaskStream component updates UI
```

---

## Database

The app defaults to SQLite at `data/jobs.db` — no setup needed.

To switch to PostgreSQL, change `DATABASE_URL` in `.env` and run `docker-compose up -d postgres`. The same SQLAlchemy models work with both drivers (`aiosqlite` for SQLite, `asyncpg` for PostgreSQL).

---

## OpenTelemetry

Every agent run is wrapped in an OTel span with attributes like `task.id`, `search.roles`, and `jobs.found`. Set `OTEL_ENABLED=true` and run Jaeger via `docker-compose up -d jaeger` to see the full distributed trace at http://localhost:16686.

---

## Supported resume formats

| Format | Support |
|--------|---------|
| `.pdf` | ✅ |
| `.docx` | ✅ (requires `pip install python-docx`) |
| `.txt` | ✅ |

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'pdfplumber'`**
```bash
pip install pdfplumber
```

**`KeyError: 'ANTHROPIC_API_KEY'`**
```bash
cp .env.example .env   # then add your key
```

**`BadRequestError: credit balance too low`**
The Anthropic API requires separate billing from Claude Pro. Add credits at [console.anthropic.com → Plans & Billing](https://console.anthropic.com).

**Job Hunter returns irrelevant results**
RemoteOK's free API has limited tag filtering. Try single-word role names like `"Python"` or `"Engineer"`.

**SSE stream hangs**
Make sure the backend is running on `:8000` and `next.config.js` proxies `/api/*` correctly.

---

## Roadmap

| Phase | Status |
|-------|--------|
| CLI with 7 agents + Band | ✅ Done |
| FastAPI backend + SSE streaming | ✅ Done |
| Next.js dashboard | ✅ Done |
| PostgreSQL + Alembic migrations | 🔜 Next |
| JWT auth + resume file upload | 🔜 Next |
| Celery + Redis (multi-server scale) | 🔮 Future |
