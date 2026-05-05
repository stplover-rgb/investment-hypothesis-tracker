"""Hypothesis definitions loaded from YAML."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass(frozen=True)
class Hypothesis:
    id: str
    title: str
    corp_name: str
    corp_code: str
    watch_keywords: tuple[str, ...] = ()
    status: str = "active"

    def matches(self, report_nm: str) -> list[str]:
        return [kw for kw in self.watch_keywords if kw in report_nm]


def load_hypotheses(path: Path) -> list[Hypothesis]:
    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or []
    return [
        Hypothesis(
            id=item["id"],
            title=item["title"],
            corp_name=item["corp_name"],
            corp_code=str(item["corp_code"]),
            watch_keywords=tuple(item.get("watch_keywords", [])),
            status=item.get("status", "active"),
        )
        for item in raw
    ]


def active(hypotheses: list[Hypothesis]) -> list[Hypothesis]:
    return [h for h in hypotheses if h.status == "active"]
