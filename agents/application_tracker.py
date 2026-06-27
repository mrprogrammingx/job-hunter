from typing import List, Dict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from agents.base_agent import BaseAgent
from core.band import Band
from core.models import BandMessage
from core import database as db

console = Console()

STATUS_COLORS = {
    "discovered": "dim",
    "applied": "blue",
    "interview": "yellow",
    "offer": "green bold",
    "accepted": "green",
    "rejected": "red",
}

STATUS_EMOJI = {
    "discovered": "🔍",
    "applied": "📤",
    "interview": "🗣️",
    "offer": "🎉",
    "accepted": "✅",
    "rejected": "❌",
}


class ApplicationTrackerAgent(BaseAgent):
    """Agent 7 — tracks application pipeline and displays metrics."""

    def __init__(self, band: Band):
        super().__init__(band, "ApplicationTracker")
        band.subscribe("application.update", self._handle_update)
        band.subscribe("tracker.show", self._handle_show)

    def show_dashboard(self) -> None:
        apps = db.get_all_applications()
        if not apps:
            console.print("[yellow]No applications tracked yet.[/yellow]")
            return

        self._print_stats(apps)
        self._print_table(apps)

    def update_status(self, job_id: int, status: str, notes: str = "") -> None:
        valid = {"discovered", "applied", "interview", "offer", "accepted", "rejected"}
        if status not in valid:
            console.print(f"[red]Invalid status. Choose from: {', '.join(valid)}[/red]")
            return
        db.update_application_status(job_id, status, notes)
        emoji = STATUS_EMOJI.get(status, "")
        console.print(f"[green]✓ Job #{job_id} updated to {emoji} {status}[/green]")
        self.band.send(self.name, "status.updated", {"job_id": job_id, "status": status})

    def _print_stats(self, apps: List[Dict]) -> None:
        counts: Dict[str, int] = {}
        for app in apps:
            counts[app["status"]] = counts.get(app["status"], 0) + 1

        total = len(apps)
        applied = sum(counts.get(s, 0) for s in ["applied", "interview", "offer", "accepted"])
        interviews = counts.get("interview", 0) + counts.get("offer", 0) + counts.get("accepted", 0)
        offers = counts.get("offer", 0) + counts.get("accepted", 0)

        stats_lines = [
            f"[bold]Total tracked:[/bold] {total}",
            f"[bold]Applied:[/bold] {applied}",
            f"[bold]Interviews:[/bold] {interviews}",
            f"[bold]Offers:[/bold] {offers}",
        ]
        if applied > 0:
            stats_lines.append(f"[bold]Interview rate:[/bold] {interviews/applied*100:.0f}%")
        if interviews > 0:
            stats_lines.append(f"[bold]Offer rate:[/bold] {offers/interviews*100:.0f}%")

        status_breakdown = "  ".join(
            f"{STATUS_EMOJI.get(s, '')} {s}: {n}" for s, n in sorted(counts.items())
        )
        stats_lines.append(f"\n{status_breakdown}")

        console.print(Panel("\n".join(stats_lines), title="[bold cyan]📊 Job Search Metrics[/bold cyan]", border_style="cyan"))

    def _print_table(self, apps: List[Dict]) -> None:
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Title", min_width=20)
        table.add_column("Company", min_width=15)
        table.add_column("Location", min_width=12)
        table.add_column("Score", width=7, justify="center")
        table.add_column("Status", width=12)
        table.add_column("Notes", min_width=15)

        for app in apps:
            status = app.get("status", "discovered")
            color = STATUS_COLORS.get(status, "white")
            emoji = STATUS_EMOJI.get(status, "")
            score = app.get("match_score", 0)
            score_str = f"{score:.0f}%" if score else "—"
            score_color = "green" if score >= 70 else ("yellow" if score >= 50 else "red")

            table.add_row(
                str(app["job_id"]),
                app.get("title", ""),
                app.get("company", ""),
                app.get("location", "")[:15],
                f"[{score_color}]{score_str}[/{score_color}]",
                f"[{color}]{emoji} {status}[/{color}]",
                (app.get("notes", "") or "")[:30],
            )

        console.print("\n[bold cyan]📋 Application Pipeline[/bold cyan]")
        console.print(table)

    def _handle_update(self, msg: BandMessage) -> None:
        p = msg.payload
        self.update_status(p["job_id"], p["status"], p.get("notes", ""))

    def _handle_show(self, msg: BandMessage) -> None:
        self.show_dashboard()
