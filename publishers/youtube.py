"""
YouTube Publisher
──────────────────
Uses the YouTube Data API v3 to upload Shorts.
Docs: https://developers.google.com/youtube/v3/guides/uploading_a_video

OAuth Setup (first run only):
  1. Go to https://console.cloud.google.com
  2. Create project → Enable "YouTube Data API v3"
  3. Create OAuth 2.0 credentials (Desktop App)
  4. Download as client_secrets.json → place in posting automation/
  5. First run opens your browser to authorize — token is saved automatically

Subsequent runs use the saved token file (no browser needed).

Shorts requirements:
  - Vertical video (9:16 aspect ratio)
  - Under 60 seconds
  - #Shorts in title or description (added automatically)
"""

import os
import sys
import pickle
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from models import ContentPackage, PostResult
from publishers.base import BasePublisher


class YouTubePublisher(BasePublisher):
    platform_name = "youtube"

    def _get_credentials(self):
        """Load or create OAuth2 credentials."""
        try:
            from google.auth.transport.requests import Request
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ImportError:
            raise ImportError(
                "Google auth libraries not installed. "
                "Run: pip install google-auth google-auth-oauthlib google-api-python-client"
            )

        creds = None
        token_path = config.YOUTUBE_TOKEN_FILE
        secrets_path = config.YOUTUBE_CLIENT_SECRETS_FILE

        if Path(token_path).exists():
            with open(token_path, "rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not Path(secrets_path).exists():
                    raise FileNotFoundError(
                        f"YouTube client_secrets.json not found at '{secrets_path}'. "
                        "Download it from Google Cloud Console and place it in the posting automation folder."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    secrets_path, config.YOUTUBE_SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(token_path, "wb") as f:
                pickle.dump(creds, f)

        return creds

    def post(self, video_path: str, content: ContentPackage) -> PostResult:
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
        except ImportError:
            return self._result(
                False,
                error="google-api-python-client not installed. Run: pip install google-api-python-client"
            )

        try:
            creds = self._get_credentials()
            youtube = build("youtube", "v3", credentials=creds)

            pkg = content.youtube

            # Ensure #Shorts is in the description
            description = pkg.full_post
            if "#Shorts" not in description and "#shorts" not in description:
                description += "\n\n#Shorts"

            title = pkg.title
            # Ensure #Shorts is in title (helps algorithm)
            if "#Shorts" not in title:
                title = title[:57] + " #Shorts" if len(title) > 57 else title + " #Shorts"

            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": pkg.hashtags + ["Shorts"],
                    "categoryId": "22",  # People & Blogs — most common for creators
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False,
                },
            }

            media = MediaFileUpload(
                video_path,
                mimetype="video/mp4",
                resumable=True,
                chunksize=5 * 1024 * 1024,  # 5MB chunks
            )

            request = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media,
            )

            response = None
            while response is None:
                status, response = request.next_chunk()

            video_id = response.get("id", "")
            return self._result(
                True,
                post_id=video_id,
                url=f"https://www.youtube.com/shorts/{video_id}",
            )

        except Exception as e:
            return self._result(False, error=e)
