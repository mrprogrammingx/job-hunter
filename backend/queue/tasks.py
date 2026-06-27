"""
Agent task wrappers.

Each function here is the sync "consumer" side of the queue.
FastAPI runs them in a ThreadPoolExecutor so they don't block the event loop.

The EventBand subclass intercepts every Band message and forwards it to the
task's SSE event queue — so the frontend sees agent-to-agent communication
in real time with zero changes to the existing agents.
"""

import sys
from pathlib import Path
from typing import Any

# Make project root importable from inside the backend package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.band import Band
from core.models import BandMessage
from backend.queue.manager import task_manager
from backend.telemetry.otel import get_tracer

tracer = get_tracer()


# ---------------------------------------------------------------------------
# EventBand — the bridge between agents and SSE
# ---------------------------------------------------------------------------

class EventBand(Band):
    """Extends Band to forward every message to the per-task SSE queue."""

    def __init__(self, task_id: str):
        super().__init__(verbose=False)
        self.task_id = task_id

    def publish(self, message: BandMessage):
        task = task_manager.get(self.task_id)
        if task:
            task.event_queue.put_nowait({
                "type": "band_event",
                "task_id": self.task_id,
                "msg_type": message.msg_type,
                "sender": message.sender,
                "payload": _safe_serialize(message.payload),
                "done": False,
            })
        return super().publish(message)


def _safe_serialize(obj: Any) -> Any:
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if isinstance(obj, dict):
        return {k: _safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_safe_serialize(i) for i in obj]
    return obj


# ---------------------------------------------------------------------------
# Task handlers — one per agent
# ---------------------------------------------------------------------------

def run_hunt(task_id: str, roles: list, keywords: list, location: str, experience_level: str):
    with tracer.start_as_current_span("agent.job_hunter") as span:
        span.set_attribute("task.id", task_id)
        span.set_attribute("search.roles", str(roles))
        try:
            from agents.job_hunter import JobHunterAgent

            task_manager.update(task_id, status="running", progress=10, message="Searching job boards...")
            band = EventBand(task_id)
            jobs = JobHunterAgent(band).hunt(
                roles=roles, keywords=keywords,
                location=location, experience_level=experience_level,
            )
            span.set_attribute("jobs.found", len(jobs))
            task_manager.finish(task_id, result=[j.to_dict() for j in jobs])
        except Exception as exc:
            span.record_exception(exc)
            task_manager.fail(task_id, str(exc))
            raise


def run_analyze(task_id: str, resume_path: str):
    with tracer.start_as_current_span("agent.resume_analyzer") as span:
        span.set_attribute("task.id", task_id)
        try:
            from agents.resume_analyzer import ResumeAnalyzerAgent

            task_manager.update(task_id, status="running", progress=20, message="Extracting resume text...")
            band = EventBand(task_id)
            profile = ResumeAnalyzerAgent(band).analyze(resume_path)
            task_manager.finish(task_id, result=profile.to_dict())
        except Exception as exc:
            span.record_exception(exc)
            task_manager.fail(task_id, str(exc))
            raise


def run_score(task_id: str, job_ids: list[int]):
    with tracer.start_as_current_span("agent.match_scorer") as span:
        span.set_attribute("task.id", task_id)
        try:
            from agents.match_scorer import MatchScorerAgent
            from core.database import get_job, get_latest_profile

            task_manager.update(task_id, status="running", progress=10, message="Loading jobs and profile...")
            profile = get_latest_profile()
            jobs = [j for i in job_ids if (j := get_job(i))]
            band = EventBand(task_id)
            results = MatchScorerAgent(band).score_jobs(jobs, profile)
            task_manager.finish(task_id, result=[
                {"job": j.to_dict(), "score": m.score,
                 "recommendation": m.recommendation, "skill_gaps": m.skill_gaps,
                 "matching_skills": m.matching_skills, "reasoning": m.reasoning}
                for j, m in results
            ])
        except Exception as exc:
            span.record_exception(exc)
            task_manager.fail(task_id, str(exc))
            raise


def run_tailor(task_id: str, job_id: int):
    with tracer.start_as_current_span("agent.resume_tailor") as span:
        span.set_attribute("task.id", task_id)
        span.set_attribute("job.id", job_id)
        try:
            from agents.resume_tailor import ResumeTailorAgent
            from core.database import get_job, get_latest_profile

            task_manager.update(task_id, status="running", progress=20, message="Tailoring resume...")
            band = EventBand(task_id)
            materials = ResumeTailorAgent(band).tailor(get_job(job_id), get_latest_profile())
            task_manager.finish(task_id, result={"tailored_resume": materials.tailored_resume})
        except Exception as exc:
            span.record_exception(exc)
            task_manager.fail(task_id, str(exc))
            raise


def run_cover_letter(task_id: str, job_id: int):
    with tracer.start_as_current_span("agent.cover_letter_writer") as span:
        span.set_attribute("task.id", task_id)
        try:
            from agents.cover_letter_writer import CoverLetterWriterAgent
            from core.database import get_job, get_latest_profile

            task_manager.update(task_id, status="running", progress=20, message="Writing application materials...")
            band = EventBand(task_id)
            m = CoverLetterWriterAgent(band).write(get_job(job_id), get_latest_profile())
            task_manager.finish(task_id, result={
                "cover_letter": m.cover_letter,
                "recruiter_message": m.recruiter_message,
                "linkedin_message": m.linkedin_message,
            })
        except Exception as exc:
            span.record_exception(exc)
            task_manager.fail(task_id, str(exc))
            raise


def run_interview(task_id: str, job_id: int):
    with tracer.start_as_current_span("agent.interview_coach") as span:
        span.set_attribute("task.id", task_id)
        try:
            from agents.interview_coach import InterviewCoachAgent
            from core.database import get_job, get_latest_profile

            task_manager.update(task_id, status="running", progress=20, message="Generating interview prep...")
            band = EventBand(task_id)
            m = InterviewCoachAgent(band).prepare(get_job(job_id), get_latest_profile())
            task_manager.finish(task_id, result={
                "questions": m.interview_questions,
                "tips": m.interview_tips,
            })
        except Exception as exc:
            span.record_exception(exc)
            task_manager.fail(task_id, str(exc))
            raise
