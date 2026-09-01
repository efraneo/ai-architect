"""
Execution Orchestrator

Execution Plan Coordinator
"""

from __future__ import annotations

from ai_architect.execution.execution_result import ExecutionResult
from ai_architect.execution.task_executor import TaskExecutor
from ai_architect.planner.models import ExecutionPlan, PlannerTask


class ExecutionOrchestrator:
    """
    Executes complete execution plans.

    Responsibilities:
        • Execute ExecutionPlan
        • Respect dependencies
        • Track progress
        • Aggregate results
        • Stop on critical failures
    """

    def __init__(self, repository: str) -> None:
        self.executor = TaskExecutor(repository)

    def execute_plan(
        self,
        plan: ExecutionPlan,
    ) -> list[ExecutionResult]:
        results: list[ExecutionResult] = []

        for task in plan.tasks:
            if not self._can_execute(task, plan):
                continue

            task.start()

            filename = str(task.metadata.get("file", ""))
            instruction = task.description

            result = self.executor.execute(
                filename=filename,
                instruction=instruction,
            )

            if result.approved:
                task.complete(result.decision_name)
            else:
                task.fail(result.decision_name)

            results.append(result)

            if result.decision_name == "REJECT":
                break

        return results

    def _can_execute(
        self,
        task: PlannerTask,
        plan: ExecutionPlan,
    ) -> bool:
        completed = {item.id for item in plan.tasks if item.completed}

        return all(dependency in completed for dependency in task.dependencies)

    def summary(self, results: list[ExecutionResult]) -> dict[str, int | float]:
        return self.executor.batch_summary(results)

    def health(self) -> dict[str, object]:
        return self.executor.health()
