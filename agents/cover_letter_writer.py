from rich.console import Console

from agents.base_agent import BaseAgent
from core.band import Band
from core.models import Job, CandidateProfile, ApplicationMaterials, BandMessage
from core import database as db

console = Console()


class CoverLetterWriterAgent(BaseAgent):
    """Agent 5 — generates cover letter, recruiter email, and LinkedIn message."""

    def __init__(self, band: Band):
        super().__init__(band, "CoverLetterWriter")
        band.subscribe("cover_letter.write", self._handle_write)

    def write(self, job: Job, profile: CandidateProfile) -> ApplicationMaterials:
        console.print(f"\n[bold cyan]✉️  Cover Letter Writer[/bold cyan] drafting materials for: {job.title}")

        with console.status("[cyan]Writing cover letter...[/cyan]"):
            cover_letter = self._write_cover_letter(job, profile)

        with console.status("[cyan]Writing recruiter message...[/cyan]"):
            recruiter_message = self._write_recruiter_message(job, profile)

        with console.status("[cyan]Writing LinkedIn message...[/cyan]"):
            linkedin_message = self._write_linkedin_message(job, profile)

        existing = db.get_materials(job.id or 0)
        materials = existing or ApplicationMaterials(job_id=job.id or 0)
        materials.cover_letter = cover_letter
        materials.recruiter_message = recruiter_message
        materials.linkedin_message = linkedin_message
        db.save_materials(materials)

        console.print("[green]✓ Application materials ready[/green]")
        self.band.send(self.name, "cover_letter.ready", {"job_id": job.id, "materials": materials})
        return materials

    def _write_cover_letter(self, job: Job, profile: CandidateProfile) -> str:
        system = (
            "You are an expert cover letter writer. Write compelling, personalized cover letters "
            "that are concise (under 350 words), professional, and specific to the role and company."
        )
        prompt = (
            f"Write a professional cover letter for this application.\n\n"
            f"CANDIDATE:\nName: {profile.name}\nEmail: {profile.email}\n"
            f"Skills: {', '.join(profile.skills[:10])}\n"
            f"Most recent role: {profile.experience[0].get('title', 'N/A') if profile.experience else 'N/A'} "
            f"at {profile.experience[0].get('company', 'N/A') if profile.experience else 'N/A'}\n\n"
            f"JOB:\nTitle: {job.title}\nCompany: {job.company}\nLocation: {job.location}\n"
            f"Description:\n{job.description[:2000]}\n\n"
            "The cover letter should:\n"
            "- Open with a strong hook specific to the company/role\n"
            "- Connect the candidate's specific experience to the job requirements\n"
            "- Show genuine enthusiasm for the company\n"
            "- Close with a clear call to action\n"
            "- Be under 350 words"
        )
        return self._llm(system, prompt, max_tokens=1024)

    def _write_recruiter_message(self, job: Job, profile: CandidateProfile) -> str:
        system = "You write concise, professional recruiter outreach messages for job applications."
        prompt = (
            f"Write a short recruiter outreach email (under 150 words) for:\n"
            f"Candidate: {profile.name}, applying for {job.title} at {job.company}.\n"
            f"Candidate's top skills: {', '.join(profile.skills[:5])}\n"
            f"Most recent role: {profile.experience[0].get('title', '') if profile.experience else ''}\n\n"
            "The message should be direct, mention the specific role, highlight 1-2 key qualifications, "
            "and end with a clear ask (a call or brief chat)."
        )
        return self._llm(system, prompt, max_tokens=512)

    def _write_linkedin_message(self, job: Job, profile: CandidateProfile) -> str:
        system = "You write short, personalized LinkedIn connection request messages."
        prompt = (
            f"Write a LinkedIn connection request message (under 300 characters) from {profile.name} "
            f"to a recruiter/employee at {job.company} regarding the {job.title} position. "
            "Be warm, specific, and professional."
        )
        return self._llm(system, prompt, max_tokens=256)

    def _handle_write(self, msg: BandMessage) -> ApplicationMaterials:
        return self.write(msg.payload["job"], msg.payload["profile"])
