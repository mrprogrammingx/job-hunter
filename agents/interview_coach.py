from typing import List, Dict
from rich.console import Console

from agents.base_agent import BaseAgent
from core.band import Band
from core.models import Job, CandidateProfile, ApplicationMaterials, BandMessage
from core import database as db

console = Console()


class InterviewCoachAgent(BaseAgent):
    """Agent 6 — generates interview questions, answers, and preparation tips."""

    def __init__(self, band: Band):
        super().__init__(band, "InterviewCoach")
        band.subscribe("interview.prepare", self._handle_prepare)

    def prepare(self, job: Job, profile: CandidateProfile) -> ApplicationMaterials:
        console.print(f"\n[bold cyan]🎓 Interview Coach[/bold cyan] preparing for: {job.title} at {job.company}")

        with console.status("[cyan]Generating technical questions...[/cyan]"):
            technical_qs = self._generate_technical(job, profile)

        with console.status("[cyan]Generating behavioral questions...[/cyan]"):
            behavioral_qs = self._generate_behavioral(job, profile)

        with console.status("[cyan]Writing interview tips...[/cyan]"):
            tips = self._generate_tips(job, profile)

        all_questions = technical_qs + behavioral_qs

        existing = db.get_materials(job.id or 0)
        materials = existing or ApplicationMaterials(job_id=job.id or 0)
        materials.interview_questions = all_questions
        materials.interview_tips = tips
        db.save_materials(materials)

        console.print(f"[green]✓ {len(all_questions)} questions generated + tips[/green]")
        self.band.send(self.name, "interview.ready", {"job_id": job.id, "materials": materials})
        return materials

    def _generate_technical(self, job: Job, profile: CandidateProfile) -> List[Dict[str, str]]:
        system = "You are a senior technical interviewer. Generate realistic, role-specific interview questions."
        prompt = (
            f"Generate 5 technical interview questions for this role with suggested answers.\n\n"
            f"Role: {job.title} at {job.company}\n"
            f"Job description excerpt:\n{job.description[:1500]}\n\n"
            f"Candidate skills: {', '.join(profile.skills[:15])}\n\n"
            "Return JSON array of objects with keys: 'type' ('technical'), 'question', 'suggested_answer'"
        )
        try:
            data = self._llm_json(system, prompt, max_tokens=2048)
            return data if isinstance(data, list) else data.get("questions", [])
        except Exception:
            return []

    def _generate_behavioral(self, job: Job, profile: CandidateProfile) -> List[Dict[str, str]]:
        system = "You are a behavioral interviewer experienced with STAR-format questions."
        prompt = (
            f"Generate 5 behavioral interview questions with STAR-format answer guidance for:\n"
            f"Role: {job.title}\n"
            f"Candidate background: {profile.experience[0].get('title', '') if profile.experience else 'N/A'} "
            f"at {profile.experience[0].get('company', '') if profile.experience else 'N/A'}\n\n"
            "Focus on: leadership, problem-solving, collaboration, handling failure, and impact.\n"
            "Return JSON array of objects with keys: 'type' ('behavioral'), 'question', 'suggested_answer'"
        )
        try:
            data = self._llm_json(system, prompt, max_tokens=2048)
            return data if isinstance(data, list) else data.get("questions", [])
        except Exception:
            return []

    def _generate_tips(self, job: Job, profile: CandidateProfile) -> str:
        system = "You are a career coach preparing candidates for job interviews."
        prompt = (
            f"Give 5 specific preparation tips for interviewing at {job.company} for the {job.title} role. "
            f"Consider the candidate's background: {profile.summary()}\n\n"
            "Include: company research angles, what to emphasize, potential weak points to address, "
            "questions to ask the interviewer, and logistics advice."
        )
        return self._llm(system, prompt, max_tokens=1024)

    def _handle_prepare(self, msg: BandMessage) -> ApplicationMaterials:
        return self.prepare(msg.payload["job"], msg.payload["profile"])
