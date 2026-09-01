"""
Execution Monitor.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


class ExecutionMonitor:
    def __init__(self) -> None:
        self.history: list[dict[str, Any]] = []

    def register(
        self,
        event: dict[str, Any],
    ) -> None:
        event["timestamp"] = datetime.utcnow().isoformat()
        self.history.append(event)

    def report(self) -> dict[str, object]:
        return {
            "executions": len(self.history),
            "events": self.history,
        }
