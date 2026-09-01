"""Notifier Manager."""

from __future__ import annotations

from pathlib import Path

from .models import (
    Notification,
    NotificationLevel,
    NotificationResult,
)
from .telegram_notifier import TelegramNotifier


class NotifierManager:
    def __init__(
        self,
        telegram_env: str | Path,
    ) -> None:
        self.telegram = TelegramNotifier(telegram_env)

    def notify(
        self,
        title: str,
        message: str,
        level: NotificationLevel,
    ) -> NotificationResult:
        notification = Notification(
            title=title,
            message=message,
            level=level,
        )

        return self.telegram.send(notification)

    def success(
        self,
        title: str,
        message: str,
    ) -> NotificationResult:
        return self.notify(
            title,
            message,
            NotificationLevel.SUCCESS,
        )

    def error(
        self,
        title: str,
        message: str,
    ) -> NotificationResult:
        return self.notify(
            title,
            message,
            NotificationLevel.ERROR,
        )

    def info(
        self,
        title: str,
        message: str,
    ) -> NotificationResult:
        return self.notify(
            title,
            message,
            NotificationLevel.INFO,
        )

    def warning(
        self,
        title: str,
        message: str,
    ) -> NotificationResult:
        return self.notify(
            title,
            message,
            NotificationLevel.WARNING,
        )
