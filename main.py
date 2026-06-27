#!/usr/bin/env python3
"""Job Hunter — 7-agent AI job search assistant."""

import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box

load_dotenv()

console = Console()


def check_env() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red bold]Error:[/red bold] ANTHROPIC_API_KEY not set.")
        console.print("Copy [dim].env.example[/dim] to [dim].env[/dim] and add your key, or run:")
        console.print("  [cyan]export ANTHROPIC_API_KEY=sk-ant-...[/cyan]")
        sys.exit(1)


def bootstrap():
    from core.database import init_db
    init_db()

    from core.band import Band
    band = Band(verbose=True)

    from agents.job_hunter import JobHunterAgent
    from agents.resume_analyzer import ResumeAnalyzerAgent
    from agents.match_scorer import MatchScorerAgent
    from agents.resume_tailor import ResumeTailorAgent
    from agents.cover_letter_writer import CoverLetterWriterAgent
    from agents.interview_coach import InterviewCoachAgent
    from agents.application_tracker import ApplicationTrackerAgent

    agents = {
        "hunter": JobHunterAgent(band),
        "analyzer": ResumeAnalyzerAgent(band),
        "scorer": MatchScorerAgent(band),
        "tailor": ResumeTailorAgent(band),
        "writer": CoverLetterWriterAgent(band),
        "coach": InterviewCoachAgent(band),
        "tracker": ApplicationTrackerAgent(band),
    }
    return band, agents


def print_banner():
    console.print(Panel(
        "[bold cyan]Job Hunter[/bold cyan] — AI-Powered Job Search Assistant\n"
        "[dim]7 agents · Band communication · Claude-powered[/dim]",
        border_style="cyan",
    ))


def menu_main() -> str:
    console.print("\n[bold]What would you like to do?[/bold]")
    options = [
        ("1", "🔍 Hunt for jobs"),
        ("2", "📄 Analyze my resume"),
        ("3", "🎯 Score job matches"),
        ("4", "🚀 Full workflow (hunt → analyze → score)"),
        ("5", "✏️  Tailor resume for a job"),
        ("6", "✉️  Write application materials"),
        ("7", "🎓 Interview prep"),
        ("8", "📊 View application tracker"),
        ("9", "🔄 Update application status"),
        ("0", "Exit"),
    ]
    for key, label in options:
        console.print(f"  [{key}] {label}")
    return Prompt.ask("\nChoice", choices=[o[0] for o in options])


def prompt_search_prefs() -> dict:
    console.print("\n[bold]Search Preferences[/bold]")
    roles_raw = Prompt.ask("Target roles (comma-separated)", default="Software Engineer")
    keywords_raw = Prompt.ask("Keywords (comma-separated)", default="Python, React")
    location = Prompt.ask("Preferred location", default="Remote")
    level = Prompt.ask("Experience level", choices=["junior", "mid", "senior", "lead"], default="mid")
    return {
        "roles": [r.strip() for r in roles_raw.split(",")],
        "keywords": [k.strip() for k in keywords_raw.split(",")],
        "location": location,
        "experience_level": level,
    }


def prompt_resume_path() -> str:
    while True:
        path = Prompt.ask("Resume path (PDF, DOCX, or TXT)")
        if Path(path).exists():
            return path
        console.print(f"[red]File not found:[/red] {path}")


def pick_job(jobs, prompt_text: str = "Select job number"):
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("#", width=4)
    table.add_column("Title")
    table.add_column("Company")
    table.add_column("Location")
    table.add_column("Score", width=7, justify="center")

    from core.database import get_match
    for i, job in enumerate(jobs, 1):
        match = get_match(job.id) if job.id else None
        score_str = f"{match.score:.0f}%" if match else "—"
        score_color = "green" if (match and match.score >= 70) else ("yellow" if (match and match.score >= 50) else "dim")
        table.add_row(str(i), job.title, job.company, job.location, f"[{score_color}]{score_str}[/{score_color}]")

    console.print(table)
    choices = [str(i) for i in range(1, len(jobs) + 1)]
    idx = int(Prompt.ask(prompt_text, choices=choices)) - 1
    return jobs[idx]


def show_match_results(results):
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    table.add_column("#", width=4)
    table.add_column("Title")
    table.add_column("Company")
    table.add_column("Score", width=7, justify="center")
    table.add_column("Match")
    table.add_column("Top Gap")

    for i, (job, match) in enumerate(results, 1):
        score = match.score
        color = "green" if score >= 70 else ("yellow" if score >= 50 else "red")
        gap = match.skill_gaps[0] if match.skill_gaps else "—"
        table.add_row(
            str(i), job.title, job.company,
            f"[{color}]{score:.0f}%[/{color}]",
            match.recommendation,
            gap,
        )

    console.print("\n[bold cyan]Match Results (ranked)[/bold cyan]")
    console.print(table)


def show_materials(materials, section: Optional[str] = None):
    if section == "resume" or section is None:
        if materials.tailored_resume:
            console.print(Panel(materials.tailored_resume, title="[cyan]Tailored Resume[/cyan]", border_style="cyan"))

    if section == "cover" or section is None:
        if materials.cover_letter:
            console.print(Panel(materials.cover_letter, title="[cyan]Cover Letter[/cyan]", border_style="cyan"))

    if section == "recruiter" or section is None:
        if materials.recruiter_message:
            console.print(Panel(materials.recruiter_message, title="[cyan]Recruiter Message[/cyan]", border_style="cyan"))

    if section == "linkedin" or section is None:
        if materials.linkedin_message:
            console.print(Panel(materials.linkedin_message, title="[cyan]LinkedIn Message[/cyan]", border_style="cyan"))

    if section == "interview" or section is None:
        if materials.interview_questions:
            console.print("\n[bold cyan]Interview Questions[/bold cyan]")
            for i, q in enumerate(materials.interview_questions, 1):
                qtype = q.get("type", "")
                emoji = "🔧" if qtype == "technical" else "🗣️"
                console.print(f"\n[bold]{emoji} Q{i}: {q.get('question', '')}[/bold]")
                if q.get("suggested_answer"):
                    console.print(f"[dim]{q['suggested_answer']}[/dim]")

        if materials.interview_tips:
            console.print(Panel(materials.interview_tips, title="[cyan]Interview Tips[/cyan]", border_style="cyan"))


def save_to_file(materials, job):
    out_dir = Path("outputs")
    out_dir.mkdir(exist_ok=True)
    slug = f"{job.company.replace(' ', '_')}_{job.title.replace(' ', '_')}"[:40]

    if materials.tailored_resume:
        p = out_dir / f"{slug}_resume.txt"
        p.write_text(materials.tailored_resume)
        console.print(f"[dim]Resume saved: {p}[/dim]")

    if materials.cover_letter:
        p = out_dir / f"{slug}_cover_letter.txt"
        p.write_text(materials.cover_letter)
        console.print(f"[dim]Cover letter saved: {p}[/dim]")

    if materials.interview_questions:
        import json
        p = out_dir / f"{slug}_interview.json"
        p.write_text(json.dumps({
            "questions": materials.interview_questions,
            "tips": materials.interview_tips,
        }, indent=2))
        console.print(f"[dim]Interview prep saved: {p}[/dim]")


def run():
    check_env()
    print_banner()

    band, agents = bootstrap()

    hunter = agents["hunter"]
    analyzer = agents["analyzer"]
    scorer = agents["scorer"]
    tailor = agents["tailor"]
    writer = agents["writer"]
    coach = agents["coach"]
    tracker = agents["tracker"]

    current_jobs = []
    current_profile = None
    match_results = []

    # Try loading existing profile from DB
    from core.database import get_latest_profile, get_all_jobs
    current_profile = get_latest_profile()
    if current_profile:
        console.print(f"[dim]Loaded existing profile: {current_profile.name or 'unnamed'}[/dim]")

    while True:
        choice = menu_main()

        if choice == "0":
            console.print("[dim]Goodbye![/dim]")
            break

        elif choice == "1":
            prefs = prompt_search_prefs()
            current_jobs = hunter.hunt(**prefs)
            if current_jobs:
                console.print(f"\n[green]Found {len(current_jobs)} jobs.[/green]")

        elif choice == "2":
            path = prompt_resume_path()
            current_profile = analyzer.analyze(path)
            console.print(f"\n[green]Profile ready:[/green]\n{current_profile.summary()}")

        elif choice == "3":
            if not current_jobs:
                current_jobs = get_all_jobs()
            if not current_jobs:
                console.print("[yellow]No jobs found. Run option 1 first.[/yellow]")
                continue
            if not current_profile:
                console.print("[yellow]No profile loaded. Run option 2 first.[/yellow]")
                continue
            match_results = scorer.score_jobs(current_jobs, current_profile)
            show_match_results(match_results)

        elif choice == "4":
            # Full workflow
            prefs = prompt_search_prefs()
            path = prompt_resume_path()

            current_jobs = hunter.hunt(**prefs)
            if not current_jobs:
                console.print("[yellow]No jobs found. Try different keywords.[/yellow]")
                continue

            current_profile = analyzer.analyze(path)
            match_results = scorer.score_jobs(current_jobs, current_profile)
            show_match_results(match_results)

        elif choice == "5":
            if not current_profile:
                current_profile = get_latest_profile()
            if not current_profile:
                console.print("[yellow]Analyze your resume first (option 2).[/yellow]")
                continue
            jobs = current_jobs or get_all_jobs()
            if not jobs:
                console.print("[yellow]Hunt for jobs first (option 1).[/yellow]")
                continue
            job = pick_job(jobs)
            mats = tailor.tailor(job, current_profile)
            show_materials(mats, "resume")
            if Confirm.ask("Save to file?"):
                save_to_file(mats, job)

        elif choice == "6":
            if not current_profile:
                current_profile = get_latest_profile()
            if not current_profile:
                console.print("[yellow]Analyze your resume first (option 2).[/yellow]")
                continue
            jobs = current_jobs or get_all_jobs()
            if not jobs:
                console.print("[yellow]Hunt for jobs first (option 1).[/yellow]")
                continue
            job = pick_job(jobs)
            mats = writer.write(job, current_profile)
            show_materials(mats, "cover")
            console.print(Panel(mats.recruiter_message, title="[cyan]Recruiter Message[/cyan]", border_style="cyan"))
            console.print(Panel(mats.linkedin_message, title="[cyan]LinkedIn Message[/cyan]", border_style="cyan"))
            if Confirm.ask("Save to file?"):
                save_to_file(mats, job)

        elif choice == "7":
            if not current_profile:
                current_profile = get_latest_profile()
            if not current_profile:
                console.print("[yellow]Analyze your resume first (option 2).[/yellow]")
                continue
            jobs = current_jobs or get_all_jobs()
            if not jobs:
                console.print("[yellow]Hunt for jobs first (option 1).[/yellow]")
                continue
            job = pick_job(jobs)
            mats = coach.prepare(job, current_profile)
            show_materials(mats, "interview")
            if Confirm.ask("Save to file?"):
                save_to_file(mats, job)

        elif choice == "8":
            tracker.show_dashboard()

        elif choice == "9":
            apps = get_all_jobs()
            if not apps:
                console.print("[yellow]No jobs tracked yet.[/yellow]")
                continue
            job = pick_job(apps, "Select job to update")
            statuses = ["discovered", "applied", "interview", "offer", "accepted", "rejected"]
            for i, s in enumerate(statuses, 1):
                console.print(f"  [{i}] {s}")
            idx = int(Prompt.ask("New status", choices=[str(i) for i in range(1, len(statuses)+1)])) - 1
            notes = Prompt.ask("Notes (optional)", default="")
            tracker.update_status(job.id, statuses[idx], notes)


if __name__ == "__main__":
    run()
