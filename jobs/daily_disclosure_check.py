"""매일 실행되는 공시 체크.

- 모든 active 가설에 대해 어제~오늘 공시를 가져온다
- 이미 처리한 rcept_no는 state 파일로 중복 제거
- 키워드 매칭이 있으면 알림 채널로 전달
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.hypotheses import Hypothesis, active, load_hypotheses  # noqa: E402
from lib.notify import log_to_file, termux_notify  # noqa: E402
from lib.opendart import Disclosure, OpenDartClient  # noqa: E402


def _load_seen(state_path: Path) -> set[str]:
    if not state_path.exists():
        return set()
    return set(json.loads(state_path.read_text(encoding="utf-8")))


def _save_seen(state_path: Path, seen: set[str]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(sorted(seen)), encoding="utf-8")


def _format(hypothesis: Hypothesis, disclosure: Disclosure, matched: list[str]) -> str:
    kw = ",".join(matched) if matched else "(키워드 미일치)"
    return (
        f"[{hypothesis.id}] {hypothesis.corp_name} | {disclosure.report_nm}"
        f" | 키워드: {kw} | {disclosure.url}"
    )


def run(*, lookback_days: int = 1) -> int:
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("OPENDART_API_KEY")
    if not api_key:
        print("OPENDART_API_KEY not set", file=sys.stderr)
        return 1

    data_dir = Path(os.environ.get("DATA_DIR", ROOT / "data"))
    state_path = data_dir / "state" / "seen_disclosures.json"
    log_dir = data_dir.parent / "logs"

    hypotheses = active(load_hypotheses(ROOT / "hypotheses.yaml"))
    if not hypotheses:
        log_to_file("no active hypotheses", log_dir)
        return 0

    client = OpenDartClient(api_key)
    seen = _load_seen(state_path)
    today = date.today()
    since = today - timedelta(days=lookback_days)

    matches = 0
    for h in hypotheses:
        try:
            disclosures = client.search_disclosures(h.corp_code, since, today)
        except Exception as exc:
            log_to_file(f"ERROR fetching {h.corp_name}: {exc}", log_dir)
            continue

        for d in disclosures:
            if d.rcept_no in seen:
                continue
            seen.add(d.rcept_no)
            matched = h.matches(d.report_nm)
            # 키워드가 정의되어 있는데 매치 0이면 무시. 아예 비어있으면 모두 통과.
            if h.watch_keywords and not matched:
                continue
            line = _format(h, d, matched)
            log_to_file(line, log_dir)
            termux_notify(f"[{h.id}] {h.corp_name}", d.report_nm)
            print(line)
            matches += 1

    _save_seen(state_path, seen)
    log_to_file(f"run complete: {matches} new alerts", log_dir)
    return 0


if __name__ == "__main__":
    sys.exit(run())
