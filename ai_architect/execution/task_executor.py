"""
Task Executor

High-Level Execution API
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_architect.execution.execution_engine import ExecutionEngine
from ai_architect.execution.execution_result import ExecutionResult
from ai_architect.patch_generator.patch_loader import PatchLoader


class TaskExecutor:
    """
    Public task-execution interface.

    The execution subsystem is patch-based. ``filename`` is therefore the
    patch file to load; ``instruction`` is retained as task metadata for the
    planner/orchestrator layer.
    """

    def __init__(self, repository: str) -> None:
        self.repository = Path(repository).resolve()
        self.engine = ExecutionEngine()
        self.loader = PatchLoader()

    def execute(
        self,
        filename: str,
        instruction: str,
    ) -> ExecutionResult:
        started = ExecutionResult(
            repository=str(self.repository),
            filename=filename,
            instruction=instruction,
        )

        try:
            patch = self.loader.load(filename)
            execution = self.engine.execute(self.repository, patch)

            started.success = bool(execution.get("success", False))
            started.validation_ok = bool(execution.get("approved", False))
            started.metadata.update(
                {
                    "execution": execution,
                    "patch_id": patch.id,
                    "patch_title": patch.title,
                }
            )

            if not started.success:
                message = execution.get("message")
                if message:
                    started.findings.append(str(message))

        except (FileNotFoundError, ValueError, OSError) as exc:
            started.success = False
            started.validation_ok = False
            started.findings.append(str(exc))
            started.metadata["error_type"] = type(exc).__name__

        finally:
            started.finish()

        return started

    def execute_many(
        self,
        tasks: list[dict[str, str]],
    ) -> list[ExecutionResult]:
        return [
            self.execute(
                filename=task["file"],
                instruction=task["instruction"],
            )
            for task in tasks
        ]

    def execute_until_success(
        self,
        filename: str,
        instruction: str,
        retries: int = 3,
    ) -> ExecutionResult:
        attempts = max(1, retries)
        result = self.execute(filename, instruction)

        for _ in range(attempts - 1):
            if result.approved:
                break

            if result.decision_name != "RETRY":
                break

            result = self.execute(filename, instruction)

        return result

    def batch_summary(
        self,
        results: list[ExecutionResult],
    ) -> dict[str, int | float]:
        summary: dict[str, int | float] = {
            "tasks": len(results),
            "approved": 0,
            "retry": 0,
            "manual_review": 0,
            "rejected": 0,
        }

        for result in results:
            decision = result.decision_name

            if decision == "ACCEPT":
                summary["approved"] = int(summary["approved"]) + 1
            elif decision == "RETRY":
                summary["retry"] = int(summary["retry"]) + 1
            elif decision == "MANUAL_REVIEW":
                summary["manual_review"] = int(summary["manual_review"]) + 1
            else:
                summary["rejected"] = int(summary["rejected"]) + 1

        if results:
            summary["success_rate"] = round(
                int(summary["approved"]) * 100 / len(results),
                2,
            )
        else:
            summary["success_rate"] = 0.0

        return summary

    def health(self) -> dict[str, Any]:
        return self.engine.health()
