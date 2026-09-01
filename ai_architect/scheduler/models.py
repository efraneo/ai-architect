"""
=========================================================
Scheduler Models
=========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class JobStatus(StrEnum):
    PENDING = "PENDING"

    RUNNING = "RUNNING"

    SUCCESS = "SUCCESS"

    FAILED = "FAILED"

    CANCELLED = "CANCELLED"


@dataclass(slots=True)
class ScheduledJob:
    id: str

    name: str

    interval_seconds: int

    callback: str

    enabled: bool = True

    last_run: datetime | None = None

    next_run: datetime | None = None

    status: JobStatus = JobStatus.PENDING


@dataclass(slots=True)
class SchedulerState:
    started_at: datetime = field(default_factory=datetime.utcnow)

    jobs: list[ScheduledJob] = field(default_factory=list)

    def add(
        self,
        job: ScheduledJob,
    ) -> None:

        self.jobs.append(job)

    @property
    def total_jobs(
        self,
    ) -> int:

        return len(self.jobs)
