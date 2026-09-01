"""
Autonomous Engine.
"""

from __future__ import annotations

from typing import Any

from .approval_engine import ApprovalEngine
from .branch_manager import BranchManager
from .execution_monitor import ExecutionMonitor
from .execution_worker import ExecutionWorker
from .merge_manager import MergeManager
from .rollback_manager import RollbackManager
from .task_queue import TaskQueue
from .task_scheduler import TaskScheduler


class AutonomousEngine:
    def __init__(self) -> None:
        self.queue = TaskQueue()
        self.scheduler = TaskScheduler()
        self.worker = ExecutionWorker()
        self.branch = BranchManager()
        self.merge = MergeManager()
        self.rollback = RollbackManager()
        self.approval = ApprovalEngine()
        self.monitor = ExecutionMonitor()

    def execute(
        self,
        tasks: list[dict[str, Any]],
    ) -> dict[str, object]:
        ordered = self.scheduler.schedule(tasks)

        for scheduled_task in ordered:
            self.queue.push(scheduled_task)

        results: list[dict[str, object]] = []

        while not self.queue.empty():
            queued_task = self.queue.pop()

            if queued_task is None:
                continue

            result: dict[str, object] = self.worker.execute(
                queued_task,
            )

            self.monitor.register(result)

            results.append(result)

        monitor_report: dict[str, object] = self.monitor.report()

        return {
            "results": results,
            "monitor": monitor_report,
        }
