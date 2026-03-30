"""
Telegram Notifications
──────────────────────
Sends a message to your Telegram when a post succeeds, fails, or the
worker crashes. Silently does nothing if credentials aren't set.

Setup (one-time):
  1. Open Telegram → search @BotFather → send /newbot → follow prompts
     → copy the token it gives you → set as TELEGRAM_BOT_TOKEN in Railway
  2. Open Telegram → search @userinfobot → send /start
     → copy your numeric ID → set as TELEGRAM_CHAT_ID in Railway
"""

import requests
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

PLATFORM_EMOJI = {
    "tiktok":    "🎵",
    "instagram": "📸",
    "youtube":   "▶️",
    "facebook":  "👤",
}


def _send(text: str):
    """Fire-and-forget Telegram message. Silent if not configured."""
    token = getattr(config, "TELEGRAM_BOT_TOKEN", "")
    chat_id = getattr(config, "TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception:
        pass  # Never let a notification crash the main pipeline


def post_success(platform: str, video_name: str, post_id: str = ""):
    emoji = PLATFORM_EMOJI.get(platform, "📲")
    detail = f" — id: <code>{post_id}</code>" if post_id else ""
    _send(f"{emoji} <b>Posted to {platform.capitalize()}</b>{detail}\n📹 {video_name}")


def post_failed(platform: str, video_name: str, error: str):
    emoji = PLATFORM_EMOJI.get(platform, "📲")
    _send(
        f"❌ <b>{platform.capitalize()} failed</b>\n"
        f"📹 {video_name}\n"
        f"⚠️ <code>{str(error)[:200]}</code>"
    )


def all_posted(video_name: str):
    _send(f"🎉 <b>All 4 platforms posted!</b>\n📹 {video_name}")


def worker_crashed(error: str):
    _send(f"🔥 <b>ClipRadar worker crashed</b>\n<code>{str(error)[:200]}</code>")


def pipeline_failed(video_name: str, error: str):
    _send(
        f"❌ <b>Pipeline failed</b>\n"
        f"📹 {video_name}\n"
        f"⚠️ <code>{str(error)[:200]}</code>"
    )
