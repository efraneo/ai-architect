"""
=========================================================
Workflow
=========================================================
"""

from __future__ import annotations

import time

from .stage import Stage


class Workflow:
    def __init__(
        self,
        name: str,
    ):

        self.name = name

        self.stages: list[Stage] = []

    def add_stage(
        self,
        stage: Stage,
    ):

        self.stages.append(stage)

    def execute(
        self,
        context,
    ):

        results = []

        for stage in self.stages:
            start = time.perf_counter()

            result = stage.execute(context)

            result.duration = time.perf_counter() - start

            results.append(result)

            if not result.success:
                break

        return results
