"""
=========================================================
Continuous Runner
=========================================================
"""

from __future__ import annotations

import time

from .project_loop import ProjectLoop


class ContinuousRunner:
    def __init__(
        self,
        interval: int = 600,
    ):

        self.interval = interval

        self.loop = ProjectLoop()

    def run(
        self,
        project,
        agents,
        tasks,
    ):

        while True:
            self.loop.cycle(
                project,
                agents,
                tasks,
            )

            time.sleep(self.interval)
