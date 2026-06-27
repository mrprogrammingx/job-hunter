# Job Hunter — AI-Powered Job Search Assistant

A 7-agent CLI application that automates your entire job search pipeline: finding jobs, analyzing your resume, scoring matches, tailoring application materials, and preparing you for interviews.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         BAND (Message Bus)                   │
│  pub/sub communication layer connecting all agents           │
└──────────────────────────┬──────────────────────────────────┘
                           │
     ┌─────────────────────┼──────────────────────┐
     ▼                     ▼                      ▼
┌─────────┐         ┌─────────────┐        ┌──────────────┐
│ Agent 1 │         │   Agent 2   │        │   Agent 3    │
│  Job    │──────▶  │  Resume     │──────▶ │   Match      │
│ Hunter  │  jobs   │  Analyzer   │ profile│   Scorer     │
└─────────┘         └─────────────┘        └──────┬───────┘
                                                  │ scores
                    ┌─────────────────────────────┘
                    ▼
             ┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
             │   Agent 4   │     │    Agent 5        │     │   Agent 6    │
             │  Resume     │────▶│  Cover Letter     │────▶│  Interview   │
             │  Tailor     │     │  Writer           │     │  Coach       │
             └─────────────┘     └──────────────────┘     └──────────────┘
                                                                  │
                                          ┌───────────────────────┘
                                          ▼
                                   ┌─────────────┐
                                   │   Agent 7   │
                                   │ Application │
                                   │  Tracker    │
                                   └─────────────┘
```

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

## Project Structure

```
job-hunter/
├── agents/                     # The 7 agents
│   ├── base_agent.py           # Shared LLM client + helpers
│   ├── job_hunter.py
│   ├── resume_analyzer.py
│   ├── match_scorer.py
│   ├── resume_tailor.py
│   ├── cover_letter_writer.py
│   ├── interview_coach.py
│   └── application_tracker.py
├── core/
│   ├── band.py                 # Agent communication hub (pub/sub)
│   ├── database.py             # SQLite persistence layer
│   └── models.py               # Data models (Job, Profile, MatchResult, etc.)
├── tools/
│   ├── job_scraper.py          # RemoteOK API fetcher
│   └── pdf_parser.py           # PDF / DOCX / TXT resume parser
├── outputs/                    # Generated files saved here (auto-created)
├── main.py                     # CLI entry point
├── requirements.txt
├── .env.example
└── .env                        # Your API key goes here (never commit this)
```

Data is stored in `~/.job-hunter/jobs.db` (SQLite, created automatically).

## Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com) (separate from Claude Pro)

## Setup

### 1. Clone / navigate to the project

```bash
cd job-hunter
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your API key

```bash
cp .env.example .env
```

Open `.env` and set:

```
ANTHROPIC_API_KEY=sk-ant-...
```

### 5. Run

```bash
python3 main.py
```

## Usage

The app presents an interactive menu:

```
[1] 🔍 Hunt for jobs
[2] 📄 Analyze my resume
[3] 🎯 Score job matches
[4] 🚀 Full workflow (hunt → analyze → score)
[5] ✏️  Tailor resume for a job
[6] ✉️  Write application materials
[7] 🎓 Interview prep
[8] 📊 View application tracker
[9] 🔄 Update application status
[0]  Exit
```

### Recommended first-time flow

```
4 → Full workflow    (enter your preferences + resume path)
5 → Tailor resume   (pick the top-scored job)
6 → Write materials (cover letter + recruiter/LinkedIn messages)
7 → Interview prep  (technical + behavioral Q&A)
8 → View tracker    (see your pipeline dashboard)
```

### Supported resume formats

| Format | Support |
|--------|---------|
| `.pdf` | ✅ Full support |
| `.docx` | ✅ Full support (requires `pip install python-docx`) |
| `.txt` | ✅ Full support |

### Outputs

Tailored resumes, cover letters, and interview prep are saved to `outputs/` in your working directory:

```
outputs/
├── Jellyfish_Data_Engineer_resume.txt
├── Jellyfish_Data_Engineer_cover_letter.txt
└── Jellyfish_Data_Engineer_interview.json
```

## Configuration

All settings live in `.env`:

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Required. Your Anthropic API key. |

The app uses `claude-sonnet-4-6` by default. To change the model, edit `model` in `agents/base_agent.py`.

## How the Band works

The **Band** is a lightweight pub/sub message bus that decouples agents from each other. Agents never call each other directly — they publish typed messages and subscribe to message types:

```python
# Agent 1 publishes after finding jobs
band.send("JobHunter", "jobs.found", {"jobs": jobs, "count": len(jobs)})

# Agent 3 subscribes and reacts
band.subscribe("score.jobs", self._handle_score)
```

Every message is logged to history, making the full agent communication trace inspectable.

## Troubleshooting

**`ModuleNotFoundError: No module named 'pdfplumber'`**
```bash
pip install pdfplumber
```

**`ModuleNotFoundError: No module named 'docx'`**
```bash
pip install python-docx
```

**`KeyError: 'ANTHROPIC_API_KEY'`**
Make sure `.env` exists and contains your key. Or export it directly:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

**`BadRequestError: credit balance too low`**
The Anthropic API requires separate billing from Claude Pro. Add credits at [console.anthropic.com → Plans & Billing](https://console.anthropic.com).

**Job Hunter returns irrelevant results**
RemoteOK's free API has limited filtering. Try broader keywords, or use option `[1]` with single-word role names like `"Python"` or `"Engineer"`.

## Dependencies

| Package | Purpose |
|---------|---------|
| `anthropic` | Claude API client |
| `pdfplumber` | PDF text extraction |
| `requests` | Job board API calls |
| `rich` | Terminal UI (tables, panels, prompts) |
| `typer` | CLI framework |
| `python-dotenv` | `.env` file loading |
