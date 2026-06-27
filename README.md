# Job Hunter — AI-Powered Job Search Assistant

A 7-agent AI system with user authentication, a CLI, FastAPI backend, and Next.js dashboard. Agents find jobs, analyze your resume, score matches, tailor application materials, and prepare you for interviews — all observable in real time, with each user's data fully isolated.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Next.js Dashboard :3000                       │
│  Login · Signup · Dashboard · Jobs · Live Agent Streams          │
│  NextAuth.js sessions  ·  Protected routes (middleware.ts)       │
└───────────────────────────┬─────────────────────────────────────┘
                            │ REST + SSE  (Bearer JWT)
┌───────────────────────────▼─────────────────────────────────────┐
│                    FastAPI Backend :8001                          │
│  /api/auth/{signup,login,me}                                     │
│  /api/agents/{hunt,analyze,score,tailor,cover-letter,interview}  │
│  /api/events/{task_id}  ·  /api/jobs  ·  /api/applications      │
└──────────┬──────────────────────────────────────────────────────┘
           │ ThreadPoolExecutor (non-blocking)
┌──────────▼──────────────────────────────────────────────────────┐
│                  TaskManager + EventBand                          │
│  EventBand subclasses Band — forwards every agent message to     │
│  a per-task queue.Queue, which the SSE generator drains async.   │
│  Zero changes to the 7 existing agents.                          │
└──────────┬──────────────────────────────────────────────────────┘
           │  user_id threaded through every write
┌──────────▼──────────────────────────────────────────────────────┐
│                        7 Agents                                  │
│  Job Hunter · Resume Analyzer · Match Scorer · Resume Tailor     │
│  Cover Letter Writer · Interview Coach · Application Tracker     │
└──────────┬──────────────────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────────┐
│  SQLite (dev, auto-migrated)  /  PostgreSQL (prod)               │
│  users · jobs · applications · profiles · match_results          │
│  agent_tasks — all row-level isolated by user_id                 │
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
├── agents/                         # The 7 agents
│   ├── base_agent.py               # Shared LLM client + helpers
│   ├── job_hunter.py               # Accepts user_id → scoped saves
│   ├── resume_analyzer.py
│   ├── match_scorer.py
│   ├── resume_tailor.py
│   ├── cover_letter_writer.py
│   ├── interview_coach.py
│   └── application_tracker.py
│
├── core/
│   ├── band.py                     # Agent pub/sub message bus
│   ├── database.py                 # SQLite persistence + auto-migration
│   └── models.py                   # Data models (Job, Profile, MatchResult, …)
│
├── tools/
│   ├── job_scraper.py              # RemoteOK API fetcher
│   └── pdf_parser.py               # PDF / DOCX / TXT resume parser
│
├── backend/                        # FastAPI backend
│   ├── main.py                     # App entry point, CORS, OTel, lifespan
│   ├── config.py                   # Settings loaded from .env
│   ├── auth.py                     # JWT utilities + get_current_user dependency
│   ├── api/
│   │   ├── auth.py                 # POST /api/auth/signup·login, GET /api/auth/me
│   │   ├── agents.py               # POST endpoints to trigger each agent
│   │   ├── events.py               # GET /api/events/{task_id}  (SSE stream)
│   │   ├── jobs.py                 # GET /api/jobs  (user-scoped)
│   │   └── applications.py         # GET + PATCH /api/applications  (user-scoped)
│   ├── db/
│   │   ├── models.py               # SQLAlchemy: User + TaskRecord
│   │   └── session.py              # Async engine + session factory
│   ├── queue/
│   │   ├── manager.py              # TaskManager + TaskState (with user_id)
│   │   └── tasks.py                # Agent wrappers + EventBand
│   ├── telemetry/
│   │   └── otel.py                 # OpenTelemetry setup (console / OTLP)
│   └── requirements.txt
│
├── frontend/                       # Next.js 14 dashboard
│   ├── app/
│   │   ├── layout.tsx              # Root layout + nav + SessionProvider
│   │   ├── page.tsx                # Dashboard — trigger agents, live stream
│   │   ├── globals.css
│   │   ├── providers.tsx           # NextAuth SessionProvider wrapper
│   │   ├── api/auth/[...nextauth]/ # NextAuth catch-all route handler
│   │   ├── auth/
│   │   │   ├── login/page.tsx      # Sign-in page
│   │   │   └── signup/page.tsx     # Sign-up page
│   │   └── jobs/
│   │       └── page.tsx            # Jobs table with per-job action buttons
│   ├── components/
│   │   ├── NavUser.tsx             # Nav: shows name + sign-out when logged in
│   │   ├── AgentStatusCard.tsx     # Task status card with progress bar
│   │   ├── TaskStream.tsx          # SSE consumer — live event log
│   │   └── ui/                     # Shadcn-style components
│   │       ├── button.tsx
│   │       ├── input.tsx
│   │       ├── card.tsx
│   │       └── label.tsx
│   ├── lib/
│   │   ├── api.ts                  # Typed API client (auth-token aware)
│   │   ├── auth.ts                 # NextAuth options + credentials provider
│   │   ├── types.ts                # TypeScript types (User, Job, Task, …)
│   │   └── utils.ts                # cn() Tailwind merge helper
│   ├── middleware.ts               # Redirects unauthenticated → /auth/login
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── next.config.js              # Proxies /api/* → FastAPI :8001
│   └── tsconfig.json
│
├── data/                           # SQLite DB (auto-created + migrated, gitignored)
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
# Edit .env — set ANTHROPIC_API_KEY and JWT_SECRET
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

### 4. Configure frontend environment

```bash
cp frontend/.env.local.example frontend/.env.local   # if provided
# or create frontend/.env.local manually:
```

```env
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=any-random-string-here
BACKEND_URL=http://localhost:8001
NEXT_PUBLIC_BACKEND_URL=http://localhost:8001
```

---

## Running

### Option A — CLI only

```bash
python3 main.py
```

The CLI runs all 7 agents interactively. Data is saved to `data/jobs.db` without user isolation (single-user mode).

### Option B — FastAPI backend + Next.js dashboard

```bash
# Terminal 1 — backend
python3 -m uvicorn backend.main:app --reload --port 8001

# Terminal 2 — frontend
cd frontend
npm run dev
```

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| API docs (Swagger) | http://localhost:8001/docs |
| Health check | http://localhost:8001/health |

Open the dashboard, click **Sign up** to create an account, then start hunting.

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

## Authentication

The app uses **NextAuth.js** on the frontend and **JWT** tokens on the backend.

### Flow

```
1. User fills in /auth/signup or /auth/login
2. NextAuth credentials provider → POST /api/auth/login (FastAPI)
3. FastAPI validates credentials → returns {access_token, user}
4. NextAuth stores token in encrypted session cookie
5. Every API call includes Authorization: Bearer <token>
6. FastAPI verifies token → extracts user_id → filters data
```

### Auth endpoints

```
POST /api/auth/signup   body: {email, name, password}  → {access_token, user}
POST /api/auth/login    body: {email, password}         → {access_token, user}
GET  /api/auth/me       header: Authorization: Bearer … → {id, email, name}
```

### User data isolation

Once authenticated, each user only sees their own data:

| Resource | Behaviour |
|----------|-----------|
| `GET /api/jobs` | Returns only jobs created during the user's own hunts |
| `GET /api/applications` | Returns only the user's applications |
| `GET /api/agents/tasks` | Returns only the user's agent task history |
| `GET /api/jobs` (no token) | Returns all rows — CLI / admin access |

`user_id` is written to `jobs`, `applications`, and `profiles` at the point of creation and is never overwritten by other users.

---

## API Reference

### Auth

```bash
# Sign up
curl -X POST http://localhost:8001/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","name":"Your Name","password":"secret"}'

# Sign in
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"secret"}'
# → {"access_token": "eyJ...", "user": {...}}

# Who am I?
curl http://localhost:8001/api/auth/me \
  -H "Authorization: Bearer eyJ..."
```

### Trigger an agent

All agent endpoints accept an optional `Authorization` header. When provided, the resulting jobs and tasks are scoped to that user.

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
curl -X POST http://localhost:8001/api/agents/hunt \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ..." \
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
curl -N http://localhost:8001/api/events/3f2a1b4c-...
```

```
data: {"status": "running", "progress": 10, "message": "Searching job boards...", "done": false}
data: {"type": "band_event", "sender": "JobHunter", "msg_type": "jobs.found", "done": false}
data: {"status": "done", "progress": 100, "message": "Found 13 jobs", "result": [...], "done": true}
```

### Other endpoints

```
GET  /api/jobs                      # List jobs (user-scoped when authenticated)
GET  /api/jobs/{id}                 # Get one job
GET  /api/applications              # List applications (user-scoped)
PATCH /api/applications/{job_id}    # Update application status
GET  /api/agents/tasks              # List agent task runs (user-scoped)
GET  /api/agents/tasks/{task_id}    # Get one task
```

---

## How real-time streaming works

```
POST /api/agents/hunt  (with Bearer token)
      │
      ▼
user_id extracted from JWT
TaskManager.create("hunt", user_id=…)  →  task_id + empty queue.Queue
      │
      ▼
ThreadPoolExecutor.run(run_hunt, task_id, …, user_id)  ← non-blocking
      │
      │  (in background thread)
      ▼
JobHunterAgent.hunt(…, user_id=…)
      │  saves every job/application with user_id
      ▼
EventBand.publish(message)  ← intercepts all Band messages
      │
task.event_queue.put_nowait(event)  ← thread-safe
      │
      ▼
GET /api/events/{task_id}  (SSE)
      │  async generator drains queue every 300ms
      ▼
Browser EventSource → TaskStream component updates UI
```

---

## Database

### SQLite (default — no setup)

Data is stored at `data/jobs.db`. The schema is created (and migrated) automatically on every backend start via `init_db()`.

**Tables and user isolation:**

| Table | user_id column | Notes |
|-------|---------------|-------|
| `users` | primary key | Managed by SQLAlchemy async DB |
| `agent_tasks` | `user_id FK` | Per-user task history |
| `jobs` | `user_id` | Set at hunt time |
| `applications` | `user_id` | Set alongside jobs |
| `profiles` | `user_id` | Set at analysis time |
| `match_results` | — | Linked via job_id |
| `application_materials` | — | Linked via job_id |

### PostgreSQL (production)

Change `DATABASE_URL` in `.env` and run `docker-compose up -d postgres`. The same SQLAlchemy models work with both `aiosqlite` and `asyncpg`.

---

## OpenTelemetry

Every agent run is wrapped in an OTel span with attributes like `task.id`, `search.roles`, and `jobs.found`. Set `OTEL_ENABLED=true` and run Jaeger via `docker-compose up -d jaeger` to see the full trace at http://localhost:16686.

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

**Login says "Invalid email or password"**
Make sure the backend is running and reachable. The NextAuth credentials provider calls `http://localhost:8001/api/auth/login` server-side — if the backend is down, auth silently fails.

**`JWT_SECRET` not set warning**
Set `JWT_SECRET` in `.env` to a long random string. The default value works for local dev but must be changed before any deployment.

**Job Hunter returns irrelevant results**
RemoteOK's free API has limited tag filtering. Try single-word role names like `"Python"` or `"Engineer"`.

**SSE stream hangs**
Make sure the backend is running on `:8001` and `next.config.js` proxies `/api/*` correctly.

**Port 8001 already in use**
Kill the process with `lsof -ti:8001 | xargs kill` or change the port in both `next.config.js` and the uvicorn command.

---

## Roadmap

| Phase | Status |
|-------|--------|
| CLI with 7 agents + Band | ✅ Done |
| FastAPI backend + SSE streaming | ✅ Done |
| Next.js dashboard | ✅ Done |
| JWT auth + user system | ✅ Done |
| Per-user data isolation | ✅ Done |
| Shadcn-style UI components | ✅ Done |
| PostgreSQL + Alembic migrations | 🔜 Next |
| Resume file upload (multipart) | 🔜 Next |
| Celery + Redis (multi-server scale) | 🔮 Future |
