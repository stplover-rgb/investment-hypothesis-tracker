"""Claude API 클라이언트.

cron이 매일 호출하는 단발성 요약용. Haiku 4.5로 비용/지연 최소화.
"""
from __future__ import annotations

import os

from anthropic import Anthropic

DEFAULT_MODEL = "claude-haiku-4-5-20251001"

BRIEFING_SYSTEM = (
    "당신은 한국어 일일 모닝 브리핑 작성자다. "
    "사용자가 출근길에 30초 안에 읽을 수 있게, "
    "핵심 사건/지표를 5~7개 bullet로 정리한다. "
    "각 줄은 한 문장, 40자 이내. 가장 중요한 것부터 위에. "
    "가능하면 숫자(주가/등락률/거래대금)를 포함하라. "
    "헤드라인이 너무 적으면 있는 만큼만 정리한다. "
    "섹션 헤더나 인삿말 없이 bullet만 출력."
)


def _client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in environment")
    return Anthropic(api_key=api_key)


def summarize_briefing(
    headlines_text: str,
    *,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 800,
) -> str:
    client = _client()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=BRIEFING_SYSTEM,
        messages=[{"role": "user", "content": headlines_text}],
    )
    parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(parts).strip()
