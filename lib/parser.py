"""금융 알림 텍스트 → Transaction 자동 파싱 (LLM 기반).

뱅크샐러드, 신한카드, KB증권 등 한국 금융 앱이 보내는 알림 메시지를
구조화된 거래 데이터로 변환한다.

동작 조건: ANTHROPIC_API_KEY 가 설정돼 있어야 함 (현재는 Anthropic 백엔드 가정).
다른 백엔드 추가 시 lib/llm.py 패턴 따라 분기.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

from lib.finance import Transaction

PARSE_SYSTEM = """당신은 한국 금융 알림 텍스트를 파싱하는 도구다.
입력 텍스트에서 거래 정보를 추출해 JSON 객체로만 출력한다.

스키마:
{
  "kind": "income | expense | transfer | balance | unknown",
  "amount": 정수 (원 단위, 양수만),
  "account": "기관/카드 이름 또는 null (예: 신한카드, 국민은행, KB증권)",
  "counterparty": "거래 상대 또는 null (예: 스타벅스, 홍길동)",
  "category": "식음료 | 교통 | 의료 | 쇼핑 | 주거 | 교육 | 여가 | 의류 | 통신 | 보험 | 급여 | 이자 | 투자 | 기타 | null",
  "note": "한 줄 요약 (한국어)"
}

규칙:
- 카드 결제, 자동이체 출금 → "expense"
- 입금, 환급, 급여 → "income"
- 본인 계좌 간 이동 → "transfer"
- 잔액 안내 (변동 없음) → "balance"
- amount는 항상 양수. 방향은 kind으로 표현.
- 콤마/원 기호는 제거하고 숫자만 추출.
- 정확히 모르겠으면 unknown + null들로.
- JSON만 출력. 코드펜스나 설명 절대 금지."""


def parse_notification(text: str, *, model: str = "claude-haiku-4-5-20251001") -> Transaction:
    """알림 텍스트를 LLM으로 파싱해 Transaction 반환."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set — 알림 자동 파싱은 Anthropic 백엔드 필요")

    from anthropic import Anthropic  # 지연 임포트
    client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model=model,
        max_tokens=400,
        system=PARSE_SYSTEM,
        messages=[{"role": "user", "content": text}],
    )
    raw = "".join(b.text for b in response.content if b.type == "text").strip()

    # 혹시 모를 코드펜스 제거
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:].lstrip()

    parsed = json.loads(raw)

    return Transaction(
        timestamp=datetime.now().isoformat(timespec="seconds"),
        kind=str(parsed.get("kind") or "unknown"),
        amount=int(parsed.get("amount") or 0),
        account=parsed.get("account") or None,
        counterparty=parsed.get("counterparty") or None,
        category=parsed.get("category") or None,
        note=parsed.get("note") or None,
        source="auto",
        raw=text,
    )
