"""
Content Generator
─────────────────
Takes the VideoAnalysis and generates fully optimized, platform-specific content.

Style guide: CLIPRADAR METADATA ENGINE v1.0
Rotation: Each call advances the hook/CTA/hashtag/first-comment indices so no
two consecutive posts use the same style. State persists in logs/rotation_state.json.

Output: ContentPackage with platform-specific captions, CTAs, hashtags, and
first comments (TikTok/IG/FB) ready for Zernio to post.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from models import VideoAnalysis, ContentPackage, PlatformContent, YoutubeContent
from metadata import strategy, rotation

import anthropic


_SYSTEM_PROMPT = f"""You are a world-class content strategist specializing in short-form video distribution for faceless podcast clip creators.

CREATOR PROFILE:
- Niche: {config.BRAND_NICHE}
- Free ebook: "{config.EBOOK_TITLE}" — a system for finding and editing high-performing podcast clips faster
- App: {config.APP_NAME} — helps creators find viral podcast clips instantly
- Audience: content creators, entrepreneurs, social media editors, personal brand builders
- Funnel keyword: "{config.EBOOK_KEYWORD}" — viewers comment this → ManyChat sends them the ebook via DM

THE TWO MASTERS:
Every caption serves the algorithm AND the funnel simultaneously.
1. ALGORITHM — completion rate, shares, saves, SEO keywords, watch-through
2. FUNNEL — driving "{config.EBOOK_KEYWORD}" comments → ManyChat → ebook → ClipRadar

PLATFORM ALGORITHM PRIORITIES (2026):

TIKTOK:
- Completion rate is #1 (70%+ needed for viral push)
- Shares and saves are the strongest engagement signals
- Caption truncates after ~80 chars — the first line IS the caption for most viewers
- TikTok is now a search engine — keywords in captions matter for discovery
- First-hour engagement determines whether the algorithm pushes it wider

INSTAGRAM REELS:
- DM shares are THE #1 signal — content shared via DM gets massive algorithmic boost
- Caption SEO is fully indexable — keywords directly influence Search and Explore
- Saves signal "content worth revisiting" — high-value indicator
- 3-5 hashtags only — classification signals, not discovery levers
- ~125 chars before truncation — hook must land in the preview

YOUTUBE SHORTS:
- Watch-through rate is the single most important metric
- Title + Description SEO is critical — YouTube is a search engine
- First 30 characters of title are indexed first
- Shorts can go viral weeks after posting — evergreen metadata beats timing
- Separate algorithm from long-form — Shorts performance doesn't affect channel

FACEBOOK REELS:
- 50% of feed is now recommended content from accounts users DON'T follow — massive discovery opportunity
- Comments with 5+ words are weighted 3x more than short comments by Facebook's algorithm
- Longer captions that make people click "See More" are flagged as "High Value Content"
- Private shares via Messenger/WhatsApp are the STRONGEST signal
- Facebook audience responds to narrative and story — not just hooks

CAPTION STRUCTURE:

TIKTOK: [Hook] → [Emotional Bridge] → [CTA with SYSTEM] → [Hashtags 3-5]
INSTAGRAM: [SEO-rich hook] → [Shareability trigger] → [Emotional statement] → [CTA with SYSTEM] → [Hashtags 3-5]
YOUTUBE: [Keyword-front-loaded Title] + [Description: link first, then body, then CTA, then hashtags]
FACEBOOK: [Thought-provoking hook — long enough to need "See More"] → [Story/Statement] → [Bridge] → [5+-word CTA with SYSTEM] → [Hashtags 3-5]

CRITICAL CTA RULES:
- "{config.EBOOK_KEYWORD}" appears in EVERY caption and EVERY first comment — no exceptions
- Never say "check out my ebook" or "I have a free resource" — sounds like selling
- Connect the CTA to the video's specific emotional leverage — it must feel EARNED
- The CTA is an OFFER, not a request — "I'll send you..." not "please share"
- Facebook CTAs MUST encourage 5+ word responses: "Comment SYSTEM and tell me [specific thing]..."
- Never beg for engagement — make sharing feel inevitable

SEO KEYWORDS TO WEAVE IN NATURALLY (don't keyword-stuff — one or two per platform):
faceless content, podcast clips, make money online, clipping method, faceless creator, short form content

HASHTAG RULES:
- TikTok: 3-5 max. Excessive hashtags = spam signal. Mix broad + niche.
- Instagram: 3-5. Classification signals, not reach hacks.
- YouTube: 3-5 including #Shorts. Searchability-focused.
- Facebook: 3-5. Topic-specific only.
- NEVER use the same hashtag set across consecutive posts.

FIRST COMMENT (TikTok, Instagram, Facebook only — YouTube API does not support it):
- Auto-posted immediately after publish via Zernio
- Short (1-2 sentences), conversational, personal tone
- Reinforces the SYSTEM CTA but uses DIFFERENT phrasing than the caption
- Feels like a personal nudge, not a copy-paste

OUTPUT: Return ONLY valid JSON. No markdown fences, no explanation, no extra text.
"""


def generate(analysis: VideoAnalysis) -> ContentPackage:
    """Generate full platform content package from video analysis."""
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    # Load rotation state and resolve current selections
    rot_state = rotation.load()
    sel = rotation.current_selections(rot_state)

    analysis_json = json.dumps({
        "topic": analysis.topic,
        "speaker_angle": analysis.speaker_angle,
        "main_message": analysis.main_message,
        "emotional_leverage": analysis.emotional_leverage,
        "emotional_peak_quote": analysis.emotional_peak_quote,
        "strongest_hook": analysis.strongest_hook,
        "key_quotes": analysis.key_quotes,
        "content_category": analysis.content_category,
        "audience_pain_point": analysis.audience_pain_point,
        "transformation_promise": analysis.transformation_promise,
    }, indent=2)

    prompt = f"""VIDEO ANALYSIS:
{analysis_json}

━━ ROTATION SLOT: Post #{sel['post_count'] + 1} ━━
HOOK STYLE FOR THIS POST: {sel['hook_style'].upper().replace('_', ' ')}

Use the items below as STYLE REFERENCES — generate fresh, unique content INSPIRED by this style.
Do NOT copy these verbatim. They set the tone, energy, and structure.

HOOK STYLE EXAMPLES ({sel['hook_style']}):
{chr(10).join(f'  • {h}' for h in sel['hook_examples'][:3])}

BRIDGE EXAMPLE (connect emotion to the system/opportunity):
  • {sel['bridge_example']}

CTA EXAMPLES (pick the energy, rewrite for this specific clip):
  • TikTok style: "{sel['cta_tiktok']}"
  • Instagram style: "{sel['cta_instagram']}"
  • Facebook style: "{sel['cta_facebook']}"

HASHTAG SETS (use these — only swap if a tag is clearly wrong for this clip's topic):
  • TikTok: {' '.join('#' + t for t in sel['hashtags_tiktok'])}
  • Instagram: {' '.join('#' + t for t in sel['hashtags_instagram'])}
  • YouTube: {' '.join('#' + t for t in sel['hashtags_youtube'])}
  • Facebook: {' '.join('#' + t for t in sel['hashtags_facebook'])}

FIRST COMMENT STYLE (generate in this voice — different phrasing from caption CTA):
  • TikTok style: "{sel['first_comment_tiktok']}"
  • Instagram style: "{sel['first_comment_instagram']}"
  • Facebook style: "{sel['first_comment_facebook']}"

━━ PLATFORM REQUIREMENTS ━━

TIKTOK:
- caption: 100-180 chars. First line is the hook — front-load it. Punchy and casual.
- cta: Must contain "SYSTEM". Connect to the specific emotional leverage of this clip.
  Frame as an offer: "Drop SYSTEM below if [specific pain/desire from THIS video]"
- hashtags: Use the TikTok set above (array without #). 3-5 max.
- first_comment: 1-2 sentences. Conversational. Reinforces SYSTEM but different phrasing than cta.
- full_post: caption + "\\n\\n" + cta + "\\n" + hashtags joined with spaces and # prefix

INSTAGRAM:
- caption: 150-280 chars. Open with a searchable keyword naturally woven in.
  Design for DM shares — "Send this to someone who..."
- cta: Must contain "SYSTEM". Slightly more premium tone. "Comment SYSTEM — I'll DM you..."
- hashtags: Use the Instagram set above. 3-5 max.
- first_comment: 1-2 sentences. Warm and direct. Different phrasing from caption cta.
- full_post: caption + "\\n\\n" + cta + "\\n\\n" + hashtags joined with spaces and # prefix

YOUTUBE:
- title: 50-70 chars. Primary keyword in the first 30 chars. Click-worthy and search-optimized.
- caption: 120-200 chars. Keyword-rich. FIRST LINE MUST BE EXACTLY: "Free guide: {config.EBOOK_LINK}"
- cta: Direct, tied to this clip's specific benefit. "Free guide in the description 👇"
- hashtags: Use the YouTube set above. Must include Shorts.
- first_comment: null (YouTube does not support first comment via Zernio API)
- full_post: "Free guide: {config.EBOOK_LINK}\\n\\n" + caption + "\\n\\n" + cta + "\\n\\n" + hashtags joined with spaces and # prefix

FACEBOOK:
- caption: 200-320 chars. MUST be long enough to require "See More" click — this is a positive signal.
  Open with a hook that creates curiosity or light controversy. Then narrative. Then bridge to the system.
- cta: Must contain "SYSTEM". Frame to encourage 5+ word responses (Facebook weights these 3x).
  Example structure: "Comment SYSTEM and tell me [specific question about this clip] — I'll DM you the guide."
- hashtags: Use the Facebook set above. 3-5 max.
- first_comment: 1-2 sentences. Personal and warm. Different phrasing from caption cta.
- full_post: caption + "\\n\\n" + cta + "\\n\\n" + hashtags joined with spaces and # prefix

Return ONLY a valid JSON object. No markdown. No explanation. Just the JSON:
{{
  "tiktok": {{
    "caption": "",
    "hashtags": [],
    "cta": "",
    "first_comment": "",
    "full_post": ""
  }},
  "instagram": {{
    "caption": "",
    "hashtags": [],
    "cta": "",
    "first_comment": "",
    "full_post": ""
  }},
  "youtube": {{
    "title": "",
    "caption": "",
    "hashtags": [],
    "cta": "",
    "first_comment": null,
    "full_post": ""
  }},
  "facebook": {{
    "caption": "",
    "hashtags": [],
    "cta": "",
    "first_comment": "",
    "full_post": ""
  }}
}}"""

    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=3500,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = ""
    for block in response.content:
        if block.type == "text":
            raw = block.text.strip()
            break

    # Strip markdown fences if Claude wraps the JSON
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    data = json.loads(raw)

    # Advance rotation state after successful generation
    rotation.save(rotation.advance(rot_state))

    return ContentPackage(
        tiktok=PlatformContent(**data["tiktok"]),
        instagram=PlatformContent(**data["instagram"]),
        youtube=YoutubeContent(**data["youtube"]),
        facebook=PlatformContent(**data["facebook"]),
    )


def run(analysis: VideoAnalysis) -> ContentPackage:
    from utils.logger import step, success
    step("Generating platform content with Claude Opus...")
    content = generate(analysis)
    success("Content generated for all 4 platforms")
    return content
