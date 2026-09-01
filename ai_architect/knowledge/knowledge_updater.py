"""
Knowledge Updater

Continuous Knowledge Learning
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ai_architect.knowledge.project_memory import (
    ProjectMemory,
)


class KnowledgeUpdater:
    """
    Updates persistent project knowledge after
    every execution.
    """

    def __init__(self) -> None:
        self.memory = ProjectMemory()

    def update(
        self,
        project: str,
        execution: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if execution is None:
            execution = {}

        current = self.memory.project(
            project,
        )

        executions = int(
            current.get(
                "executions",
                0,
            )
        )

        successful = int(
            current.get(
                "successful",
                0,
            )
        )

        failed = int(
            current.get(
                "failed",
                0,
            )
        )

        executions += 1

        if execution.get(
            "success",
            False,
        ):
            successful += 1
        else:
            failed += 1

        raw_history = current.get(
            "confidence_history",
            [],
        )

        if isinstance(
            raw_history,
            list,
        ):
            confidence_history = [float(value) for value in raw_history]
        else:
            confidence_history = []

        confidence = float(
            execution.get(
                "confidence",
                0.0,
            )
        )

        confidence_history.append(
            confidence,
        )

        average_confidence = (
            sum(confidence_history) / len(confidence_history)
            if confidence_history
            else 0.0
        )

        information: dict[str, Any] = {
            "executions": executions,
            "successful": successful,
            "failed": failed,
            "last_execution": (datetime.utcnow().isoformat()),
            "last_file": execution.get(
                "file",
            ),
            "last_provider": execution.get(
                "provider",
            ),
            "confidence": confidence,
            "confidence_history": (confidence_history),
            "average_confidence": round(
                average_confidence,
                3,
            ),
        }

        self.memory.update_project(
            project,
            information,
        )

        return information

    def project_summary(
        self,
        project: str,
    ) -> dict[str, Any]:
        return self.memory.project(
            project,
        )

    def best_confidence(
        self,
        project: str,
    ) -> float:
        history = self.memory.project(
            project,
        ).get(
            "confidence_history",
            [],
        )

        if not isinstance(
            history,
            list,
        ):
            return 0.0

        if not history:
            return 0.0

        return max(float(value) for value in history)

    def success_rate(
        self,
        project: str,
    ) -> float:
        data = self.memory.project(
            project,
        )

        total = int(
            data.get(
                "executions",
                0,
            )
        )

        if total == 0:
            return 0.0

        successful = int(
            data.get(
                "successful",
                0,
            )
        )

        return round(
            (successful / total) * 100,
            2,
        )

    def reset(
        self,
        project: str,
    ) -> None:
        self.memory.update_project(
            project,
            {
                "executions": 0,
                "successful": 0,
                "failed": 0,
                "confidence": 0.0,
                "confidence_history": [],
                "average_confidence": 0.0,
            },
        )
