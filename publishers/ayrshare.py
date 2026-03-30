"""
Ayrshare Publisher
───────────────────
Posts to a single platform via the Ayrshare API.
Ayrshare handles TikTok, Instagram, Facebook, and YouTube — all approved,
no platform-specific developer accounts or OAuth flows needed.

Docs: https://docs.ayrshare.com/rest-api/endpoints/post

Flow per platform (called individually as each scheduled time arrives):
  1. Upload local video file to Ayrshare → get public media URL
  2. POST to /post with platform-specific options
  3. Parse and return result
"""

import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from models import ContentPackage, PostResult
from publishers.base import BasePublisher


class AyrsharePublisher(BasePublisher):

    def __init__(self, platform: str):
        self.platform_name = platform
        self.api_key = config.AYRSHARE_API_KEY
        self.base_url = "https://app.ayrshare.com/api"

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}"}

    def _upload_video(self, video_path: str) -> str:
        """Upload the local video file to Ayrshare and return the public URL."""
        with open(video_path, "rb") as f:
            resp = requests.post(
                f"{self.base_url}/media/upload",
                headers=self._headers(),
                files={"file": (Path(video_path).name, f, "video/mp4")},
                timeout=300,
            )
        resp.raise_for_status()
        data = resp.json()
        url = data.get("url") or data.get("contentUrl")
        if not url:
            raise RuntimeError(f"Ayrshare upload returned no URL: {data}")
        return url

    def _build_post_body(self, media_url: str, content: ContentPackage) -> dict:
        """Build the request body for this platform."""
        platform = self.platform_name

        if platform == "tiktok":
            pkg = content.tiktok
            return {
                "post": pkg.full_post,
                "platforms": ["tiktok"],
                "mediaUrls": [media_url],
            }

        elif platform == "instagram":
            pkg = content.instagram
            return {
                "post": pkg.full_post,
                "platforms": ["instagram"],
                "mediaUrls": [media_url],
                "instagramOptions": {"reels": True},
            }

        elif platform == "facebook":
            pkg = content.facebook
            return {
                "post": pkg.full_post,
                "platforms": ["facebook"],
                "mediaUrls": [media_url],
                "faceBookOptions": {"reels": True},
            }

        elif platform == "youtube":
            pkg = content.youtube
            return {
                "post": pkg.full_post,
                "platforms": ["youtube"],
                "mediaUrls": [media_url],
                "youTubeOptions": {
                    "title": pkg.title,
                    "visibility": "public",
                    "youTubeShorts": True,
                },
            }

        else:
            raise ValueError(f"Unknown platform: {platform}")

    def post(self, video_path: str, content: ContentPackage) -> PostResult:
        try:
            # Step 1: upload video
            media_url = self._upload_video(video_path)

            # Step 2: post to platform
            body = self._build_post_body(media_url, content)
            resp = requests.post(
                f"{self.base_url}/post",
                headers={**self._headers(), "Content-Type": "application/json"},
                json=body,
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()

            # Ayrshare returns per-platform results inside "postIds" or "errors"
            platform_key = self.platform_name
            post_ids = data.get("postIds", [])
            errors = data.get("errors", [])

            # Find result for this platform
            post_id = None
            for item in post_ids:
                if item.get("platform") == platform_key:
                    post_id = item.get("id") or item.get("postId")
                    break

            if errors:
                for err in errors:
                    if err.get("platform") == platform_key:
                        raise RuntimeError(err.get("message", str(err)))

            if post_id or data.get("status") == "success":
                return self._result(True, post_id=str(post_id or data.get("id", "")))

            # Fallback: treat any 200 response without explicit error as success
            return self._result(True, post_id=data.get("id", "posted"))

        except Exception as e:
            return self._result(False, error=e)
