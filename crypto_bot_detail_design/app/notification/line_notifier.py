from __future__ import annotations

from datetime import datetime

import requests

from app.database.db import execute
from config import settings


class LineNotifier:
    def __init__(self) -> None:
        self.channel_access_token = settings.line_channel_access_token
        self.user_id = settings.line_user_id
        self.endpoint = "https://api.line.me/v2/bot/message/push"

    def send_text(self, message: str, notification_type: str = "INFO") -> None:
        if not self.channel_access_token or not self.user_id:
            self._record(notification_type, message, "SKIPPED")
            return

        response = requests.post(
            self.endpoint,
            headers={
                "Authorization": f"Bearer {self.channel_access_token}",
                "Content-Type": "application/json",
            },
            json={
                "to": self.user_id,
                "messages": [{"type": "text", "text": message}],
            },
            timeout=10,
        )
        status = "SENT" if response.ok else "FAILED"
        self._record(notification_type, message, status)

    def _record(self, notification_type: str, message: str, status: str) -> None:
        execute(
            """
            INSERT INTO dbo.notifications
            (notification_type, destination, title, message, status, sent_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                notification_type,
                "LINE",
                None,
                message,
                status,
                datetime.now() if status == "SENT" else None,
                datetime.now(),
            ],
        )
