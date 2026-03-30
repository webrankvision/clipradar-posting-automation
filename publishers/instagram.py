"""
Instagram Publisher
────────────────────
Uses the Meta Graph API to publish Instagram Reels.
Docs: https://developers.facebook.com/docs/instagram-api/guides/reels-publishing

Flow:
  1. POST /{ig-user-id}/media  (create container, upload video)
  2. Poll container status until FINISHED
  3. POST /{ig-user-id}/media_publish  (publish the container)

Requirements in .env:
  INSTAGRAM_ACCESS_TOKEN  — Page access token with instagram_content_publish permission
  INSTAGRAM_USER_ID       — Instagram Business/Creator account ID

NOTE on video hosting:
  Instagram requires the video to be accessible via a public URL.
  Option A (recommended): Host your videos on S3/Cloudinary and set VIDEO_PUBLIC_URL
  Option B: The system will attempt direct upload via resumable upload flow.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from models import ContentPackage, PostResult
from publishers.base import BasePublisher

import requests


class InstagramPublisher(BasePublisher):
    platform_name = "instagram"

    def __init__(self):
        self.token = config.INSTAGRAM_ACCESS_TOKEN
        self.user_id = config.INSTAGRAM_USER_ID
        self.base = f"{config.META_GRAPH_URL}/{self.user_id}"

    def _params(self, **kwargs):
        return {"access_token": self.token, **kwargs}

    def post(self, video_path: str, content: ContentPackage) -> PostResult:
        try:
            pkg = content.instagram
            caption_text = pkg.full_post
            video_file = Path(video_path)

            # ── Step 1: Upload video and create Reels container ───────────────
            # Instagram requires a video_url. We upload via resumable upload.
            # Start a resumable upload session:
            upload_resp = requests.post(
                f"{config.META_GRAPH_URL}/{self.user_id}/media",
                params=self._params(
                    media_type="REELS",
                    caption=caption_text,
                    share_to_feed=True,
                ),
                files={"video_file": (video_file.name, open(video_path, "rb"), "video/mp4")},
                timeout=300,
            )

            if not upload_resp.ok:
                # Try the URL-based approach (fallback message)
                err = upload_resp.json()
                if "video_url" in str(err):
                    return self._result(
                        False,
                        error=(
                            "Instagram requires a public video URL for Reels. "
                            "Host your video publicly (e.g., S3) and use INSTAGRAM_VIDEO_URL "
                            "in your .env, or use a tool like Cloudinary."
                        )
                    )
                raise RuntimeError(f"Instagram media create failed: {err}")

            container_id = upload_resp.json().get("id")
            if not container_id:
                raise RuntimeError(f"No container ID returned: {upload_resp.json()}")

            # ── Step 2: Poll until container is ready ─────────────────────────
            for attempt in range(30):
                time.sleep(5)
                status_resp = requests.get(
                    f"{config.META_GRAPH_URL}/{container_id}",
                    params=self._params(fields="status_code,status"),
                    timeout=30,
                )
                status_resp.raise_for_status()
                status_data = status_resp.json()
                status_code = status_data.get("status_code", "")

                if status_code == "FINISHED":
                    break
                elif status_code == "ERROR":
                    raise RuntimeError(f"Instagram container error: {status_data}")
            else:
                raise RuntimeError("Instagram container processing timed out")

            # ── Step 3: Publish ───────────────────────────────────────────────
            publish_resp = requests.post(
                f"{self.base}/media_publish",
                params=self._params(creation_id=container_id),
                timeout=30,
            )
            publish_resp.raise_for_status()
            post_data = publish_resp.json()
            post_id = post_data.get("id", container_id)

            return self._result(
                True,
                post_id=post_id,
                url=f"https://www.instagram.com/p/{post_id}/",
            )

        except Exception as e:
            return self._result(False, error=e)
