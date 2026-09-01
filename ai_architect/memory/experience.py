"""
=========================================================
Experience Model

Domain Entity
=========================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(slots=True)
class Experience:
    """
    Represents one learning experience
    produced by QUANT AI Architect.
    """

    timestamp: datetime

    project: str

    task: str

    decision: str

    success: bool

    confidence: float

    duration: float

    notes: str = ""

    quality: float = 0.0

    provider: str = ""

    model: str = ""

    commit: str = ""

    retries: int = 0

    metadata: dict | None = None

    def to_dict(self) -> dict:

        data = asdict(self)

        data["timestamp"] = self.timestamp.isoformat()

        return data

    @classmethod
    def from_dict(
        cls,
        data: dict,
    ) -> Experience:

        values = dict(data)

        values["timestamp"] = datetime.fromisoformat(values["timestamp"])

        return cls(**values)

    @property
    def successful(self) -> bool:

        return self.success

    @property
    def failed(self) -> bool:

        return not self.success
