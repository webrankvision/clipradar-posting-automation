"""
Scheduling logic — 2 slots per platform per day, US Eastern Time.

Each platform has two configurable time slots per day (e.g. 11am + 7pm).
When a new video is queued, the scheduler finds the earliest available slot
that is not already taken by a pending post. If both slots for a day are
taken, it rolls to the next day. No two videos ever share a slot.
"""

import json
from datetime import datetime, timedelta, date
from pathlib import Path
import pytz
import sys

sys.path.insert(0, str(Path(__file__).parent))
import config


def _tz():
    return pytz.timezone(config.AUDIENCE_TIMEZONE)


def _load_taken_slots() -> dict[str, list[datetime]]:
    """
    Read all pending queue files and return already-reserved datetimes per platform.
    Slots for already-posted platforms are excluded (they're free again conceptually,
    but we never reuse past times anyway).
    """
    tz = _tz()
    taken: dict[str, list[datetime]] = {p: [] for p in config.DAILY_SLOTS}

    for queue_file in config.QUEUE_DIR.glob("pending_*.json"):
        try:
            with open(queue_file, "r", encoding="utf-8") as f:
                job = json.load(f)
            for platform, iso in job.get("schedule", {}).items():
                if job.get("posted", {}).get(platform):
                    continue
                dt = datetime.fromisoformat(iso)
                if dt.tzinfo is None:
                    dt = tz.localize(dt)
                if platform in taken:
                    taken[platform].append(dt)
        except Exception:
            pass

    return taken


def _slot_datetime(day: date, time_str: str, tz) -> datetime:
    """Build an aware datetime from a date and HH:MM string."""
    h, m = map(int, time_str.split(":"))
    naive = datetime(day.year, day.month, day.day, h, m, 0)
    return tz.localize(naive)


def _is_taken(candidate: datetime, taken_list: list[datetime]) -> bool:
    """A slot is taken if any existing post is within 30 minutes of it."""
    for existing in taken_list:
        if abs((candidate - existing).total_seconds()) < 1800:  # 30 min
            return True
    return False


def next_available_slot(platform: str, taken: dict[str, list[datetime]]) -> datetime:
    """
    Find the earliest available slot for a platform.

    Walks forward day by day. For each day, tries slot 1 then slot 2
    (in chronological order). Returns the first slot that:
      - is in the future
      - is not already taken by a pending post
    """
    tz = _tz()
    now_et = datetime.now(tz)
    today = now_et.date()

    # Sort the two daily slot times chronologically
    slots = sorted(config.DAILY_SLOTS[platform])
    taken_list = taken.get(platform, [])

    for day_offset in range(365):  # look up to 1 year ahead (never hits in practice)
        check_date = today + timedelta(days=day_offset)

        for slot_time in slots:
            candidate = _slot_datetime(check_date, slot_time, tz)

            if candidate <= now_et:
                continue  # Already passed

            if not _is_taken(candidate, taken_list):
                return candidate

    # Unreachable in practice
    raise RuntimeError(f"Could not find available slot for {platform} within 365 days")


def build_schedule(platforms: list[str]) -> dict[str, str]:
    """
    Build a conflict-free schedule for one video across all platforms.
    Reads the current queue to avoid collisions, then registers each
    new slot in memory so that back-to-back calls in the same watcher
    run don't double-book (queue files aren't written yet at that point).
    """
    taken = _load_taken_slots()
    schedule = {}

    for platform in platforms:
        slot = next_available_slot(platform, taken)
        schedule[platform] = slot.isoformat()
        # Register immediately so the next video in this same batch
        # doesn't pick the same slot
        taken.setdefault(platform, []).append(slot)

    return schedule


def is_due(scheduled_iso: str) -> bool:
    """Return True if the scheduled time has arrived or passed."""
    tz = _tz()
    now_et = datetime.now(tz)
    scheduled = datetime.fromisoformat(scheduled_iso)
    if scheduled.tzinfo is None:
        scheduled = tz.localize(scheduled)
    return now_et >= scheduled


def format_schedule(schedule: dict) -> str:
    """Human-readable schedule summary."""
    tz = _tz()
    now_et = datetime.now(tz)
    lines = []
    for platform, iso in schedule.items():
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = tz.localize(dt)
        delta_days = (dt.date() - now_et.date()).days
        if delta_days == 0:
            day_label = "today"
        elif delta_days == 1:
            day_label = "tomorrow"
        else:
            day_label = dt.strftime("%A %b %d")
        lines.append(
            f"  {platform.capitalize():<12} {day_label} at {dt.strftime('%I:%M %p')} ET"
        )
    return "\n".join(lines)
