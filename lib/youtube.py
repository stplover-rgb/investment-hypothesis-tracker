"""유튜브 영상 ID 추출 + 자막 가져오기.

`/링크 [URL]` 명령에서 사용. 자막 없는 영상이나 미지원 언어는 graceful fail.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# 흔한 유튜브 URL 패턴 — youtu.be, youtube.com/watch, /shorts/, /embed/, m.youtube.com
_VIDEO_ID_RE = re.compile(
    r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})"
)


def extract_video_id(url: str) -> str | None:
    """URL에서 영상 ID 추출. 형식 다양해도 대부분 잡힘."""
    if not url:
        return None
    m = _VIDEO_ID_RE.search(url.strip())
    return m.group(1) if m else None


@dataclass
class TranscriptResult:
    text: str
    language: str        # 실제로 가져온 언어 코드
    is_generated: bool   # 자동 생성 자막인지


def fetch_transcript(video_id: str, *, prefer: tuple[str, ...] = ("ko", "en")) -> TranscriptResult | None:
    """자막 텍스트 통째로 반환. 없으면 None.

    한국어 우선, 없으면 영어로 폴백. 자동생성 자막도 OK.
    """
    try:
        from youtube_transcript_api import (
            NoTranscriptFound,
            TranscriptsDisabled,
            YouTubeTranscriptApi,
        )
    except ImportError as exc:
        raise RuntimeError(
            "youtube-transcript-api 미설치. `pip install youtube-transcript-api`"
        ) from exc

    try:
        listing = YouTubeTranscriptApi.list_transcripts(video_id)
    except (TranscriptsDisabled, NoTranscriptFound):
        return None
    except Exception as exc:  # noqa: BLE001
        # 비공개/제한 영상 등
        raise RuntimeError(f"자막 목록 조회 실패: {exc}") from exc

    # 1. 수동 자막 우선 (선호 언어 순)
    for lang in prefer:
        try:
            t = listing.find_manually_created_transcript([lang])
            items = t.fetch()
            return _join(items, lang, generated=False)
        except Exception:  # noqa: BLE001
            continue

    # 2. 자동생성 자막 (선호 언어 순)
    for lang in prefer:
        try:
            t = listing.find_generated_transcript([lang])
            items = t.fetch()
            return _join(items, lang, generated=True)
        except Exception:  # noqa: BLE001
            continue

    # 3. 어떤 언어든 잡히는 거
    try:
        for t in listing:
            items = t.fetch()
            return _join(items, t.language_code, generated=t.is_generated)
    except Exception:  # noqa: BLE001
        pass

    return None


def _join(items, language: str, *, generated: bool) -> TranscriptResult:
    text = " ".join(it.get("text", "").strip() for it in items if it.get("text"))
    return TranscriptResult(text=text, language=language, is_generated=generated)
