"""
=========================================================
Execution Context
=========================================================
"""

from __future__ import annotations

from ai_architect.agent import (
    AIArchitect,
)
from ai_architect.config.settings import (
    Settings,
)
from ai_architect.logger.logger import (
    Logger,
)


class ExecutionContext:
    def __init__(
        self,
        settings: Settings,
    ):

        self.settings = settings

        self.logger = Logger()

        self.agent = AIArchitect(
            project=settings.project_root,
            telegram_env=settings.telegram_env,
        )
