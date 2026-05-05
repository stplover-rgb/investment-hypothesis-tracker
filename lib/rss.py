"""RSS 피드 수집기.

feedparser는 URL 직접 호출 시 타임아웃이 없어 cron이 멈출 수 있다.
그래서 requests로 본문을 받은 뒤 feedparser에 넘긴다.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests
import yaml

USER_AGENT = "investment-hypothesis-tracker/0.1"


@dataclass(frozen=True)
class FeedItem:
    feed_name: str
    title: str
    link: str
    summary: str
    published_at: datetime | None


def load_feeds(path: Path) -> list[tuple[str, str]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [(f["name"], f["url"]) for f in raw.get("feeds", [])]


def _parsed_to_dt(parsed) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        t = parsed.get(key)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    return None


def _fetch(url: str, *, timeout: float = 10.0):
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, */*"},
        )
        resp.raise_for_status()
        return feedparser.parse(resp.content)
    except Exception:
        return None


def fetch_recent(
    feeds: list[tuple[str, str]],
    *,
    hours: int = 24,
    per_feed_limit: int = 20,
) -> list[FeedItem]:
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
    items: list[FeedItem] = []

    for name, url in feeds:
        parsed = _fetch(url)
        if parsed is None:
            continue
        for entry in parsed.entries[:per_feed_limit]:
            published = _parsed_to_dt(entry)
            # 발행일이 없는 피드도 있으니 None은 일단 통과시킨다.
            if published is not None and published < cutoff:
                continue
            items.append(
                FeedItem(
                    feed_name=name,
                    title=entry.get("title", "").strip(),
                    link=entry.get("link", ""),
                    summary=(entry.get("summary", "") or "")[:300],
                    published_at=published,
                )
            )
    items.sort(key=lambda x: x.published_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return items
