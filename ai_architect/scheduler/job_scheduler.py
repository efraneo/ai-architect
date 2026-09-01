"""
=========================================================
Job Scheduler
=========================================================
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from .models import (
    ScheduledJob,
    SchedulerState,
)


class JobScheduler:
    def __init__(self):

        self.state = SchedulerState()

    def register(
        self,
        name: str,
        callback: str,
        interval_seconds: int,
    ) -> ScheduledJob:

        job = ScheduledJob(
            id=uuid.uuid4().hex,
            name=name,
            callback=callback,
            interval_seconds=interval_seconds,
            next_run=(datetime.utcnow() + timedelta(seconds=interval_seconds)),
        )

        self.state.add(job)

        return job

    def pending(self):

        now = datetime.utcnow()

        return [
            job
            for job in self.state.jobs
            if (job.enabled and job.next_run and job.next_run <= now)
        ]

    def update(
        self,
        job: ScheduledJob,
    ):

        job.last_run = datetime.utcnow()

        job.next_run = job.last_run + timedelta(seconds=job.interval_seconds)
