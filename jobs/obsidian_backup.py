"""Obsidian vault 일일 백업.

OBSIDIAN_VAULT_PATH 환경변수로 vault 경로 지정. 미설정 시 graceful skip.

동작:
- vault 전체를 tar.gz로 압축
- data/backups/obsidian/YYYY-MM-DD.tar.gz 에 저장
- 30일 넘는 백업 자동 삭제
- 같은 날 두 번 돌아도 idempotent (이미 있으면 스킵)
"""
from __future__ import annotations

import os
import sys
import tarfile
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.notify import log_to_file, termux_notify  # noqa: E402

KEEP_DAYS = 30


def run() -> int:
    load_dotenv(ROOT / ".env")
    log_dir = ROOT / "logs"

    raw_path = os.environ.get("OBSIDIAN_VAULT_PATH", "").strip()
    if not raw_path:
        msg = "obsidian_backup: OBSIDIAN_VAULT_PATH 미설정 — 스킵"
        log_to_file(msg, log_dir)
        print(msg)
        return 0

    vault = Path(raw_path).expanduser()
    if not vault.exists() or not vault.is_dir():
        msg = f"obsidian_backup: vault 경로 없음 — {vault}"
        log_to_file(msg, log_dir)
        print(msg, file=sys.stderr)
        return 1

    backup_dir = ROOT / "data" / "backups" / "obsidian"
    backup_dir.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()
    out_path = backup_dir / f"{today}.tar.gz"

    if out_path.exists():
        msg = f"obsidian_backup: 오늘자 이미 존재 — {out_path.name}"
        log_to_file(msg, log_dir)
        print(msg)
        return 0

    print(f"백업 중: {vault} → {out_path}")
    with tarfile.open(out_path, "w:gz") as tar:
        tar.add(vault, arcname=vault.name)

    # 오래된 백업 정리 (KEEP_DAYS 초과)
    backups = sorted(backup_dir.glob("*.tar.gz"), key=lambda p: p.stat().st_mtime)
    for old in backups[:-KEEP_DAYS]:
        old.unlink()
        log_to_file(f"obsidian_backup: 오래된 백업 삭제 — {old.name}", log_dir)

    size_mb = out_path.stat().st_size / 1024 / 1024
    msg = f"obsidian_backup: {size_mb:.1f}MB → {out_path.name}"
    log_to_file(msg, log_dir)
    termux_notify("📓 Obsidian 백업", f"{size_mb:.1f}MB 완료")
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(run())
