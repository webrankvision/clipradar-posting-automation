"""
Facebook Publisher
───────────────────
Uses the Meta Graph API to publish Facebook Reels.
Docs: https://developers.facebook.com/docs/video-api/reels-api

Flow (Facebook Reels):
  1. POST /{page-id}/video_reels (upload_phase=start) → video_id + upload_url
  2. POST upload_url (binary upload)
  3. POST /{page-id}/video_reels (upload_phase=finish) → publish

Requirements in .env:
  FACEBOOK_PAGE_ACCESS_TOKEN  — Page access token with pages_manage_posts permission
  FACEBOOK_PAGE_ID            — Your Facebook Page ID
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from models import ContentPackage, PostResult
from publishers.base import BasePublisher

import requests


class FacebookPublisher(BasePublisher):
    platform_name = "facebook"

    def __init__(self):
        self.token = config.FACEBOOK_PAGE_ACCESS_TOKEN
        self.page_id = config.FACEBOOK_PAGE_ID
        self.base = f"{config.META_GRAPH_URL}/{self.page_id}"

    def _params(self, **kwargs):
        return {"access_token": self.token, **kwargs}

    def post(self, video_path: str, content: ContentPackage) -> PostResult:
        try:
            pkg = content.facebook
            description = pkg.full_post
            video_file = Path(video_path)
            file_size = video_file.stat().st_size

            # ── Step 1: Start upload session ──────────────────────────────────
            start_resp = requests.post(
                f"{self.base}/video_reels",
                params=self._params(
                    upload_phase="start",
                    file_size=file_size,
                ),
                timeout=30,
            )
            start_resp.raise_for_status()
            start_data = start_resp.json()

            video_id = start_data.get("video_id")
            upload_url = start_data.get("upload_url")

            if not video_id or not upload_url:
                raise RuntimeError(f"Facebook Reels start failed: {start_data}")

            # ── Step 2: Upload binary ─────────────────────────────────────────
            with open(video_path, "rb") as f:
                upload_resp = requests.post(
                    upload_url,
                    headers={
                        "Authorization": f"OAuth {self.token}",
                        "offset": "0",
                        "file_size": str(file_size),
                    },
                    data=f,
                    timeout=300,
                )
            upload_resp.raise_for_status()

            # ── Step 3: Finish and publish ────────────────────────────────────
            finish_resp = requests.post(
                f"{self.base}/video_reels",
                params=self._params(
                    upload_phase="finish",
                    video_id=video_id,
                    video_state="PUBLISHED",
                    description=description,
                    title=description[:100],
                ),
                timeout=60,
            )
            finish_resp.raise_for_status()
            finish_data = finish_resp.json()

            success = finish_data.get("success", False)
            if not success:
                raise RuntimeError(f"Facebook Reels finish failed: {finish_data}")

            return self._result(
                True,
                post_id=video_id,
                url=f"https://www.facebook.com/video/{video_id}/",
            )

        except Exception as e:
            return self._result(False, error=e)
