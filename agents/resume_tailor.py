from rich.console import Console

from agents.base_agent import BaseAgent
from core.band import Band
from core.models import Job, CandidateProfile, ApplicationMaterials, BandMessage
from core import database as db

console = Console()


class ResumeTailorAgent(BaseAgent):
    """Agent 4 — rewrites the resume to target a specific job."""

    def __init__(self, band: Band):
        super().__init__(band, "ResumeTailor")
        band.subscribe("resume.tailor", self._handle_tailor)

    def tailor(self, job: Job, profile: CandidateProfile) -> ApplicationMaterials:
        console.print(f"\n[bold cyan]✏️  Resume Tailor[/bold cyan] customizing for: {job.title} at {job.company}")

        with console.status("[cyan]Tailoring resume with Claude...[/cyan]"):
            tailored_resume = self._tailor_resume(job, profile)

        materials = ApplicationMaterials(job_id=job.id or 0, tailored_resume=tailored_resume)
        db.save_materials(materials)

        console.print("[green]✓ Tailored resume ready[/green]")
        self.band.send(self.name, "resume.tailored", {"job_id": job.id, "materials": materials})
        return materials

    def _tailor_resume(self, job: Job, profile: CandidateProfile) -> str:
        system = (
            "You are an expert resume writer specializing in ATS optimization. "
            "Rewrite resumes to match specific job descriptions while maintaining 100% factual accuracy. "
            "Never invent experience, skills, or achievements that the candidate does not have."
        )
        prompt = (
            f"Tailor this resume for the following job. Do NOT invent anything — only reorder, rephrase, "
            f"and emphasize existing experience and skills.\n\n"
            f"TARGET JOB:\nTitle: {job.title}\nCompany: {job.company}\n"
            f"Description:\n{job.description[:3000]}\n\n"
            f"CURRENT RESUME (raw text):\n{profile.raw_text[:5000]}\n\n"
            "Produce a clean, professional resume in plain text format with these sections:\n"
            "- Header (name, email, phone)\n"
            "- Professional Summary (3 sentences, tailored to this role)\n"
            "- Skills (reordered to put most relevant first, ATS keywords from job description added if candidate actually has them)\n"
            "- Professional Experience (bullet points rewritten to emphasize relevance to this role)\n"
            "- Education\n"
            "- Projects (if relevant)\n"
            "- Certifications (if any)\n\n"
            "At the end, add a section '--- ATS KEYWORDS ADDED ---' listing keywords from the job description "
            "that were naturally incorporated."
        )

        return self._llm(system, prompt, max_tokens=4096)

    def _handle_tailor(self, msg: BandMessage) -> ApplicationMaterials:
        return self.tailor(msg.payload["job"], msg.payload["profile"])
