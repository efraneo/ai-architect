"""
=========================================================
Job Runner
=========================================================
"""

from __future__ import annotations

from .job_scheduler import JobScheduler
from .models import JobStatus


class JobRunner:
    def __init__(
        self,
        scheduler: JobScheduler,
    ):

        self.scheduler = scheduler

    def run(
        self,
        callbacks: dict,
    ):

        for job in self.scheduler.pending():
            try:
                job.status = JobStatus.RUNNING

                callback = callbacks.get(job.callback)

                if callback:
                    callback()

                job.status = JobStatus.SUCCESS

            except Exception:
                job.status = JobStatus.FAILED

            finally:
                self.scheduler.update(job)
