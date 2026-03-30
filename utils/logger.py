import json
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

# Ensure stdout/stderr use UTF-8 on Windows (default is cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

console = Console()


def log_campaign(result) -> Path:
    """Save the full campaign result to a JSON log file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_stem = Path(result.video_path).stem
    log_file = config.LOGS_DIR / f"{timestamp}_{video_stem}.json"

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)

    return log_file


def print_analysis(analysis):
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]{analysis.topic}[/bold cyan]\n\n"
        f"[yellow]Category:[/yellow] {analysis.content_category}\n"
        f"[yellow]Emotional leverage:[/yellow] {analysis.emotional_leverage}\n"
        f"[yellow]Main message:[/yellow] {analysis.main_message}\n"
        f"[yellow]Peak quote:[/yellow] [italic]\"{analysis.emotional_peak_quote}\"[/italic]\n"
        f"[yellow]Pain point:[/yellow] {analysis.audience_pain_point}\n"
        f"[yellow]Hook:[/yellow] {analysis.strongest_hook}",
        title="[bold]VIDEO ANALYSIS",
        border_style="cyan"
    ))


def print_content(content):
    platforms = [
        ("TikTok", content.tiktok),
        ("Instagram", content.instagram),
        ("YouTube", content.youtube),
        ("Facebook", content.facebook),
    ]

    for name, pkg in platforms:
        console.print()
        console.print(Panel(
            f"[bold white]{pkg.full_post}[/bold white]",
            title=f"[bold green]{name}",
            border_style="green"
        ))


def print_results(results):
    console.print()
    table = Table(title="POSTING RESULTS", box=box.ROUNDED, border_style="bold")
    table.add_column("Platform", style="cyan", width=12)
    table.add_column("Status", width=10)
    table.add_column("Post ID / Error", style="dim")

    for r in results:
        if r.success:
            status = "[bold green]✓ Posted[/bold green]"
            detail = r.post_id or r.url or "-"
        else:
            status = "[bold red]✗ Failed[/bold red]"
            detail = f"[red]{r.error}[/red]"
        table.add_row(r.platform.capitalize(), status, detail)

    console.print(table)


def step(msg: str):
    console.print(f"\n[bold blue]▶ {msg}[/bold blue]")


def success(msg: str):
    console.print(f"[bold green]✓ {msg}[/bold green]")


def warn(msg: str):
    console.print(f"[bold yellow]⚠ {msg}[/bold yellow]")


def error(msg: str):
    console.print(f"[bold red]✗ {msg}[/bold red]")
