#!/usr/bin/env python3
"""
Inbox watcher — runs via cron every 30 minutes on the cloud server.

Watches a Google Drive folder for new video files.
For each new video found:
  1. Downloads it from Google Drive to a local temp file
  2. Runs transcription + AI analysis + content generation
  3. Calculates conflict-free posting schedule
  4. Saves job to queue/
  5. Moves the file in Google Drive to a "processed" subfolder

The user uploads videos from their iPhone using the Google Drive app.
The server picks them up automatically within 30 minutes.

All output goes to logs/watcher.log
"""

import io
import json
import logging
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import config
from pipeline import analyzer, generator
from scheduler import build_schedule

# ── Logger ────────────────────────────────────────────────────────────────────
log_file = config.LOGS_DIR / "watcher.log"
logging.basicConfig(
    filename=str(log_file),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
)
log = logging.getLogger(__name__)


def get_drive_service():
    """Build and return an authenticated Google Drive service."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError:
        raise ImportError(
            "Google API libraries not installed. Run: pip install google-api-python-client google-auth"
        )

    # On Railway: pass the full JSON as GOOGLE_SERVICE_ACCOUNT_JSON env var
    # Locally: use the service-account.json file
    import json as _json
    json_content = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if json_content:
        creds = service_account.Credentials.from_service_account_info(
            _json.loads(json_content),
            scopes=["https://www.googleapis.com/auth/drive"],
        )
    else:
        creds = service_account.Credentials.from_service_account_file(
            config.GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/drive"],
        )
    return build("drive", "v3", credentials=creds)


def get_or_create_processed_folder(service, inbox_folder_id: str) -> str:
    """Return the ID of the 'processed' subfolder, creating it if needed."""
    results = service.files().list(
        q=(
            f"name='processed' and "
            f"'{inbox_folder_id}' in parents and "
            f"mimeType='application/vnd.google-apps.folder' and "
            f"trashed=false"
        ),
        fields="files(id)",
    ).execute()

    files = results.get("files", [])
    if files:
        return files[0]["id"]

    # Create it
    metadata = {
        "name": "processed",
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [inbox_folder_id],
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    log.info("Created 'processed' subfolder in Google Drive.")
    return folder["id"]


def list_inbox_videos(service, inbox_folder_id: str) -> list[dict]:
    """List all video files directly in the inbox folder (not in subfolders)."""
    mime_types = [
        "video/mp4", "video/quicktime", "video/x-msvideo",
        "video/x-matroska", "video/mp4v-es", "video/mpeg",
    ]
    mime_query = " or ".join(f"mimeType='{m}'" for m in mime_types)

    results = service.files().list(
        q=(
            f"({mime_query}) and "
            f"'{inbox_folder_id}' in parents and "
            f"trashed=false"
        ),
        fields="files(id, name, size, createdTime)",
        orderBy="createdTime",  # oldest first = FIFO
    ).execute()

    return results.get("files", [])


def download_video(service, file_id: str, filename: str) -> Path:
    """Download a Drive file to a local temp file. Returns the local path."""
    from googleapiclient.http import MediaIoBaseDownload

    tmp_dir = config.PROCESSING_DIR
    local_path = tmp_dir / filename

    request = service.files().get_media(fileId=file_id)
    with open(local_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

    return local_path


def move_to_processed(service, file_id: str, inbox_folder_id: str, processed_folder_id: str):
    """Move a Drive file from inbox to the processed subfolder."""
    service.files().update(
        fileId=file_id,
        addParents=processed_folder_id,
        removeParents=inbox_folder_id,
        fields="id, parents",
    ).execute()


def get_enabled_platforms() -> list[str]:
    platforms = []
    if config.ENABLE_TIKTOK:
        platforms.append("tiktok")
    if config.ENABLE_INSTAGRAM:
        platforms.append("instagram")
    if config.ENABLE_YOUTUBE:
        platforms.append("youtube")
    if config.ENABLE_FACEBOOK:
        platforms.append("facebook")
    return platforms


def process_video(service, drive_file: dict, inbox_folder_id: str, processed_folder_id: str):
    """Full pipeline for one video: download → analyze → generate → schedule → queue."""
    file_id = drive_file["id"]
    filename = drive_file["name"]
    log.info(f"Processing: {filename}")

    local_path = None
    try:
        # ── Download from Google Drive ────────────────────────────────────────
        log.info(f"Downloading {filename} from Google Drive...")
        local_path = download_video(service, file_id, filename)
        log.info(f"Downloaded to {local_path}")

        # ── Move Drive file to processed/ immediately (claim it) ──────────────
        # Do this before heavy processing so a second watcher run doesn't
        # pick up the same file.
        move_to_processed(service, file_id, inbox_folder_id, processed_folder_id)
        log.info(f"Moved {filename} to processed/ in Drive.")

        # ── Transcribe + analyze ──────────────────────────────────────────────
        log.info("Transcribing and analyzing...")
        analysis = analyzer.run(str(local_path))
        log.info(f"Analysis: {analysis.topic} [{analysis.content_category}]")

        # ── Generate content ──────────────────────────────────────────────────
        log.info("Generating platform content...")
        content = generator.run(analysis)
        log.info("Content generated.")

        # ── Build conflict-free schedule ──────────────────────────────────────
        platforms = get_enabled_platforms()
        schedule = build_schedule(platforms)
        log.info(f"Schedule: { {p: schedule[p][:16] for p in schedule} }")

        # ── Copy video to processed/ local folder for posting ─────────────────
        final_path = config.PROCESSED_DIR / filename
        shutil.copy2(str(local_path), str(final_path))

        # ── Save to queue ─────────────────────────────────────────────────────
        job_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + Path(filename).stem[:20]

        queue_entry = {
            "id": job_id,
            "video_path": str(final_path),
            "original_filename": filename,
            "drive_file_id": file_id,
            "queued_at": datetime.now().isoformat(),
            "analysis": analysis.model_dump(),
            "content": content.model_dump(),
            "schedule": schedule,
            "posted": {p: False for p in platforms},
            "results": {},
        }

        queue_file = config.QUEUE_DIR / f"pending_{job_id}.json"
        with open(queue_file, "w", encoding="utf-8") as f:
            json.dump(queue_entry, f, indent=2, ensure_ascii=False)

        log.info(f"Queued as {queue_file.name}")

    except Exception as e:
        log.error(f"Failed to process {filename}: {e}")

    finally:
        # Clean up the temp processing file
        if local_path and local_path.exists():
            try:
                local_path.unlink()
            except Exception:
                pass


def main():
    if not config.GOOGLE_DRIVE_FOLDER_ID:
        log.error("GOOGLE_DRIVE_FOLDER_ID not set in .env")
        return

    if not config.GOOGLE_SERVICE_ACCOUNT_FILE or not Path(config.GOOGLE_SERVICE_ACCOUNT_FILE).exists():
        log.error(f"Service account file not found: {config.GOOGLE_SERVICE_ACCOUNT_FILE}")
        return

    if not config.ANTHROPIC_API_KEY:
        log.error("ANTHROPIC_API_KEY not set.")
        return

    try:
        service = get_drive_service()
    except Exception as e:
        log.error(f"Could not connect to Google Drive: {e}")
        return

    inbox_folder_id = config.GOOGLE_DRIVE_FOLDER_ID
    processed_folder_id = get_or_create_processed_folder(service, inbox_folder_id)

    videos = list_inbox_videos(service, inbox_folder_id)

    if not videos:
        return  # Nothing to do — exit silently

    log.info(f"Found {len(videos)} video(s) in Google Drive inbox.")

    for video in videos:
        process_video(service, video, inbox_folder_id, processed_folder_id)

    log.info("Inbox scan complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error(f"Watcher crashed: {e}")
        sys.exit(1)
