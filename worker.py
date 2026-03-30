#!/usr/bin/env python3
"""
ClipRadar — Railway Worker
──────────────────────────
Runs continuously on the cloud server.
Every 30 minutes:
  1. Checks Google Drive inbox for new videos (watch_inbox)
  2. Checks the queue for posts that are due and sends them (post_scheduled)

This is the entry point Railway starts and keeps running 24/7.
"""

import time
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config

# ── Logger ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Railway captures stdout
        logging.FileHandler(str(config.LOGS_DIR / "worker.log")),
    ]
)
log = logging.getLogger(__name__)

INTERVAL_SECONDS = 30 * 60  # 30 minutes


def run_cycle():
    """Run one full watch + post cycle."""

    # ── 1. Check Google Drive for new videos ──────────────────────────────────
    try:
        log.info("── Checking Google Drive inbox...")
        import watch_inbox
        watch_inbox.main()
        log.info("── Drive check complete.")
    except Exception as e:
        log.error(f"watch_inbox error: {e}")

    # ── 2. Post anything that is due ──────────────────────────────────────────
    try:
        log.info("── Checking post queue...")
        import post_scheduled
        post_scheduled.process_queue()
        log.info("── Queue check complete.")
    except Exception as e:
        log.error(f"post_scheduled error: {e}")


if __name__ == "__main__":
    log.info("ClipRadar worker starting...")
    log.info(f"Running every {INTERVAL_SECONDS // 60} minutes.")

    # Validate credentials on startup
    issues = config.validate()
    if issues:
        for issue in issues:
            log.warning(f"Config warning: {issue}")

    # Run immediately on startup, then loop
    while True:
        try:
            run_cycle()
        except Exception as e:
            log.error(f"Cycle crashed: {e}")

        log.info(f"Sleeping {INTERVAL_SECONDS // 60} minutes...")
        time.sleep(INTERVAL_SECONDS)
