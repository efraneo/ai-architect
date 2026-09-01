"""
=========================================================
Stage Result
=========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class StageResult:
    name: str

    success: bool

    message: str = ""

    duration: float = 0.0

    started_at: datetime = field(default_factory=datetime.utcnow)

    finished_at: datetime | None = None

    data: dict = field(default_factory=dict)
