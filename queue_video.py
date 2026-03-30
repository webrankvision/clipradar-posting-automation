#!/usr/bin/env python3
"""
Queue a video for scheduled posting.

Usage:
    python queue_video.py "path/to/video.mp4"

What this does:
  1. Transcribes the video (Whisper)
  2. Analyzes it with Claude Opus
  3. Generates platform content with Claude Opus
  4. Saves everything to queue/ with scheduled posting times
  5. Prints exactly when each platform will post

The actual posting happens automatically via Windows Task Scheduler.
"""

import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import config
from pipeline import analyzer, generator
from scheduler import build_schedule, format_schedule
from utils import logger
from rich.console import Console
from rich.panel import Panel

console = Console()


def main():
    if len(sys.argv) < 2:
        console.print("[red]Usage: python queue_video.py \"path/to/video.mp4\"[/red]")
        sys.exit(1)

    video_path = Path(sys.argv[1])
    if not video_path.exists():
        logger.error(f"File not found: {video_path}")
        sys.exit(1)

    # ── Validate credentials ──────────────────────────────────────────────────
    issues = config.validate()
    if not config.ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set. Edit your .env file.")
        sys.exit(1)
    for issue in issues:
        logger.warn(issue)

    console.print(Panel.fit(
        f"[bold cyan]Queuing:[/bold cyan] {video_path.name}",
        border_style="cyan"
    ))

    # ── Step 1: Analyze ───────────────────────────────────────────────────────
    analysis = analyzer.run(str(video_path))
    logger.print_analysis(analysis)

    # ── Step 2: Generate content ──────────────────────────────────────────────
    content = generator.run(analysis)
    logger.print_content(content)

    # ── Step 3: Calculate posting schedule ───────────────────────────────────
    platforms = []
    if config.ENABLE_TIKTOK:
        platforms.append("tiktok")
    if config.ENABLE_INSTAGRAM:
        platforms.append("instagram")
    if config.ENABLE_YOUTUBE:
        platforms.append("youtube")
    if config.ENABLE_FACEBOOK:
        platforms.append("facebook")

    schedule = build_schedule(platforms)

    # ── Step 4: Save to queue ─────────────────────────────────────────────────
    job_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + video_path.stem[:20]

    queue_entry = {
        "id": job_id,
        "video_path": str(video_path.resolve()),
        "queued_at": datetime.now().isoformat(),
        "analysis": analysis.model_dump(),
        "content": content.model_dump(),
        "schedule": schedule,
        "posted": {p: False for p in platforms},
        "results": {},
    }

    queue_file = config.QUEUE_DIR / f"pending_{job_id}.json"
    with open(queue_file, "w", encoding="utf-8") as f:
        json.dump(queue_entry, f, indent=2, ensure_ascii=False)

    # ── Done ──────────────────────────────────────────────────────────────────
    console.print()
    console.print(Panel(
        f"[bold green]Video queued successfully.[/bold green]\n\n"
        f"[bold]Posting schedule (US Eastern Time):[/bold]\n"
        f"{format_schedule(schedule)}",
        title="SCHEDULED",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
