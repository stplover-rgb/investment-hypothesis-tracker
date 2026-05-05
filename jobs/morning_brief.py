"""매일 아침 cron이 실행하는 모닝 브리핑.

- feeds.yaml의 RSS에서 최근 24시간 헤드라인 수집
- Claude Haiku로 한국어 5~7줄 bullet 요약
- 결과를 data/briefings/YYYY-MM-DD.md에 저장
- Termux 알림 + (있으면) ntfy.sh로 푸시
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.llm import summarize_briefing  # noqa: E402
from lib.notify import log_to_file, ntfy_send, termux_notify  # noqa: E402
from lib.rss import FeedItem, fetch_recent, load_feeds  # noqa: E402


def _format_for_llm(items: list[FeedItem], limit: int = 40) -> str:
    return "\n".join(f"[{it.feed_name}] {it.title}" for it in items[:limit] if it.title)


def _format_sources(items: list[FeedItem], limit: int = 40) -> str:
    return "\n".join(f"- [{it.feed_name}] {it.title} ({it.link})" for it in items[:limit] if it.title)


def run(*, hours: int = 24) -> int:
    load_dotenv(ROOT / ".env")

    log_dir = ROOT / "logs"
    feeds_path = ROOT / "feeds.yaml"
    if not feeds_path.exists():
        log_to_file("morning_brief: feeds.yaml not found", log_dir)
        return 1

    feeds = load_feeds(feeds_path)
    items = fetch_recent(feeds, hours=hours)

    if not items:
        log_to_file("morning_brief: no fresh items in last %dh" % hours, log_dir)
        return 0

    headlines = _format_for_llm(items)
    try:
        summary = summarize_briefing(headlines)
    except Exception as exc:
        msg = f"morning_brief: LLM error — {exc}"
        log_to_file(msg, log_dir)
        print(msg, file=sys.stderr)
        return 1

    today = date.today().isoformat()
    out_path = ROOT / "data" / "briefings" / f"{today}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        f"# 모닝 브리핑 {today}\n\n{summary}\n\n---\n\n## 원본 헤드라인\n\n{_format_sources(items)}\n",
        encoding="utf-8",
    )

    log_to_file(f"morning_brief: {len(items)} items → {out_path}", log_dir)
    termux_notify("📰 모닝 브리핑", summary[:200])
    ntfy_send("📰 모닝 브리핑", summary)
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(run())
