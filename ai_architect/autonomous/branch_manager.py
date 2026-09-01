"""
=========================================================
Branch Manager
=========================================================
"""

from __future__ import annotations

import subprocess


class BranchManager:
    def create(
        self,
        name: str,
    ):

        subprocess.run(
            [
                "git",
                "checkout",
                "-b",
                name,
            ],
            check=False,
        )

    def current(self):

        result = subprocess.run(
            [
                "git",
                "branch",
                "--show-current",
            ],
            capture_output=True,
            text=True,
        )

        return result.stdout.strip()
