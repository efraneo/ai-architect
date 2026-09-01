"""
=========================================================
Code Planner

Determines what should be modified before invoking the LLM.
=========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class PlannedChange:
    """
    Represents a single modification request.
    """

    file: str

    priority: int

    instruction: str

    reason: str

    context: list[str] = field(default_factory=list)


class CodePlanner:
    """
    Builds an execution plan for the Smart Editor.

    The planner does NOT modify code.

    It only decides:

        • what file should be edited
        • why
        • in which order
        • what contextual files should accompany it
    """

    def __init__(self) -> None:

        self.max_context_files = 5

    def build_plan(
        self,
        repository: str | Path,
        target_file: str,
        instruction: str,
        related_files: list[str] | None = None,
    ) -> list[PlannedChange]:

        repository = Path(repository)

        if related_files is None:
            related_files = []

        context: list[str] = []

        for item in related_files:
            if item == target_file:
                continue

            candidate = repository / item

            if candidate.exists():
                context.append(item)

            if len(context) >= self.max_context_files:
                break

        return [
            PlannedChange(
                file=target_file,
                priority=1,
                instruction=instruction,
                reason="User requested improvement.",
                context=context,
            )
        ]

    def execution_order(
        self,
        changes: list[PlannedChange],
    ) -> list[PlannedChange]:

        return sorted(
            changes,
            key=lambda change: (
                change.priority,
                change.file,
            ),
        )

    def summarize(
        self,
        changes: list[PlannedChange],
    ) -> dict:

        return {
            "files": len(changes),
            "ordered_files": [
                item.file
                for item in self.execution_order(
                    changes,
                )
            ],
            "context_files": sum(len(item.context) for item in changes),
        }
