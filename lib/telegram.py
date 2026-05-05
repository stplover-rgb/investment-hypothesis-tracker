"""Telegram Bot API 최소 클라이언트 (long polling).

공식 SDK(python-telegram-bot)는 cron/데몬 환경에서 무겁고 의존성이 많아
필요 기능만 requests로 구현. 4096자 제한은 자동 분할.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests

API_BASE = "https://api.telegram.org"
MAX_MSG = 4000  # 안전 마진


@dataclass(frozen=True)
class Update:
    update_id: int
    chat_id: int
    text: str
    user_id: int
    user_name: str


class TelegramClient:
    def __init__(self, token: str, *, request_timeout: float = 60.0):
        if not token:
            raise ValueError("token required")
        self.url = f"{API_BASE}/bot{token}"
        self.request_timeout = request_timeout

    def get_updates(self, offset: int = 0, *, long_poll: int = 25) -> list[Update]:
        resp = requests.get(
            f"{self.url}/getUpdates",
            params={
                "offset": offset,
                "timeout": long_poll,
                "allowed_updates": '["message"]',
            },
            timeout=self.request_timeout + long_poll,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram getUpdates error: {data}")

        updates: list[Update] = []
        for item in data.get("result", []):
            msg = item.get("message")
            if not msg or "from" not in msg:
                continue
            updates.append(
                Update(
                    update_id=item["update_id"],
                    chat_id=msg["chat"]["id"],
                    text=msg.get("text", ""),
                    user_id=msg["from"]["id"],
                    user_name=msg["from"].get("first_name", "?"),
                )
            )
        return updates

    def send_message(
        self,
        chat_id: int,
        text: str,
        *,
        parse_mode: Optional[str] = "Markdown",
        disable_preview: bool = True,
    ) -> None:
        for chunk in self._chunks(text):
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "disable_web_page_preview": disable_preview,
            }
            if parse_mode:
                payload["parse_mode"] = parse_mode
            resp = requests.post(f"{self.url}/sendMessage", json=payload, timeout=self.request_timeout)
            # Markdown 파싱 실패 시 plain text로 폴백
            if resp.status_code == 400 and parse_mode:
                payload.pop("parse_mode", None)
                resp = requests.post(f"{self.url}/sendMessage", json=payload, timeout=self.request_timeout)
            resp.raise_for_status()

    @staticmethod
    def _chunks(text: str):
        if len(text) <= MAX_MSG:
            yield text
            return
        for i in range(0, len(text), MAX_MSG):
            yield text[i:i + MAX_MSG]
