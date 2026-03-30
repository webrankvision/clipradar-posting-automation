"""
TikTok Publisher
────────────────
Uses the TikTok Content Posting API v2.
Docs: https://developers.tiktok.com/doc/content-posting-api-get-started

Flow:
  1. POST /v2/post/publish/video/init/  → get upload_url + publish_id
  2. PUT upload_url (chunked binary upload)
  3. GET /v2/post/publish/status/fetch/ → poll until success

Requirements in .env:
  TIKTOK_ACCESS_TOKEN  — OAuth access token with video.publish scope
  TIKTOK_OPEN_ID       — The authenticated user's open_id
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from models import ContentPackage, PostResult
from publishers.base import BasePublisher

import requests


class TikTokPublisher(BasePublisher):
    platform_name = "tiktok"

    def __init__(self):
        self.access_token = config.TIKTOK_ACCESS_TOKEN
        self.open_id = config.TIKTOK_OPEN_ID
        self.base_url = config.TIKTOK_BASE_URL

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

    def post(self, video_path: str, content: ContentPackage) -> PostResult:
        try:
            pkg = content.tiktok
            video_file = Path(video_path)
            file_size = video_file.stat().st_size

            # ── Step 1: Initialize upload ─────────────────────────────────────
            init_body = {
                "post_info": {
                    "title": pkg.full_post[:2200],  # TikTok title max 2200 chars
                    "privacy_level": "PUBLIC_TO_EVERYONE",
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                    "video_cover_timestamp_ms": 1000,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": file_size,
                    "chunk_size": min(file_size, 10 * 1024 * 1024),  # 10MB chunks
                    "total_chunk_count": max(1, -(-file_size // (10 * 1024 * 1024))),
                },
            }

            r = requests.post(
                f"{self.base_url}/post/publish/video/init/",
                headers=self._headers(),
                json=init_body,
                timeout=30,
            )
            r.raise_for_status()
            init_data = r.json()

            if init_data.get("error", {}).get("code", "ok") != "ok":
                raise RuntimeError(f"TikTok init error: {init_data['error']}")

            upload_url = init_data["data"]["upload_url"]
            publish_id = init_data["data"]["publish_id"]

            # ── Step 2: Upload video ──────────────────────────────────────────
            chunk_size = 10 * 1024 * 1024
            with open(video_path, "rb") as f:
                chunk_index = 0
                offset = 0
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    end_offset = offset + len(chunk) - 1
                    headers = {
                        "Content-Range": f"bytes {offset}-{end_offset}/{file_size}",
                        "Content-Type": "video/mp4",
                    }
                    upload_resp = requests.put(
                        upload_url,
                        headers=headers,
                        data=chunk,
                        timeout=120,
                    )
                    if upload_resp.status_code not in (200, 201, 206):
                        raise RuntimeError(
                            f"TikTok upload failed at chunk {chunk_index}: {upload_resp.status_code}"
                        )
                    offset += len(chunk)
                    chunk_index += 1

            # ── Step 3: Poll publish status ───────────────────────────────────
            for _ in range(20):
                time.sleep(5)
                status_resp = requests.post(
                    f"{self.base_url}/post/publish/status/fetch/",
                    headers=self._headers(),
                    json={"publish_id": publish_id},
                    timeout=30,
                )
                status_resp.raise_for_status()
                status_data = status_resp.json()
                status = status_data.get("data", {}).get("status", "")

                if status == "PUBLISH_COMPLETE":
                    post_id = status_data["data"].get("publicaly_available_post_id", [publish_id])
                    return self._result(True, post_id=str(post_id))
                elif status in ("FAILED", "CANCELED"):
                    raise RuntimeError(f"TikTok publish failed: {status_data}")

            return self._result(False, error="TikTok publish timed out after polling")

        except Exception as e:
            return self._result(False, error=e)
