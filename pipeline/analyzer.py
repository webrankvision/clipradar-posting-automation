"""
Video Analyzer
──────────────
Step 1: Transcribe the audio with faster-whisper (local, free, accurate)
Step 2: Send transcript to Claude Opus with adaptive thinking for deep content analysis
Returns a VideoAnalysis object used by the generator.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from models import VideoAnalysis

import anthropic


def transcribe(video_path: str) -> tuple[str, float]:
    """
    Transcribe the video audio using faster-whisper.
    Returns (transcript_text, duration_seconds).
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise ImportError(
            "faster-whisper is not installed. Run: pip install faster-whisper"
        )

    model = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")
    segments, info = model.transcribe(video_path, beam_size=5, language="en")

    lines = []
    for seg in segments:
        lines.append(seg.text.strip())

    transcript = " ".join(lines).strip()
    duration = info.duration

    return transcript, duration


def analyze(video_path: str, transcript: str, duration: float) -> VideoAnalysis:
    """
    Use Claude Opus 4.6 with adaptive thinking to deeply analyze the clip.
    Returns a structured VideoAnalysis.
    """
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    filename = Path(video_path).name

    prompt = f"""You are analyzing a short-form podcast speaker clip for a content distribution system.

TRANSCRIPT:
{transcript}

VIDEO METADATA:
- Filename: {filename}
- Duration: {duration:.1f} seconds

CONTEXT:
This is a podcast speaker edit in the motivational / business / mindset / money / discipline / success niche.
The creator's brand is ClipRadar — helping content creators find and post better podcast clips.
Their free lead magnet is an ebook called "Stop Wasting Edits."

YOUR TASK:
Analyze this clip with extreme depth and precision. Extract the following:

1. TOPIC — The specific subject discussed (be specific, not generic)
2. SPEAKER_ANGLE — The speaker's unique stance or perspective on this topic
3. MAIN_MESSAGE — The single core insight or call to action, in one sentence
4. EMOTIONAL_LEVERAGE — The dominant emotion this creates in the viewer. Be specific and creative. Not just "motivating" — think deeper: "frustrated ambition that needs a release valve", "fear of dying having never acted on potential", "envious urgency after seeing someone else succeed", etc.
5. EMOTIONAL_PEAK_QUOTE — The exact line or moment in the transcript that hits hardest emotionally. This is the line that could make someone stop scrolling.
6. STRONGEST_HOOK — The most powerful possible first line to stop someone scrolling on TikTok or Instagram. This can come directly from the transcript or be reframed from it. Must be punchy, vivid, and create immediate curiosity or tension.
7. KEY_QUOTES — 2-3 of the most powerful, shareable, standalone quotes from the transcript
8. CONTENT_CATEGORY — Exactly one of: motivation, discipline, business, mindset, money, success
9. AUDIENCE_PAIN_POINT — The specific struggle or frustration this video addresses
10. TRANSFORMATION_PROMISE — What the viewer will feel, know, or be able to do differently after fully engaging with this content

Return your analysis as a valid JSON object with exactly these keys:
{{
  "topic": "",
  "speaker_angle": "",
  "main_message": "",
  "emotional_leverage": "",
  "emotional_peak_quote": "",
  "strongest_hook": "",
  "key_quotes": ["", ""],
  "content_category": "",
  "audience_pain_point": "",
  "transformation_promise": ""
}}

Return ONLY the JSON object. No explanation, no markdown fences."""

    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=2048,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}]
    )

    raw = ""
    for block in response.content:
        if block.type == "text":
            raw = block.text.strip()
            break

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    data = json.loads(raw)
    data["transcript"] = transcript

    return VideoAnalysis(**data)


def run(video_path: str) -> VideoAnalysis:
    """Full analysis pipeline: transcribe → analyze."""
    from utils.logger import step, success

    step(f"Transcribing: {Path(video_path).name}")
    transcript, duration = transcribe(video_path)
    success(f"Transcribed {duration:.1f}s — {len(transcript.split())} words")

    step("Analyzing content with Claude Opus...")
    analysis = analyze(video_path, transcript, duration)
    success("Analysis complete")

    return analysis
