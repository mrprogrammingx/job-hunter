from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    source: str
    date_posted: str
    description: str = ""
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "url": self.url,
            "source": self.source,
            "date_posted": self.date_posted,
            "description": self.description,
        }


@dataclass
class CandidateProfile:
    name: str = ""
    email: str = ""
    phone: str = ""
    skills: List[str] = field(default_factory=list)
    experience: List[Dict[str, Any]] = field(default_factory=list)
    education: List[Dict[str, Any]] = field(default_factory=list)
    projects: List[Dict[str, Any]] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    raw_text: str = ""
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "skills": self.skills,
            "experience": self.experience,
            "education": self.education,
            "projects": self.projects,
            "certifications": self.certifications,
        }

    def summary(self) -> str:
        lines = []
        if self.name:
            lines.append(f"Name: {self.name}")
        if self.skills:
            lines.append(f"Skills: {', '.join(self.skills[:15])}")
        if self.experience:
            lines.append("Experience:")
            for exp in self.experience[:3]:
                lines.append(f"  - {exp.get('title', '')} at {exp.get('company', '')} ({exp.get('duration', '')})")
        if self.education:
            lines.append("Education:")
            for edu in self.education[:2]:
                lines.append(f"  - {edu.get('degree', '')} from {edu.get('institution', '')}")
        return "\n".join(lines)


@dataclass
class MatchResult:
    job_id: int
    profile_id: int
    score: float
    skill_gaps: List[str]
    matching_skills: List[str]
    recommendation: str
    reasoning: str
    id: Optional[int] = None


@dataclass
class ApplicationMaterials:
    job_id: int
    tailored_resume: str = ""
    cover_letter: str = ""
    recruiter_message: str = ""
    linkedin_message: str = ""
    interview_questions: List[Dict[str, str]] = field(default_factory=list)
    interview_tips: str = ""
    id: Optional[int] = None


@dataclass
class Application:
    job_id: int
    status: str = "discovered"
    date_discovered: str = field(default_factory=lambda: datetime.now().isoformat())
    date_applied: Optional[str] = None
    match_score: float = 0.0
    notes: str = ""
    id: Optional[int] = None


@dataclass
class BandMessage:
    sender: str
    msg_type: str
    payload: Any
    receiver: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
