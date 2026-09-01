"""
=========================================================
Refactor Planner
=========================================================
"""

from __future__ import annotations


class RefactorPlanner:
    MAX_FILES = 5

    def split(
        self,
        files: list[str],
    ) -> list[list[str]]:

        return [
            files[i : i + self.MAX_FILES]
            for i in range(
                0,
                len(files),
                self.MAX_FILES,
            )
        ]

    def create_plan(
        self,
        task: str,
        files: list[str],
    ):

        batches = self.split(files)

        return [
            {
                "step": index + 1,
                "task": task,
                "files": batch,
            }
            for index, batch in enumerate(batches)
        ]
