"""
Planner Models

Execution Planning Domain Models
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

# =========================================================
# Priority
# =========================================================


class TaskPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# =========================================================
# Status
# =========================================================


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"


# =========================================================
# Planner Task
# =========================================================


@dataclass(slots=True)
class PlannerTask:
    """
    Represents one executable task.
    """

    id: str
    title: str
    description: str
    priority: TaskPriority

    status: TaskStatus = TaskStatus.PENDING

    assigned_agent: str = ""

    estimated_seconds: int = 0

    retries: int = 0

    max_retries: int = 3

    dependencies: list[str] = field(
        default_factory=list,
    )

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    result: str = ""

    error: str = ""

    confidence: float = 0.0

    risk: float = 0.0

    quality: float = 0.0

    created_at: datetime = field(
        default_factory=datetime.utcnow,
    )

    started_at: datetime | None = None

    finished_at: datetime | None = None

    duration: float = 0.0

    execution_count: int = 0

    tags: list[str] = field(
        default_factory=list,
    )

    # -----------------------------------------------------
    # Lifecycle
    # -----------------------------------------------------

    def start(
        self,
    ) -> None:
        self.status = TaskStatus.RUNNING

        self.started_at = datetime.utcnow()

        self.execution_count += 1

    def complete(
        self,
        result: str = "",
    ) -> None:
        self.status = TaskStatus.COMPLETED

        self.result = result

        self.finished_at = datetime.utcnow()

        if self.started_at:
            self.duration = (self.finished_at - self.started_at).total_seconds()

    def fail(
        self,
        error: str,
    ) -> None:
        self.status = TaskStatus.FAILED

        self.error = error

        self.finished_at = datetime.utcnow()

        if self.started_at:
            self.duration = (self.finished_at - self.started_at).total_seconds()

    def cancel(
        self,
    ) -> None:
        self.status = TaskStatus.CANCELLED

    def retry(
        self,
    ) -> None:
        self.retries += 1

        self.status = TaskStatus.PENDING

        self.started_at = None

        self.finished_at = None

        self.error = ""

        self.duration = 0.0

    # -----------------------------------------------------
    # State properties
    # -----------------------------------------------------

    @property
    def completed(
        self,
    ) -> bool:
        return self.status == TaskStatus.COMPLETED

    @property
    def pending(
        self,
    ) -> bool:
        return self.status == TaskStatus.PENDING

    @property
    def running(
        self,
    ) -> bool:
        return self.status == TaskStatus.RUNNING

    @property
    def failed(
        self,
    ) -> bool:
        return self.status == TaskStatus.FAILED

    @property
    def retry_available(
        self,
    ) -> bool:
        return self.retries < self.max_retries

    # -----------------------------------------------------
    # Serialization
    # -----------------------------------------------------

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "assigned_agent": self.assigned_agent,
            "estimated_seconds": self.estimated_seconds,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "dependencies": list(self.dependencies),
            "metadata": dict(self.metadata),
            "result": self.result,
            "error": self.error,
            "confidence": self.confidence,
            "risk": self.risk,
            "quality": self.quality,
            "created_at": self.created_at.isoformat(),
            "started_at": (self.started_at.isoformat() if self.started_at else None),
            "finished_at": (self.finished_at.isoformat() if self.finished_at else None),
            "duration": self.duration,
            "execution_count": self.execution_count,
            "tags": list(self.tags),
        }


# =========================================================
# Execution Plan
# =========================================================


@dataclass(slots=True)
class ExecutionPlan:
    """
    Ordered execution plan produced by Planner.
    """

    tasks: list[PlannerTask] = field(
        default_factory=list,
    )

    created_at: datetime = field(
        default_factory=datetime.utcnow,
    )

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    # -----------------------------------------------------
    # Task management
    # -----------------------------------------------------

    def add(
        self,
        task: PlannerTask,
    ) -> None:
        self.tasks.append(
            task,
        )

    def extend(
        self,
        tasks: list[PlannerTask],
    ) -> None:
        self.tasks.extend(
            tasks,
        )

    def sort(
        self,
    ) -> None:
        order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3,
        }

        self.tasks.sort(
            key=lambda task: (
                order[task.priority],
                len(task.dependencies),
            ),
        )

    def task(
        self,
        task_id: str,
    ) -> PlannerTask | None:
        for task in self.tasks:
            if task.id == task_id:
                return task

        return None

    # -----------------------------------------------------
    # Statistics
    # -----------------------------------------------------

    @property
    def total_tasks(
        self,
    ) -> int:
        return len(
            self.tasks,
        )

    @property
    def completed_tasks(
        self,
    ) -> int:
        return sum(task.completed for task in self.tasks)

    @property
    def pending_tasks(
        self,
    ) -> int:
        return sum(task.pending for task in self.tasks)

    @property
    def running_tasks(
        self,
    ) -> int:
        return sum(task.running for task in self.tasks)

    @property
    def failed_tasks(
        self,
    ) -> int:
        return sum(task.failed for task in self.tasks)

    @property
    def progress(
        self,
    ) -> float:
        if not self.tasks:
            return 100.0

        return round(
            (self.completed_tasks / self.total_tasks) * 100,
            2,
        )

    @property
    def estimated_seconds(
        self,
    ) -> int:
        return sum(task.estimated_seconds for task in self.tasks)

    @property
    def execution_seconds(
        self,
    ) -> float:
        return round(
            sum(task.duration for task in self.tasks),
            2,
        )

    # -----------------------------------------------------
    # Serialization
    # -----------------------------------------------------

    def to_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "created_at": self.created_at.isoformat(),
            "progress": self.progress,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "pending_tasks": self.pending_tasks,
            "running_tasks": self.running_tasks,
            "failed_tasks": self.failed_tasks,
            "estimated_seconds": self.estimated_seconds,
            "execution_seconds": self.execution_seconds,
            "metadata": dict(self.metadata),
            "tasks": [task.to_dict() for task in self.tasks],
        }

    def summary(
        self,
    ) -> dict[str, Any]:
        return {
            "tasks": self.total_tasks,
            "completed": self.completed_tasks,
            "pending": self.pending_tasks,
            "running": self.running_tasks,
            "failed": self.failed_tasks,
            "progress": self.progress,
            "estimated_seconds": self.estimated_seconds,
        }
