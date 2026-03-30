"""
Rotation state tracker — ensures no two consecutive posts use the same style.
State is persisted to logs/rotation_state.json across runs.

Tracked indices (all cycle independently):
  hook_style_index    — which hook category (contrarian / curiosity / identity / shareability / seo)
  cta_index           — which CTA variant from each platform's pool
  hashtag_set_index   — which hashtag set (0/1/2) across all platforms
  first_comment_index — which first comment variant per platform
  post_count          — total posts generated (never resets)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from metadata import strategy

_STATE_FILE = config.LOGS_DIR / "rotation_state.json"

_DEFAULTS = {
    "hook_style_index": 0,
    "cta_index": 0,
    "hashtag_set_index": 0,
    "first_comment_index": 0,
    "post_count": 0,
}


def load() -> dict:
    """Load rotation state from disk. Returns defaults if not found or corrupt."""
    if _STATE_FILE.exists():
        try:
            return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return dict(_DEFAULTS)


def save(state: dict):
    """Persist rotation state to disk."""
    _STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def advance(state: dict) -> dict:
    """Return a new state with all indices incremented by 1 (wrapping)."""
    s = dict(state)
    s["hook_style_index"] = (s["hook_style_index"] + 1) % len(strategy.HOOK_STYLES)
    s["cta_index"] = (s["cta_index"] + 1) % len(strategy.CTAS_TIKTOK)
    s["hashtag_set_index"] = (s["hashtag_set_index"] + 1) % len(strategy.HASHTAG_SETS_TIKTOK)
    s["first_comment_index"] = (s["first_comment_index"] + 1) % len(strategy.FIRST_COMMENTS_TIKTOK)
    s["post_count"] = s["post_count"] + 1
    return s


def current_selections(state: dict) -> dict:
    """Return the resolved values for this rotation slot."""
    hook_style = strategy.HOOK_STYLES[state["hook_style_index"] % len(strategy.HOOK_STYLES)]
    cta_idx = state["cta_index"] % len(strategy.CTAS_TIKTOK)
    hs_idx = state["hashtag_set_index"] % len(strategy.HASHTAG_SETS_TIKTOK)
    fc_idx = state["first_comment_index"] % len(strategy.FIRST_COMMENTS_TIKTOK)

    return {
        "hook_style": hook_style,
        "hook_examples": strategy.HOOK_BANKS[hook_style],
        "bridge_example": strategy.BRIDGES[fc_idx % len(strategy.BRIDGES)],
        "cta_tiktok": strategy.CTAS_TIKTOK[cta_idx],
        "cta_instagram": strategy.CTAS_INSTAGRAM[cta_idx % len(strategy.CTAS_INSTAGRAM)],
        "cta_facebook": strategy.CTAS_FACEBOOK[cta_idx % len(strategy.CTAS_FACEBOOK)],
        "hashtags_tiktok": strategy.HASHTAG_SETS_TIKTOK[hs_idx],
        "hashtags_instagram": strategy.HASHTAG_SETS_INSTAGRAM[hs_idx % len(strategy.HASHTAG_SETS_INSTAGRAM)],
        "hashtags_youtube": strategy.HASHTAG_SETS_YOUTUBE[hs_idx % len(strategy.HASHTAG_SETS_YOUTUBE)],
        "hashtags_facebook": strategy.HASHTAG_SETS_FACEBOOK[hs_idx % len(strategy.HASHTAG_SETS_FACEBOOK)],
        "first_comment_tiktok": strategy.FIRST_COMMENTS_TIKTOK[fc_idx],
        "first_comment_instagram": strategy.FIRST_COMMENTS_INSTAGRAM[fc_idx % len(strategy.FIRST_COMMENTS_INSTAGRAM)],
        "first_comment_facebook": strategy.FIRST_COMMENTS_FACEBOOK[fc_idx % len(strategy.FIRST_COMMENTS_FACEBOOK)],
        "post_count": state["post_count"],
    }
