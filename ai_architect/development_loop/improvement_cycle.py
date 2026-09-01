"""
=========================================================
Improvement Cycle
=========================================================
"""

from __future__ import annotations

from .task_generator import TaskGenerator


class ImprovementCycle:
    def __init__(self):

        self.generator = TaskGenerator()

    def create_tasks(
        self,
        reports: dict,
    ):

        return self.generator.build(reports)
