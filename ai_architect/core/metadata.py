"""
=========================================================
Metadata

Shared Metadata Container
=========================================================
"""

from __future__ import annotations

import platform
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Metadata:
    """
    Shared execution metadata.
    """

    project: str = ""

    repository: str = ""

    version: str = "2.0"

    provider: str = ""

    model: str = ""

    user: str = ""

    started_at: datetime = field(
        default_factory=datetime.utcnow,
    )

    tags: list[str] = field(
        default_factory=list,
    )

    custom: dict = field(
        default_factory=dict,
    )

    @property
    def environment(self) -> dict:

        return {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "implementation": (platform.python_implementation()),
            "executable": sys.executable,
        }

    def to_dict(self) -> dict:

        data = asdict(self)

        data["started_at"] = self.started_at.isoformat()

        data["environment"] = self.environment

        return data
