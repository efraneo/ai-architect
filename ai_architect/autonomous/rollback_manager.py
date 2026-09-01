"""
=========================================================
Rollback Manager
=========================================================
"""

from __future__ import annotations

import subprocess


class RollbackManager:
    def rollback_last_commit(self):

        subprocess.run(
            [
                "git",
                "reset",
                "--hard",
                "HEAD~1",
            ],
            check=False,
        )

    def rollback_file(
        self,
        file: str,
    ):

        subprocess.run(
            [
                "git",
                "checkout",
                "--",
                file,
            ],
            check=False,
        )
