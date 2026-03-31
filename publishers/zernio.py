"""
Zernio Publisher
────────────────
Posts to a single platform via the Zernio REST API.
One API key handles TikTok, Instagram, Facebook, and YouTube Shorts.

Docs: https://docs.zernio.com
Base URL: https://zernio.com/api/v1
Auth: Bearer sk_... token

Flow:
  1. POST /v1/media/presign → get uploadUrl + publicUrl
  2. PUT video file directly to cloud storage via uploadUrl
  3. POST /v1/posts with mediaItems[{type,url}], platform options, and firstComment
"""

import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from models import ContentPackage, PostResult
from publishers.base import BasePublisher


class ZernioPublisher(BasePublisher):

    BASE_URL = "https://zernio.com/api/v1"

    def __init__(self, platform: str):
        self.platform_name = platform
        self.api_key = config.ZERNIO_API_KEY
        self.account_id = config.ZERNIO_ACCOUNT_IDS.get(platform, "")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _upload_video(self, video_path: str) -> str:
        """
        Upload video via Zernio's presigned URL flow.
        Returns the publicUrl to reference in the post.
        """
        video_file = Path(video_path)
        file_size = video_file.stat().st_size

        _mime_map = {
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
            ".avi": "video/x-msvideo",
            ".mkv": "video/x-matroska",
            ".m4v": "video/mp4",
        }
        mime_type = _mime_map.get(video_file.suffix.lower(), "video/mp4")

        # Step 1: Request presigned upload URL
        resp = requests.post(
            f"{self.BASE_URL}/media/presign",
            headers=self._headers(),
            json={
                "filename": video_file.name,
                "fileSize": file_size,
                "contentType": mime_type,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        upload_url = data["uploadUrl"]
        public_url = data["publicUrl"]

        # Step 2: PUT file directly to cloud storage (no auth header — direct S3/GCS upload)
        with open(video_path, "rb") as f:
            put_resp = requests.put(
                upload_url,
                data=f,
                headers={"Content-Type": mime_type},
                timeout=300,
            )
        put_resp.raise_for_status()

        return public_url

    def _get_caption(self, content: ContentPackage) -> str:
        mapping = {
            "tiktok": content.tiktok.full_post,
            "instagram": content.instagram.full_post,
            "facebook": content.facebook.full_post,
            "youtube": content.youtube.full_post,
        }
        return mapping[self.platform_name]

    def _get_first_comment(self, content: ContentPackage) -> str | None:
        """Zernio supports firstComment on TikTok, Instagram, and Facebook only."""
        if self.platform_name == "tiktok":
            return content.tiktok.first_comment
        if self.platform_name == "instagram":
            return content.instagram.first_comment
        if self.platform_name == "facebook":
            return content.facebook.first_comment
        return None  # YouTube: not supported

    def _platform_options(self, content: ContentPackage) -> dict:
        if self.platform_name == "youtube":
            return {
                "youtubeOptions": {
                    "title": content.youtube.title,
                    "visibility": "public",
                    "shorts": True,
                }
            }
        if self.platform_name == "instagram":
            return {"instagramOptions": {"reels": True}}
        if self.platform_name == "facebook":
            return {"facebookOptions": {"reels": True}}
        return {}

    def post(self, video_path: str, content: ContentPackage) -> PostResult:
        try:
            public_url = self._upload_video(video_path)

            body: dict = {
                "publishNow": True,
                "content": self._get_caption(content),
                "mediaItems": [{"type": "video", "url": public_url}],
                "platforms": [
                    {"platform": self.platform_name, "accountId": self.account_id}
                ],
            }

            body.update(self._platform_options(content))

            first_comment = self._get_first_comment(content)
            if first_comment:
                body["firstComment"] = first_comment

            resp = requests.post(
                f"{self.BASE_URL}/posts",
                headers=self._headers(),
                json=body,
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()

            post_id = str(data.get("_id") or data.get("id", ""))
            url = data.get("platformPostUrl", "")

            return self._result(True, post_id=post_id, url=url)

        except Exception as e:
            return self._result(False, error=e)
