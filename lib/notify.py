"""Notification channels.

지원 채널:
- 파일 로그 (항상)
- Termux 알림 (termux-notification 있을 때만)
- ntfy.sh 푸시 (NTFY_TOPIC env 설정 시)
"""
from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import requests


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


def ntfy_send(title: str, body: str, *, priority: str = "default") -> bool:
    """NTFY_TOPIC 환경변수가 설정돼 있으면 ntfy.sh로 푸시. 없으면 False."""
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        return False
    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
    try:
        requests.post(
            f"{server}/{topic}",
            data=body.encode("utf-8"),
            headers={
                "Title": title.encode("utf-8"),
                "Priority": priority,
            },
            timeout=5,
        )
        return True
    except requests.RequestException:
        return False
