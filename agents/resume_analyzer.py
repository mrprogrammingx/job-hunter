from rich.console import Console

from agents.base_agent import BaseAgent
from core.band import Band
from core.models import CandidateProfile, BandMessage
from core import database as db
from tools.pdf_parser import extract_text

console = Console()


class ResumeAnalyzerAgent(BaseAgent):
    """Agent 2 — parses a resume and builds a structured candidate profile."""

    def __init__(self, band: Band):
        super().__init__(band, "ResumeAnalyzer")
        band.subscribe("resume.analyze", self._handle_analyze)

    def analyze(self, resume_path: str) -> CandidateProfile:
        console.print(f"\n[bold cyan]📄 Resume Analyzer[/bold cyan] processing: {resume_path}")

        with console.status("[cyan]Extracting text from resume...[/cyan]"):
            raw_text = extract_text(resume_path)

        if not raw_text.strip():
            raise ValueError("Could not extract text from resume. Is the file readable?")

        console.print(f"[dim]Extracted {len(raw_text)} characters. Structuring with AI...[/dim]")

        with console.status("[cyan]Analyzing resume with Claude...[/cyan]"):
            profile = self._structure_profile(raw_text)

        profile_id = db.save_profile(profile)
        profile.id = profile_id

        console.print(f"[green]✓ Profile created (id={profile_id})[/green]")
        console.print(f"[dim]  Skills: {len(profile.skills)} | Experience: {len(profile.experience)} entries | Education: {len(profile.education)} entries[/dim]")

        self.band.send(self.name, "profile.ready", {"profile": profile})
        return profile

    def _structure_profile(self, raw_text: str) -> CandidateProfile:
        system = (
            "You are an expert resume parser. Extract all information from the resume and return a structured JSON object."
        )
        prompt = (
            f"Parse this resume and return a JSON object with these exact keys:\n"
            "- name (string)\n"
            "- email (string)\n"
            "- phone (string)\n"
            "- skills (array of strings)\n"
            "- experience (array of objects with: title, company, duration, responsibilities[])\n"
            "- education (array of objects with: degree, institution, year, gpa)\n"
            "- projects (array of objects with: name, description, technologies[])\n"
            "- certifications (array of strings)\n\n"
            f"Resume text:\n{raw_text[:8000]}"
        )

        data = self._llm_json(system, prompt, max_tokens=4096)

        return CandidateProfile(
            name=data.get("name", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            skills=_ensure_list(data.get("skills", [])),
            experience=_ensure_list(data.get("experience", [])),
            education=_ensure_list(data.get("education", [])),
            projects=_ensure_list(data.get("projects", [])),
            certifications=_ensure_list(data.get("certifications", [])),
            raw_text=raw_text,
        )

    def _handle_analyze(self, msg: BandMessage) -> CandidateProfile:
        return self.analyze(msg.payload["path"])


def _ensure_list(val) -> list:
    return val if isinstance(val, list) else []
