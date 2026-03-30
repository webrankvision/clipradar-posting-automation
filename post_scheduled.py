#!/usr/bin/env python3
"""
Scheduled poster — called by Windows Task Scheduler every 30 minutes.

Checks the queue/ folder for any posts that are due and posts them.
Fully silent when nothing is due. Logs everything to logs/scheduler.log.
"""

import json
import sys
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import config
from scheduler import is_due
from models import ContentPackage, PlatformContent, YoutubeContent
from publishers.zernio import ZernioPublisher
from utils.notify import post_success, post_failed, all_posted

# ── File logger (no console output — this runs silently in background) ────────
log_file = config.LOGS_DIR / "scheduler.log"
logging.basicConfig(
    filename=str(log_file),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
)
log = logging.getLogger(__name__)


def load_content(data: dict) -> ContentPackage:
    c = data["content"]
    return ContentPackage(
        tiktok=PlatformContent(**c["tiktok"]),
        instagram=PlatformContent(**c["instagram"]),
        youtube=YoutubeContent(**c["youtube"]),
        facebook=PlatformContent(**c["facebook"]),
    )


def process_queue():
    pending_files = list(config.QUEUE_DIR.glob("pending_*.json"))

    if not pending_files:
        return  # Nothing queued — exit silently

    log.info(f"Checking {len(pending_files)} queued job(s)...")

    for queue_file in pending_files:
        with open(queue_file, "r", encoding="utf-8") as f:
            job = json.load(f)

        job_id = job["id"]
        video_path = job["video_path"]
        video_name = job.get("original_filename", job_id)
        schedule = job["schedule"]
        posted = job["posted"]
        content = load_content(job)

        anything_posted = False

        for platform, scheduled_iso in schedule.items():
            if posted.get(platform):
                continue  # Already posted

            if not is_due(scheduled_iso):
                continue  # Not time yet

            # Post
            log.info(f"[{job_id}] Posting to {platform}...")
            try:
                publisher = ZernioPublisher(platform)
                result = publisher.post(video_path, content)

                if result.success:
                    log.info(f"[{job_id}] {platform} posted OK — id={result.post_id}")
                    posted[platform] = True
                    job["results"][platform] = {
                        "success": True,
                        "post_id": result.post_id,
                        "url": result.url,
                        "posted_at": datetime.now().isoformat(),
                    }
                    post_success(platform, video_name, result.post_id)
                else:
                    log.error(f"[{job_id}] {platform} failed — {result.error}")
                    job["results"][platform] = {
                        "success": False,
                        "error": result.error,
                        "attempted_at": datetime.now().isoformat(),
                    }
                    post_failed(platform, video_name, result.error)

            except Exception as e:
                log.error(f"[{job_id}] {platform} exception — {e}")
                post_failed(platform, video_name, e)

            anything_posted = True

        # Save updated state back to file
        job["posted"] = posted
        with open(queue_file, "w", encoding="utf-8") as f:
            json.dump(job, f, indent=2, ensure_ascii=False)

        # If all platforms are done, move to completed/
        if all(posted.values()):
            completed_path = config.QUEUE_DIR / "completed" / queue_file.name
            queue_file.rename(completed_path)
            log.info(f"[{job_id}] All platforms posted. Moved to completed/.")
            all_posted(video_name)


if __name__ == "__main__":
    try:
        process_queue()
    except Exception as e:
        log.error(f"Scheduler crashed: {e}")
        sys.exit(1)
