"""Task Generator."""

from __future__ import annotations

from typing import Any


class TaskGenerator:
    def build(
        self,
        reports: dict,
    ) -> list[dict[str, Any]]:
        tasks = []

        for agent, report in reports.items():
            tasks.append(
                {
                    "agent": agent,
                    "priority": 1,
                    "callback": lambda report=report: report,
                }
            )

        return tasks
