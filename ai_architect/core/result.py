"""
=========================================================
Core Result

Standard Result Object
=========================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Result:
    """
    Standard response returned by every engine.

    Every module should return Result instead of a raw dict.
    """

    success: bool = True

    payload: Any = None

    errors: list[str] = field(
        default_factory=list,
    )

    warnings: list[str] = field(
        default_factory=list,
    )

    metrics: dict[str, Any] = field(
        default_factory=dict,
    )

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    started_at: datetime = field(
        default_factory=datetime.utcnow,
    )

    finished_at: datetime | None = None

    def finish(self) -> None:

        self.finished_at = datetime.utcnow()

    @property
    def duration(self) -> float:

        if self.finished_at is None:
            return 0.0

        return round(
            (self.finished_at - self.started_at).total_seconds(),
            3,
        )

    def add_error(
        self,
        message: str,
    ) -> None:

        self.success = False

        self.errors.append(message)

    def add_warning(
        self,
        message: str,
    ) -> None:

        self.warnings.append(message)

    def set_metric(
        self,
        key: str,
        value: Any,
    ) -> None:

        self.metrics[key] = value

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:

        self.metadata[key] = value

    def to_dict(self) -> dict:

        data = asdict(self)

        data["started_at"] = self.started_at.isoformat()

        data["finished_at"] = self.finished_at.isoformat() if self.finished_at else None

        data["duration"] = self.duration

        return data
