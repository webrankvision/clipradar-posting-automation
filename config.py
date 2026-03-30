import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from this directory
_env_path = Path(__file__).parent / ".env"
load_dotenv(_env_path)


# ── Funnel ────────────────────────────────────────────────────────────────────
EBOOK_TITLE = "Stop Wasting Edits"
EBOOK_KEYWORD = "SYSTEM"          # Comment trigger for DM automation
EBOOK_LINK = os.getenv("EBOOK_LINK", "https://your-ebook-link.com")
APP_NAME = "ClipRadar"
BRAND_NICHE = "podcast speaker edits — motivational, business, mindset, discipline, money, success"

# ── Telegram notifications ────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ── AI ────────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-opus-4-6"
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

# ── Platform toggles ──────────────────────────────────────────────────────────
ENABLE_TIKTOK = os.getenv("ENABLE_TIKTOK", "true").lower() == "true"
ENABLE_INSTAGRAM = os.getenv("ENABLE_INSTAGRAM", "true").lower() == "true"
ENABLE_FACEBOOK = os.getenv("ENABLE_FACEBOOK", "true").lower() == "true"
ENABLE_YOUTUBE = os.getenv("ENABLE_YOUTUBE", "true").lower() == "true"

# ── Zernio (handles TikTok, Instagram, Facebook, YouTube) ─────────────────────
ZERNIO_API_KEY = os.getenv("ZERNIO_API_KEY", "")
ZERNIO_ACCOUNT_IDS: dict[str, str] = {
    "tiktok":    os.getenv("ZERNIO_ACCOUNT_TIKTOK",    ""),
    "instagram": os.getenv("ZERNIO_ACCOUNT_INSTAGRAM", ""),
    "facebook":  os.getenv("ZERNIO_ACCOUNT_FACEBOOK",  ""),
    "youtube":   os.getenv("ZERNIO_ACCOUNT_YOUTUBE",   ""),
}

# ── Google Drive (inbox for videos uploaded from iPhone) ──────────────────────
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")

# ── Scheduling ────────────────────────────────────────────────────────────────
# All times are in US Eastern Time (your audience timezone).
# Each platform has 2 slots per day (slot 1 = earlier, slot 2 = later).
# Edit times in your .env file — format HH:MM (24-hour).
# These are the ONE place to change posting times.
AUDIENCE_TIMEZONE = "US/Eastern"

DAILY_SLOTS: dict[str, list[str]] = {
    #              slot 1 (earlier)                        slot 2 (later)
    "tiktok":    [os.getenv("SCHEDULE_TIKTOK_1",    "11:00"), os.getenv("SCHEDULE_TIKTOK_2",    "19:00")],
    "instagram": [os.getenv("SCHEDULE_INSTAGRAM_1", "09:00"), os.getenv("SCHEDULE_INSTAGRAM_2", "18:00")],
    "youtube":   [os.getenv("SCHEDULE_YOUTUBE_1",   "12:00"), os.getenv("SCHEDULE_YOUTUBE_2",   "17:00")],
    "facebook":  [os.getenv("SCHEDULE_FACEBOOK_1",  "12:00"), os.getenv("SCHEDULE_FACEBOOK_2",  "20:00")],
}

# ── Folders ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent

# On Railway: set DATA_DIR to your volume mount path (e.g. /data)
# Locally: defaults to the project directory
_data_root = Path(os.getenv("DATA_DIR", str(BASE_DIR)))

LOGS_DIR = _data_root / "logs"
LOGS_DIR.mkdir(exist_ok=True)

QUEUE_DIR = _data_root / "queue"
QUEUE_DIR.mkdir(exist_ok=True)
(QUEUE_DIR / "completed").mkdir(exist_ok=True)

INBOX_DIR = _data_root / "inbox"
INBOX_DIR.mkdir(exist_ok=True)

PROCESSED_DIR = _data_root / "processed"
PROCESSED_DIR.mkdir(exist_ok=True)

PROCESSING_DIR = _data_root / "processing"
PROCESSING_DIR.mkdir(exist_ok=True)

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".m4v"}


def validate():
    """Check that required credentials are set."""
    issues = []
    if not ANTHROPIC_API_KEY:
        issues.append("ANTHROPIC_API_KEY is not set")
    if not ZERNIO_API_KEY:
        issues.append("ZERNIO_API_KEY is not set")
    for platform, account_id in ZERNIO_ACCOUNT_IDS.items():
        if not account_id:
            issues.append(f"ZERNIO_ACCOUNT_{platform.upper()} is not set")
    if not GOOGLE_DRIVE_FOLDER_ID:
        issues.append("GOOGLE_DRIVE_FOLDER_ID is not set")
    if not GOOGLE_SERVICE_ACCOUNT_FILE:
        issues.append("GOOGLE_SERVICE_ACCOUNT_FILE is not set")
    return issues
