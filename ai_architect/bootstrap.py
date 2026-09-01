"""
=========================================================
Bootstrap
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from ai_architect.config.settings import Settings
from ai_architect.logger.logger import Logger


class Bootstrap:
    def __init__(
        self,
        env_file: str | Path,
    ):

        self.settings = Settings(env_file)

        self.logger = Logger()

    def initialize(self):

        self.logger.info("Initializing AI Architect")

        self.logger.info(f"Project: {self.settings.project_root}")

        return self.settings
