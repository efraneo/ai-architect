"""Notifier Models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class NotificationLevel(StrEnum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(slots=True)
class Notification:
    title: str
    message: str
    level: NotificationLevel
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class NotificationResult:
    success: bool
    provider: str
    response: str = ""
