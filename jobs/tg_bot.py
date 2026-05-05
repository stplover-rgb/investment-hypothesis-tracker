"""Telegram 봇 데몬 — long polling.

명령어:
  /start       — 환영 + 본인 chat_id 안내
  /help, /도움  — 명령 목록
  /whoami      — 본인 user/chat id
  /가설        — 활성 가설 목록
  /공시 [회사]  — 회사 최근 14일 공시
  /브리핑       — 즉시 모닝 브리핑 실행 후 결과 회신
  /상태        — cron, git, 최근 sync 상태
  /log [N]     — logs/tasks.log 최근 N줄

cron 워치독(crontab.example 참조)이 5분마다 살아있는지 확인 후 살림.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import traceback
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.hypotheses import active, load_hypotheses  # noqa: E402
from lib.telegram import TelegramClient, Update  # noqa: E402

# ------------------------ 명령어 핸들러 ------------------------

HELP_TEXT = (
    "*투자 트래커 봇*\n\n"
    "/help, /도움 — 이 도움말\n"
    "/whoami — 내 chat id\n"
    "/가설 — 활성 가설 목록\n"
    "/공시 회사명 — 최근 14일 공시\n"
    "/브리핑 — 즉시 모닝 브리핑\n"
    "/거래 알림본문 — 알림 텍스트 자동 파싱 + 저장\n"
    "/자산 — 자산 대시보드 (오늘/7일/전체)\n"
    "/오늘 — 오늘 거래 목록\n"
    "/상태 — 시스템 상태\n"
    "/log N — 최근 N줄 로그\n"
)


def cmd_start(_args: str, update: Update) -> str:
    return (
        f"투자 트래커 봇입니다, {update.user_name}님.\n\n"
        f"당신의 `chat_id`: `{update.chat_id}`\n\n"
        f".env의 `ALLOWED_CHAT_IDS` 에 이 ID를 넣으면 봇이 본인만 받습니다.\n\n"
        f"명령은 `/help` 참조."
    )


def cmd_help(_args: str, _update: Update) -> str:
    return HELP_TEXT


def cmd_whoami(_args: str, update: Update) -> str:
    return (
        f"chat_id: `{update.chat_id}`\n"
        f"user_id: `{update.user_id}`\n"
        f"name: {update.user_name}"
    )


def cmd_hypotheses(_args: str, _update: Update) -> str:
    hs = active(load_hypotheses(ROOT / "hypotheses.yaml"))
    if not hs:
        return "활성 가설이 없습니다."
    lines = [f"*활성 가설 {len(hs)}개*"]
    for h in hs:
        lines.append(f"`{h.id}` *{h.corp_name}* — {h.title}")
    return "\n".join(lines)


def cmd_disclosure(args: str, _update: Update) -> str:
    name = args.strip()
    if not name:
        return "사용법: `/공시 회사명`"

    hs = load_hypotheses(ROOT / "hypotheses.yaml")
    target = next((h for h in hs if name in h.corp_name), None)
    if not target:
        return f"가설에 등록된 회사명 중 '{name}'을 찾지 못했습니다.\n`/가설` 으로 등록 회사 확인."

    api_key = os.environ.get("OPENDART_API_KEY")
    if not api_key:
        return "OPENDART_API_KEY 미설정 — .env 확인."

    from lib.opendart import OpenDartClient
    client = OpenDartClient(api_key)
    today = date.today()
    items = client.search_disclosures(target.corp_code, today - timedelta(days=14), today)

    if not items:
        return f"{target.corp_name}: 최근 14일 공시 없음."

    lines = [f"*{target.corp_name} 최근 14일 공시 ({len(items)}건)*"]
    for d in items[:15]:
        lines.append(f"• `{d.rcept_dt}` {d.report_nm}\n  {d.url}")
    return "\n".join(lines)


def cmd_brief(_args: str, _update: Update) -> str:
    from jobs.morning_brief import run as run_brief
    try:
        code = run_brief()
    except Exception as exc:
        return f"❌ 브리핑 실행 중 예외:\n```\n{exc!r}\n```"

    today = date.today().isoformat()
    out = ROOT / "data" / "briefings" / f"{today}.md"
    if code == 0 and out.exists():
        body = out.read_text(encoding="utf-8")
        return body[:3500] + ("\n\n_(잘림)_" if len(body) > 3500 else "")

    # 실패 시 오늘자 로그 끝부분을 그대로 회신해서 즉시 디버그 가능하게
    daily_log = ROOT / "logs" / f"{today}.log"
    if daily_log.exists():
        tail = "\n".join(daily_log.read_text(encoding="utf-8").splitlines()[-10:])
        return f"❌ 브리핑 실패 (exit={code}). 최근 로그:\n```\n{tail}\n```"
    return f"❌ 브리핑 실패 (exit={code}) — 로그 파일도 없음."


def cmd_status(_args: str, _update: Update) -> str:
    cron_alive = subprocess.run(
        ["pgrep", "-x", "crond"], capture_output=True
    ).returncode == 0
    bot_count = len(
        subprocess.run(
            ["pgrep", "-f", "jobs.tg_bot"], capture_output=True, text=True
        ).stdout.strip().splitlines()
    )

    sync_log = ROOT / "logs" / "sync.log"
    last_sync = "(none)"
    if sync_log.exists():
        lines = sync_log.read_text(encoding="utf-8").splitlines()
        if lines:
            last_sync = lines[-1][:80]

    git_head = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True,
    ).stdout.strip() or "?"

    branch = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True,
    ).stdout.strip() or "?"

    return (
        "*시스템 상태*\n"
        f"• crond: {'✅ alive' if cron_alive else '❌ down'}\n"
        f"• bot 프로세스: {bot_count}개\n"
        f"• git: `{branch}` @ `{git_head}`\n"
        f"• 최근 sync: `{last_sync}`"
    )


def cmd_transaction(args: str, _update: Update) -> str:
    text = args.strip()
    if not text:
        return (
            "사용법: `/거래 알림 본문 그대로 붙여넣기`\n\n"
            "예: `/거래 신한카드 12,300원 사용 / 스타벅스 강남점`"
        )

    from lib.finance import Transaction, append_transaction
    from lib.parser import parse_notification

    try:
        t = parse_notification(text)
    except Exception as exc:
        return f"❌ 파싱 실패:\n```\n{exc!r}\n```"

    path = ROOT / "data" / "transactions" / "transactions.jsonl"
    append_transaction(t, path)

    return (
        f"✅ 저장됨\n"
        f"• 종류: `{t.kind}`\n"
        f"• 금액: *{t.amount:,}원*\n"
        f"• 카테고리: {t.category or '-'}\n"
        f"• 상대: {t.counterparty or '-'}\n"
        f"• 계좌: {t.account or '-'}\n"
        f"• 메모: {t.note or '-'}"
    )


def cmd_assets(_args: str, _update: Update) -> str:
    from lib.finance import filter_recent, filter_today, load_transactions, summarize

    path = ROOT / "data" / "transactions" / "transactions.jsonl"
    all_tx = load_transactions(path)
    if not all_tx:
        return "거래 데이터 없음.\n`/거래 알림본문` 으로 입력 시작하세요."

    today = filter_today(all_tx)
    week = filter_recent(all_tx, days=7)
    s_today = summarize(today)
    s_week = summarize(week)
    s_all = summarize(all_tx)

    lines = ["*💰 자산 대시보드*", ""]
    lines.append(f"*오늘* ({len(today)}건)")
    lines.append(f"  수입 +{s_today['income']:,}원")
    lines.append(f"  지출 -{s_today['expense']:,}원")
    lines.append(f"  순변동 *{s_today['net']:+,}원*")
    lines.append("")
    lines.append(f"*최근 7일* ({len(week)}건)")
    lines.append(f"  수입 +{s_week['income']:,}원")
    lines.append(f"  지출 -{s_week['expense']:,}원")
    lines.append(f"  순변동 *{s_week['net']:+,}원*")
    lines.append("")
    lines.append(f"*전체 누적* ({s_all['count']}건)")
    lines.append(f"  순누적 *{s_all['net']:+,}원*")

    if s_week["by_category"]:
        lines.append("")
        lines.append("*최근 7일 카테고리별 지출*")
        for cat, amt in sorted(s_week["by_category"].items(), key=lambda x: -x[1])[:10]:
            lines.append(f"  • {cat}: {amt:,}원")

    return "\n".join(lines)


def cmd_today(_args: str, _update: Update) -> str:
    from lib.finance import filter_today, load_transactions

    path = ROOT / "data" / "transactions" / "transactions.jsonl"
    today_tx = filter_today(load_transactions(path))

    if not today_tx:
        return "오늘 거래 없음."

    lines = [f"*오늘 거래 {len(today_tx)}건*"]
    for t in today_tx:
        time = t.timestamp.split("T")[1][:5] if "T" in t.timestamp else "??:??"
        sign = "-" if t.kind == "expense" else "+"
        cp = t.counterparty or t.account or ""
        cat = f" ({t.category})" if t.category else ""
        lines.append(f"`{time}` {sign}{t.amount:,}원 {cp}{cat}")
    return "\n".join(lines)


def cmd_log(args: str, _update: Update) -> str:
    try:
        n = max(1, min(int(args.strip() or "20"), 100))
    except ValueError:
        n = 20
    log_file = ROOT / "logs" / "tasks.log"
    if not log_file.exists():
        return "로그 파일 없음."
    lines = log_file.read_text(encoding="utf-8").splitlines()[-n:]
    return "```\n" + "\n".join(lines) + "\n```"


COMMANDS = {
    "/start": cmd_start,
    "/help": cmd_help,
    "/도움": cmd_help,
    "/whoami": cmd_whoami,
    "/가설": cmd_hypotheses,
    "/공시": cmd_disclosure,
    "/브리핑": cmd_brief,
    "/거래": cmd_transaction,
    "/자산": cmd_assets,
    "/오늘": cmd_today,
    "/상태": cmd_status,
    "/log": cmd_log,
}


# ------------------------ 인증 + 디스패치 ------------------------

def _allowed_set() -> set[int]:
    raw = os.environ.get("ALLOWED_CHAT_IDS", "").strip()
    if not raw:
        return set()
    return {int(x.strip()) for x in raw.split(",") if x.strip()}


def handle(client: TelegramClient, update: Update, allowed: set[int]) -> None:
    if allowed and update.chat_id not in allowed:
        client.send_message(
            update.chat_id,
            f"권한 없음.\nchat_id `{update.chat_id}` 를 `.env` 의 `ALLOWED_CHAT_IDS` 에 추가하세요.",
        )
        print(f"[deny] chat_id={update.chat_id} user={update.user_name}", flush=True)
        return

    text = (update.text or "").strip()
    if not text.startswith("/"):
        client.send_message(update.chat_id, "명령은 `/` 로 시작합니다. `/help` 참고.")
        return

    parts = text.split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    handler = COMMANDS.get(cmd)
    if not handler:
        client.send_message(update.chat_id, f"알 수 없는 명령: `{cmd}`\n`/help` 참고.")
        return

    try:
        result = handler(args, update)
    except Exception:
        result = "❌ 에러:\n```\n" + traceback.format_exc()[-1500:] + "\n```"
    client.send_message(update.chat_id, result)


# ------------------------ 메인 루프 ------------------------

def main() -> int:
    load_dotenv(ROOT / ".env")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN not set in .env", file=sys.stderr)
        return 1

    allowed = _allowed_set()
    client = TelegramClient(token)
    print(f"[start] bot polling (allowed={allowed or 'ANY'})", flush=True)

    offset = 0
    backoff = 1.0
    while True:
        try:
            updates = client.get_updates(offset=offset)
            backoff = 1.0
            for u in updates:
                offset = u.update_id + 1
                print(f"[{u.user_name}/{u.chat_id}] {u.text}", flush=True)
                handle(client, u, allowed)
        except KeyboardInterrupt:
            print("[stop] interrupt", flush=True)
            return 0
        except Exception as e:
            print(f"[loop-error] {e}; sleep {backoff:.0f}s", flush=True)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60.0)


if __name__ == "__main__":
    sys.exit(main())
