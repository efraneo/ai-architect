"""
=========================================================
Improvement Selector

Automatic File Selection
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from ai_architect.llm.repository_scanner import (
    RepositoryScanner,
)


class ImprovementSelector:
    """
    Selects the best candidate for improvement.

    This class is responsible for moving the Architect
    from manual mode:

        architect improve repo --file xxx.py

    to automatic mode:

        architect improve repo
    """

    def __init__(self) -> None:

        self.scanner = RepositoryScanner()

    def select(
        self,
        repository: str | Path,
    ) -> str | None:

        candidates = self.scanner.scan(
            repository,
        )

        for item in candidates:
            if not item["python"]:
                continue

            if item["test"]:
                continue

            if item["generated"]:
                continue

            path = item["path"]

            if isinstance(path, str):
                return path

        return None

    def select_many(
        self,
        repository: str | Path,
        limit: int = 5,
    ) -> list[str]:

        selected: list[str] = []

        for item in self.scanner.scan(
            repository,
        ):
            if len(selected) >= limit:
                break

            if not item["python"]:
                continue

            if item["generated"]:
                continue

            if item["test"]:
                continue

            selected.append(item["path"])

        return selected

    def build_execution_queue(
        self,
        repository: str | Path,
        limit: int = 10,
    ) -> list[dict]:

        queue = []

        for filename in self.select_many(
            repository,
            limit,
        ):
            queue.append(
                {
                    "file": filename,
                    "instruction": "Improve code quality.",
                    "status": "pending",
                }
            )

        return queue

    def statistics(
        self,
        repository: str | Path,
    ) -> dict:

        summary = self.scanner.summary(
            repository,
        )

        summary["selected"] = self.select(
            repository,
        )

        summary["queue"] = len(
            self.select_many(
                repository,
            )
        )

        return summary
