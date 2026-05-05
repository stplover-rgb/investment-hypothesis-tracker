"""Transaction 모델 + JSONL 저장소.

거래 데이터는 append-only JSONL 파일에 저장 (data/transactions/transactions.jsonl).
간단하고, grep/jq로 분석 가능, 백업 쉬움.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

VALID_KINDS = ("income", "expense", "transfer", "balance", "unknown")


@dataclass
class Transaction:
    timestamp: str  # ISO8601
    kind: str       # income | expense | transfer | balance | unknown
    amount: int     # 원 단위, 음수 불가 (kind으로 방향 표현)
    account: Optional[str] = None       # "신한카드", "국민은행" 등
    counterparty: Optional[str] = None  # 거래 상대 ("스타벅스", "홍길동")
    category: Optional[str] = None      # 식음료, 교통 등
    note: Optional[str] = None          # 사람 읽을 한 줄
    source: str = "manual"              # manual | banksalad | sms | bot
    raw: Optional[str] = None           # 원본 텍스트

    def to_dict(self) -> dict:
        return asdict(self)


def append_transaction(t: Transaction, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(t.to_dict(), ensure_ascii=False) + "\n")


def load_transactions(path: Path) -> list[Transaction]:
    if not path.exists():
        return []
    out: list[Transaction] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                out.append(Transaction(**d))
            except (json.JSONDecodeError, TypeError):
                # 깨진 줄은 무시
                continue
    return out


def filter_recent(transactions: list[Transaction], *, days: int) -> list[Transaction]:
    cutoff = datetime.now() - timedelta(days=days)
    return [
        t for t in transactions
        if _parse_ts(t.timestamp) >= cutoff
    ]


def filter_today(transactions: list[Transaction]) -> list[Transaction]:
    today = date.today().isoformat()
    return [t for t in transactions if t.timestamp.startswith(today)]


def summarize(transactions: list[Transaction]) -> dict:
    income = sum(t.amount for t in transactions if t.kind == "income")
    expense = sum(t.amount for t in transactions if t.kind == "expense")
    by_category: dict[str, int] = {}
    for t in transactions:
        if t.kind == "expense" and t.category:
            by_category[t.category] = by_category.get(t.category, 0) + t.amount
    return {
        "income": income,
        "expense": expense,
        "net": income - expense,
        "by_category": by_category,
        "count": len(transactions),
    }


def _parse_ts(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return datetime.min
