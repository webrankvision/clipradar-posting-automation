#!/usr/bin/env python3
"""
ClipRadar — Automated Video Distribution System
────────────────────────────────────────────────
Usage:
    python main.py path/to/your/video.mp4
    python main.py path/to/video.mp4 --dry-run      # analyze + generate only, no posting
    python main.py path/to/video.mp4 --platforms tiktok instagram

Pipeline:
    1. Transcribe audio with Whisper (local)
    2. Analyze content with Claude Opus (extracts emotional leverage, hook, etc.)
    3. Generate platform-specific content (captions, hashtags, CTAs) with Claude Opus
    4. Post to TikTok, Instagram, Facebook, YouTube Shorts in parallel
    5. Log everything to logs/
"""

import argparse
import sys
import concurrent.futures
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

import config
from models import CampaignResult, PostResult
from pipeline import analyzer, generator
from publishers.zernio import ZernioPublisher
from utils import logger


def parse_args():
    parser = argparse.ArgumentParser(
        description="ClipRadar — Automated video distribution for podcast speaker edits"
    )
    parser.add_argument("video", help="Path to the video file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze and generate content only — do not post to any platform",
    )
    parser.add_argument(
        "--platforms",
        nargs="+",
        choices=["tiktok", "instagram", "facebook", "youtube"],
        help="Only post to specific platforms (default: all enabled in .env)",
    )
    parser.add_argument(
        "--skip-analyze",
        action="store_true",
        help="Skip analysis (useful for testing generation step independently)",
    )
    return parser.parse_args()


def get_publishers(platform_filter=None):
    """Return the list of enabled Zernio publishers (one per platform)."""
    all_platforms = [
        ("tiktok",    config.ENABLE_TIKTOK),
        ("instagram", config.ENABLE_INSTAGRAM),
        ("facebook",  config.ENABLE_FACEBOOK),
        ("youtube",   config.ENABLE_YOUTUBE),
    ]
    publishers = []
    for name, enabled in all_platforms:
        if not enabled:
            continue
        if platform_filter and name not in platform_filter:
            continue
        publishers.append(ZernioPublisher(name))
    return publishers


def post_to_platform(publisher, video_path, content):
    """Post to a single platform — wrapped for parallel execution."""
    logger.step(f"Posting to {publisher.platform_name.capitalize()}...")
    result = publisher.post(video_path, content)
    if result.success:
        logger.success(f"{publisher.platform_name.capitalize()} posted → {result.post_id or result.url}")
    else:
        logger.error(f"{publisher.platform_name.capitalize()} failed: {result.error}")
    return result


def main():
    from rich.console import Console
    from rich.panel import Panel
    console = Console()

    console.print(Panel.fit(
        "[bold cyan]ClipRadar Automated Posting System[/bold cyan]\n"
        "Podcast speaker edits → TikTok · Instagram · YouTube · Facebook",
        border_style="cyan"
    ))

    args = parse_args()
    video_path = Path(args.video)

    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        sys.exit(1)

    # ── Credential validation ─────────────────────────────────────────────────
    issues = config.validate()
    if issues:
        console.print("\n[bold yellow]Configuration warnings:[/bold yellow]")
        for issue in issues:
            logger.warn(issue)
        if not config.ANTHROPIC_API_KEY:
            logger.error("ANTHROPIC_API_KEY is required. Set it in your .env file.")
            sys.exit(1)

    # ── Step 1: Analyze ───────────────────────────────────────────────────────
    analysis = analyzer.run(str(video_path))
    logger.print_analysis(analysis)

    # ── Step 2: Generate content ──────────────────────────────────────────────
    content = generator.run(analysis)
    logger.print_content(content)

    if args.dry_run:
        logger.success("Dry run complete. No posts were made.")
        return

    # ── Step 3: Post in parallel ──────────────────────────────────────────────
    publishers = get_publishers(args.platforms)
    if not publishers:
        logger.warn("No platforms enabled or selected. Check your .env settings.")
        return

    console.print(f"\n[bold]Posting to {len(publishers)} platform(s)...[/bold]")

    results: list[PostResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(post_to_platform, pub, str(video_path), content): pub
            for pub in publishers
        }
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    # ── Step 4: Report + Log ──────────────────────────────────────────────────
    logger.print_results(results)

    campaign = CampaignResult(
        video_path=str(video_path),
        analysis=analysis,
        content=content,
        results=results,
    )
    log_file = logger.log_campaign(campaign)
    logger.success(f"Campaign logged to: {log_file}")

    # Summary
    succeeded = sum(1 for r in results if r.success)
    console.print(
        f"\n[bold]{'✓' if succeeded == len(results) else '⚠'} "
        f"{succeeded}/{len(results)} platforms posted successfully.[/bold]"
    )


if __name__ == "__main__":
    main()
