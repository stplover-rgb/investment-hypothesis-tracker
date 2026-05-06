"""LLM 클라이언트 — Anthropic / OpenRouter / NVIDIA / Gemini 백엔드 선택.

LLM_BACKEND 환경변수로 선택. 두 가지 진입점:
- summarize_briefing(text)   : 한 번에 한국어 brief 한 덩어리
- chat(messages)             : 멀티턴 대화

내부적으로 _call(messages, system) 한 곳에서 백엔드 분기.
"""
from __future__ import annotations

import os

import requests

DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_OPENROUTER_MODEL = "qwen/qwen-2.5-72b-instruct:free"
DEFAULT_NVIDIA_MODEL = "meta/llama-3.3-70b-instruct"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

BRIEFING_SYSTEM = (
    "당신은 한국어 일일 모닝 브리핑 작성자다. "
    "사용자가 출근길에 30초 안에 읽을 수 있게, "
    "핵심 사건/지표를 5~7개 bullet로 정리한다. "
    "각 줄은 한 문장, 40자 이내. 가장 중요한 것부터 위에. "
    "가능하면 숫자(주가/등락률/거래대금)를 포함하라. "
    "헤드라인이 너무 적으면 있는 만큼만 정리한다. "
    "섹션 헤더나 인삿말 없이 bullet만 출력."
)

CHAT_SYSTEM = (
    "당신은 박동은님의 개인 비서이자 투자 트래커 봇입니다.\n"
    "\n"
    "원칙:\n"
    "- 한국어로 자연스럽고 간결하게 답변\n"
    "- 답변은 텔레그램 채팅에 맞게 짧게 — 보통 1~5줄, 길어도 10줄 이내\n"
    "- 투자/시장/거시경제 질문은 전문적이면서도 균형 잡힌 시각으로\n"
    "- 모르는 것은 모른다고 솔직히 (특히 실시간 시세, 미래 예측)\n"
    "- 일반 대화도 자연스럽게\n"
    "- 마크다운(*굵게*, `코드`)은 가볍게 사용 가능\n"
    "\n"
    "추가 도구 (사용자가 슬래시 명령으로 호출):\n"
    "- /가설 활성 가설 목록\n"
    "- /공시 회사명 — 최근 14일 공시\n"
    "- /브리핑 — 즉시 모닝 브리핑\n"
    "- /링크 URL — 유튜브 영상 자막 요약\n"
    "- /상태 — 시스템 상태\n"
    "필요하다면 사용자에게 위 명령을 안내해도 좋다."
)

YOUTUBE_SYSTEM = (
    "당신은 한국 투자/경제 유튜브 영상의 자막을 요약하는 도구입니다.\n"
    "\n"
    "입력은 영상 자막 텍스트 (자동생성 자막 포함). 출력 형식 — Markdown:\n"
    "\n"
    "*핵심 5~7줄*\n"
    "- 가장 중요한 사실/주장부터, 각 줄 40자 이내\n"
    "- 구체적 숫자/지표 있으면 포함\n"
    "\n"
    "*언급 종목/티커*\n"
    "- 한국 종목명 + 미국 티커 + ETF 등 (있으면)\n"
    "- 없으면 '없음'\n"
    "\n"
    "*주제 키워드*\n"
    "- 매크로/산업/정책 등 3~5개 태그\n"
    "\n"
    "*추천도*\n"
    "- 1~5점 (시간 투자 가치) + 한 문장 이유\n"
    "\n"
    "주의:\n"
    "- 자동생성 자막은 종목명 오타가 많음 — 맥락으로 보정해서 추정\n"
    "- 잘 모르는 부분은 추측하지 말고 생략\n"
    "- 헤더/인삿말 없이 바로 본문 시작"
)


def _backend() -> str:
    return os.environ.get("LLM_BACKEND", "anthropic").lower().strip()


# ---------- 백엔드별 transport ----------

def _call_anthropic(messages: list[dict], system: str, *, max_tokens: int) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in environment")
    from anthropic import Anthropic  # 지연 임포트
    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    )
    return "\n".join(b.text for b in response.content if b.type == "text").strip()


def _call_openrouter(messages: list[dict], system: str, *, max_tokens: int) -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set in environment")
    model = os.environ.get("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)
    full = [{"role": "system", "content": system}, *messages]
    resp = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/stplover-rgb/investment-hypothesis-tracker",
            "X-Title": "investment-hypothesis-tracker",
        },
        json={"model": model, "max_tokens": max_tokens, "messages": full},
        timeout=60,
    )
    if not resp.ok:
        body = (resp.text or "(empty)")[:500]
        raise RuntimeError(
            f"OpenRouter HTTP {resp.status_code} {resp.reason} | model={model} | body: {body}"
        )
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"unexpected OpenRouter response: {data}") from exc


def _call_nvidia(messages: list[dict], system: str, *, max_tokens: int) -> str:
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY not set in environment")
    model = os.environ.get("NVIDIA_MODEL", DEFAULT_NVIDIA_MODEL)
    full = [{"role": "system", "content": system}, *messages]
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
            "messages": full,
        },
        timeout=60,
    )
    if not resp.ok:
        body = (resp.text or "(empty)")[:500]
        raise RuntimeError(
            f"NVIDIA HTTP {resp.status_code} {resp.reason} | model={model} | body: {body}"
        )
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"unexpected NVIDIA response: {data}") from exc


def _call_gemini(messages: list[dict], system: str, *, max_tokens: int) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment")
    model = os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)

    # OpenAI 포맷 → Gemini 포맷 변환
    contents = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})

    resp = requests.post(
        f"{GEMINI_BASE_URL}/{model}:generateContent",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        json={
            "system_instruction": {"parts": [{"text": system}]},
            "contents": contents,
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.4},
        },
        timeout=60,
    )
    if not resp.ok:
        body = (resp.text or "(empty)")[:500]
        raise RuntimeError(
            f"Gemini HTTP {resp.status_code} {resp.reason} | model={model} | body: {body}"
        )
    data = resp.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts).strip()
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"unexpected Gemini response: {data}") from exc


def _call(messages: list[dict], system: str, *, max_tokens: int) -> str:
    backend = _backend()
    if backend == "anthropic":
        return _call_anthropic(messages, system, max_tokens=max_tokens)
    if backend == "openrouter":
        return _call_openrouter(messages, system, max_tokens=max_tokens)
    if backend == "nvidia":
        return _call_nvidia(messages, system, max_tokens=max_tokens)
    if backend == "gemini":
        return _call_gemini(messages, system, max_tokens=max_tokens)
    raise RuntimeError(
        f"unknown LLM_BACKEND: {backend!r} "
        f"(expected anthropic|openrouter|nvidia|gemini)"
    )


# ---------- 진입점 ----------

def summarize_briefing(headlines_text: str, *, max_tokens: int = 800) -> str:
    return _call(
        [{"role": "user", "content": headlines_text}],
        system=BRIEFING_SYSTEM,
        max_tokens=max_tokens,
    )


def chat(messages: list[dict], *, max_tokens: int = 1000) -> str:
    """멀티턴 대화. messages는 [{role: "user"|"assistant", content: str}] 리스트."""
    return _call(messages, system=CHAT_SYSTEM, max_tokens=max_tokens)


def summarize_youtube(transcript: str, *, max_tokens: int = 1200) -> str:
    """유튜브 자막 → 구조화된 한국어 요약. transcript은 30000자 초과시 잘라냄."""
    truncated = transcript[:30000]
    return _call(
        [{"role": "user", "content": truncated}],
        system=YOUTUBE_SYSTEM,
        max_tokens=max_tokens,
    )
