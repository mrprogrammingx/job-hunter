from typing import List
from rich.console import Console

from agents.base_agent import BaseAgent
from core.band import Band
from core.models import Job, CandidateProfile, MatchResult, BandMessage
from core import database as db

console = Console()


class MatchScorerAgent(BaseAgent):
    """Agent 3 — scores each job against the candidate profile."""

    def __init__(self, band: Band):
        super().__init__(band, "MatchScorer")
        band.subscribe("score.jobs", self._handle_score)

    def score_jobs(self, jobs: List[Job], profile: CandidateProfile) -> List[tuple[Job, MatchResult]]:
        console.print(f"\n[bold cyan]🎯 Match Scorer[/bold cyan] scoring {len(jobs)} jobs")

        results = []
        for i, job in enumerate(jobs, 1):
            with console.status(f"[cyan]Scoring [{i}/{len(jobs)}]: {job.title} at {job.company}...[/cyan]"):
                match = self._score_one(job, profile)
                db.save_match(match)
                results.append((job, match))

        results.sort(key=lambda x: x[1].score, reverse=True)

        self.band.send(self.name, "scores.ready", {"results": results})
        console.print(f"[green]✓ Scored {len(results)} jobs[/green]")
        return results

    def score_one(self, job: Job, profile: CandidateProfile) -> MatchResult:
        return self._score_one(job, profile)

    def _score_one(self, job: Job, profile: CandidateProfile) -> MatchResult:
        system = (
            "You are an expert technical recruiter and career coach. "
            "Evaluate job-candidate compatibility objectively and precisely."
        )
        prompt = (
            f"Score the compatibility between this candidate and job.\n\n"
            f"CANDIDATE PROFILE:\n{profile.summary()}\n"
            f"All skills: {', '.join(profile.skills)}\n\n"
            f"JOB:\nTitle: {job.title}\nCompany: {job.company}\n"
            f"Description:\n{job.description[:3000]}\n\n"
            "Return JSON with:\n"
            "- score (integer 0-100)\n"
            "- matching_skills (array of strings — skills candidate has that job needs)\n"
            "- skill_gaps (array of strings — skills job needs that candidate lacks)\n"
            "- recommendation (one of: 'Strong Match', 'Good Match', 'Partial Match', 'Poor Match')\n"
            "- reasoning (2-3 sentences explaining the score)"
        )

        data = self._llm_json(system, prompt)
        profile_id = profile.id or 0

        return MatchResult(
            job_id=job.id or 0,
            profile_id=profile_id,
            score=float(data.get("score", 0)),
            matching_skills=data.get("matching_skills", []),
            skill_gaps=data.get("skill_gaps", []),
            recommendation=data.get("recommendation", "Unknown"),
            reasoning=data.get("reasoning", ""),
        )

    def _handle_score(self, msg: BandMessage):
        return self.score_jobs(msg.payload["jobs"], msg.payload["profile"])
