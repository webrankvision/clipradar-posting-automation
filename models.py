from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class VideoAnalysis(BaseModel):
    topic: str
    speaker_angle: str
    main_message: str
    emotional_leverage: str       # The dominant emotion created (e.g., "frustrated ambition")
    emotional_peak_quote: str     # The exact line that hits hardest
    strongest_hook: str           # Best possible opening hook to stop the scroll
    key_quotes: List[str]         # 2-3 most powerful, shareable quotes
    content_category: str         # motivation / discipline / business / mindset / money / success
    audience_pain_point: str      # The specific struggle this addresses
    transformation_promise: str   # What the viewer gains by watching/acting
    transcript: str


class PlatformContent(BaseModel):
    caption: str                  # Full caption text (no hashtags)
    hashtags: List[str]           # Hashtags without #
    cta: str                      # Standalone CTA line
    first_comment: Optional[str] = None  # Auto-posted first comment (TikTok/IG/FB only)
    full_post: str                # Ready-to-paste: caption + cta + hashtags


class YoutubeContent(BaseModel):
    title: str                    # Video title (50-70 chars)
    caption: str                  # Description body
    hashtags: List[str]
    cta: str
    first_comment: Optional[str] = None  # Always None — YouTube API doesn't support first comment
    full_post: str                # Full description ready to paste


class ContentPackage(BaseModel):
    tiktok: PlatformContent
    instagram: PlatformContent
    youtube: YoutubeContent
    facebook: PlatformContent


class PostResult(BaseModel):
    platform: str
    success: bool
    post_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None
    timestamp: str = ""

    def __init__(self, **data):
        if "timestamp" not in data or not data["timestamp"]:
            data["timestamp"] = datetime.now().isoformat()
        super().__init__(**data)


class CampaignResult(BaseModel):
    video_path: str
    analysis: VideoAnalysis
    content: ContentPackage
    results: List[PostResult]
    timestamp: str = ""

    def __init__(self, **data):
        if "timestamp" not in data or not data["timestamp"]:
            data["timestamp"] = datetime.now().isoformat()
        super().__init__(**data)
