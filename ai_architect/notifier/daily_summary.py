"""
Daily Summary
"""

from __future__ import annotations

import os

from .notification import Notification
from .report_formatter import ReportFormatter
from .telegram_notifier import TelegramNotifier


class DailySummary:
    def __init__(self) -> None:
        self.formatter = ReportFormatter()

        env_file = os.getenv(
            "ENV_FILE",
            ".env",
        )

        self.telegram = TelegramNotifier(
            env_file=env_file,
        )

    def send(
        self,
        report: dict,
    ):
        message = self.formatter.format(report)

        notification = Notification(
            message=message,
        )

        return self.telegram.send(
            notification,
        )
