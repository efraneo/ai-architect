"""
=========================================================
Merge Manager
=========================================================
"""

from __future__ import annotations

import subprocess


class MergeManager:
    def merge(
        self,
        branch: str,
    ):

        subprocess.run(
            [
                "git",
                "merge",
                branch,
            ],
            check=False,
        )
