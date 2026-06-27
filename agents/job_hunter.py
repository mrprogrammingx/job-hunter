from typing import List
from rich.console import Console
from rich.progress import track

from agents.base_agent import BaseAgent
from core.band import Band
from core.models import Job, BandMessage
from core import database as db
from tools.job_scraper import fetch_jobs

console = Console()


class JobHunterAgent(BaseAgent):
    """Agent 1 — searches job boards and stores matching listings."""

    def __init__(self, band: Band):
        super().__init__(band, "JobHunter")
        band.subscribe("search.start", self._handle_search)

    def hunt(self, roles: List[str], keywords: List[str], location: str, experience_level: str) -> List[Job]:
        console.print(f"\n[bold cyan]🔍 Job Hunter[/bold cyan] searching for: {', '.join(roles)}")

        with console.status("[cyan]Fetching jobs from RemoteOK...[/cyan]"):
            raw_jobs = fetch_jobs(roles, keywords, location)

        if not raw_jobs:
            console.print("[yellow]No jobs found via API. Try broader keywords.[/yellow]")
            return []

        console.print(f"[dim]Found {len(raw_jobs)} raw listings. Ranking with AI...[/dim]")

        ranked = self._rank_jobs(raw_jobs, roles, keywords, experience_level)

        saved_ids = []
        for job in ranked:
            jid = db.save_job(job)
            job.id = jid
            db.upsert_application(
                _make_app(job.id)
            )
            saved_ids.append(jid)

        console.print(f"[green]✓ Stored {len(ranked)} jobs[/green]")

        self.band.send(self.name, "jobs.found", {"jobs": ranked, "count": len(ranked)})
        return ranked

    def _rank_jobs(self, jobs: List[Job], roles: List[str], keywords: List[str], level: str) -> List[Job]:
        if not jobs:
            return []

        job_list = "\n".join(
            f"{i+1}. {j.title} at {j.company} ({j.location}) — {j.date_posted}"
            for i, j in enumerate(jobs)
        )
        prompt = (
            f"Target roles: {', '.join(roles)}\n"
            f"Keywords: {', '.join(keywords)}\n"
            f"Experience level: {level}\n\n"
            f"Jobs:\n{job_list}\n\n"
            "Return a JSON object with key 'ranked_indices' containing the 0-based indices "
            "of jobs sorted from most to least relevant. Include all jobs."
        )
        try:
            result = self._llm_json(
                "You are a job ranking assistant. Rank jobs by relevance to the candidate's preferences.",
                prompt,
            )
            indices = result.get("ranked_indices", list(range(len(jobs))))
            return [jobs[i] for i in indices if 0 <= i < len(jobs)]
        except Exception:
            return jobs

    def _handle_search(self, msg: BandMessage) -> List[Job]:
        payload = msg.payload
        return self.hunt(
            roles=payload.get("roles", []),
            keywords=payload.get("keywords", []),
            location=payload.get("location", "remote"),
            experience_level=payload.get("experience_level", "mid"),
        )


def _make_app(job_id: int):
    from core.models import Application
    return Application(job_id=job_id)
