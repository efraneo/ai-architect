"""
=========================================================
Telegram Notifier
=========================================================
"""

from __future__ import annotations

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from .models import (
    Notification,
    NotificationResult,
)


class TelegramNotifier:
    def __init__(
        self,
        env_file: str | Path,
    ) -> None:

        load_dotenv(env_file)

        self.token = os.getenv("TELEGRAM_BOT_TOKEN")

        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def send(
        self,
        notification: Notification,
    ) -> NotificationResult:

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"

        text = f"🤖 {notification.title}\n\n{notification.message}"

        response = requests.post(
            url,
            json={
                "chat_id": self.chat_id,
                "text": text,
            },
            timeout=20,
        )

        return NotificationResult(
            success=response.ok,
            provider="telegram",
            response=response.text,
        )
