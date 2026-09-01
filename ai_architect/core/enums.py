"""
=========================================================
Global Enums

Shared Enumerations
=========================================================
"""

from __future__ import annotations

from enum import StrEnum


class Status(StrEnum):
    PENDING = "PENDING"

    RUNNING = "RUNNING"

    COMPLETED = "COMPLETED"

    FAILED = "FAILED"

    CANCELLED = "CANCELLED"

    SKIPPED = "SKIPPED"


class Priority(StrEnum):
    LOW = "LOW"

    MEDIUM = "MEDIUM"

    HIGH = "HIGH"

    CRITICAL = "CRITICAL"


class Decision(StrEnum):
    ACCEPT = "ACCEPT"

    RETRY = "RETRY"

    REJECT = "REJECT"

    MANUAL_REVIEW = "MANUAL_REVIEW"


class RiskLevel(StrEnum):
    LOW = "LOW"

    MEDIUM = "MEDIUM"

    HIGH = "HIGH"

    CRITICAL = "CRITICAL"


class Confidence(StrEnum):
    VERY_LOW = "VERY_LOW"

    LOW = "LOW"

    MEDIUM = "MEDIUM"

    HIGH = "HIGH"

    VERY_HIGH = "VERY_HIGH"


class AgentState(StrEnum):
    IDLE = "IDLE"

    RUNNING = "RUNNING"

    WAITING = "WAITING"

    FAILED = "FAILED"


class ProviderStatus(StrEnum):
    AVAILABLE = "AVAILABLE"

    UNAVAILABLE = "UNAVAILABLE"

    RATE_LIMITED = "RATE_LIMITED"

    ERROR = "ERROR"
