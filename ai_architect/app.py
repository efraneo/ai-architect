"""
=========================================================
QUANT AI ARCHITECT

Application
=========================================================
"""

from __future__ import annotations

from ai_architect.engine import ArchitectEngine


class Application:
    def __init__(
        self,
        project: str,
        telegram_env: str,
    ):

        self.engine = ArchitectEngine(
            project=project,
            telegram_env=telegram_env,
        )

    def run(self):

        return self.engine.execute()
