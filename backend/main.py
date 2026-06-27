"""
Job Hunter — FastAPI Backend

Run with:
    cd job-hunter
    uvicorn backend.main:app --reload --port 8000

Interactive docs: http://localhost:8000/docs
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from backend.config import settings
from backend.db.session import init_async_db
from backend.telemetry.otel import setup_telemetry
from backend.api.auth import router as auth_router
from backend.api.agents import router as agents_router
from backend.api.events import router as events_router
from backend.api.jobs import router as jobs_router
from backend.api.applications import router as applications_router

import os
os.environ.setdefault("ANTHROPIC_API_KEY", settings.anthropic_api_key)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_telemetry(otel_enabled=settings.otel_enabled, endpoint=settings.otel_endpoint)
    await init_async_db()
    yield


app = FastAPI(
    title="Job Hunter API",
    description="7-agent AI-powered job search backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FastAPIInstrumentor.instrument_app(app)

app.include_router(auth_router)
app.include_router(agents_router)
app.include_router(events_router)
app.include_router(jobs_router)
app.include_router(applications_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
