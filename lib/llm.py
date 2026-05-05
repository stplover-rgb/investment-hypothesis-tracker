"""LLM 클라이언트 — Anthropic 또는 OpenRouter 백엔드 선택 가능.

LLM_BACKEND 환경변수로 선택:
  - "anthropic" (기본): ANTHROPIC_API_KEY 필요
  - "openrouter":      OPENROUTER_API_KEY 필요

cron이 매일 호출하는 단발성 요약용. 작은/빠른 모델로 비용 최소화.
"""
from __future__ import annotations

import os

import requests

DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"

# OpenRouter 무료 모델 (모델 ID는 가끔 바뀌니 .env에서 OPENROUTER_MODEL로 오버라이드 가능).
# 무료 모델 목록: https://openrouter.ai/models?max_price=0
DEFAULT_OPENROUTER_MODEL = "qwen/qwen-2.5-72b-instruct:free"

# NVIDIA NIM (build.nvidia.com) — OpenAI 호환, 무료 크레딧 제공.
# 모델 카탈로그: https://build.nvidia.com/explore/discover
DEFAULT_NVIDIA_MODEL = "meta/llama-3.3-70b-instruct"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

BRIEFING_SYSTEM = (
    "당신은 한국어 일일 모닝 브리핑 작성자다. "
    "사용자가 출근길에 30초 안에 읽을 수 있게, "
    "핵심 사건/지표를 5~7개 bullet로 정리한다. "
    "각 줄은 한 문장, 40자 이내. 가장 중요한 것부터 위에. "
    "가능하면 숫자(주가/등락률/거래대금)를 포함하라. "
    "헤드라인이 너무 적으면 있는 만큼만 정리한다. "
    "섹션 헤더나 인삿말 없이 bullet만 출력."
)


def _backend() -> str:
    return os.environ.get("LLM_BACKEND", "anthropic").lower().strip()


def summarize_briefing(headlines_text: str, *, max_tokens: int = 800) -> str:
    backend = _backend()
    if backend == "openrouter":
        return _via_openrouter(headlines_text, max_tokens=max_tokens)
    if backend == "nvidia":
        return _via_nvidia(headlines_text, max_tokens=max_tokens)
    if backend == "anthropic":
        return _via_anthropic(headlines_text, max_tokens=max_tokens)
    raise RuntimeError(
        f"unknown LLM_BACKEND: {backend!r} (expected anthropic|openrouter|nvidia)"
    )


def _via_anthropic(headlines_text: str, *, max_tokens: int) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in environment")
    # 지연 임포트 — OpenRouter만 쓰는 사용자는 anthropic 패키지 설치 안 해도 됨
    from anthropic import Anthropic

    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=BRIEFING_SYSTEM,
        messages=[{"role": "user", "content": headlines_text}],
    )
    return "\n".join(b.text for b in response.content if b.type == "text").strip()


def _via_nvidia(headlines_text: str, *, max_tokens: int) -> str:
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY not set in environment")
    model = os.environ.get("NVIDIA_MODEL", DEFAULT_NVIDIA_MODEL)

    resp = requests.post(
        NVIDIA_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "model": model,
            "max_tokens": max_tokens,
            "temperature": 0.4,
            "messages": [
                {"role": "system", "content": BRIEFING_SYSTEM},
                {"role": "user", "content": headlines_text},
            ],
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"unexpected NVIDIA response: {data}") from exc


def _via_openrouter(headlines_text: str, *, max_tokens: int) -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set in environment")
    model = os.environ.get("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)

    resp = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            # OpenRouter 분석용 (선택)
            "HTTP-Referer": "https://github.com/stplover-rgb/investment-hypothesis-tracker",
            "X-Title": "investment-hypothesis-tracker",
        },
        json={
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": BRIEFING_SYSTEM},
                {"role": "user", "content": headlines_text},
            ],
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"unexpected OpenRouter response: {data}") from exc
