"""Notification channels.

L2 단계에서는 파일 로그 + Termux 알림(있으면)만 지원.
L3에서 카카오 메모챗/슬랙 등으로 확장 예정.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import subprocess


def log_to_file(message: str, log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {message}\n"
    (log_dir / f"{today}.log").open("a", encoding="utf-8").write(line)


def termux_notify(title: str, content: str) -> bool:
    """Termux:API의 termux-notification가 있으면 호출. 없으면 False."""
    if shutil.which("termux-notification") is None:
        return False
    try:
        subprocess.run(
            ["termux-notification", "--title", title, "--content", content],
            check=True,
            timeout=5,
        )
        return True
    except (subprocess.SubprocessError, OSError):
        return False
