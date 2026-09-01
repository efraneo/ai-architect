"""
=========================================================
Logger
=========================================================
"""

from __future__ import annotations

import logging
from pathlib import Path


class Logger:
    def __init__(
        self,
        folder: str | Path = "logs",
    ):

        folder = Path(folder)

        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.logger = logging.getLogger("AI_ARCHITECT")

        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

            file_handler = logging.FileHandler(
                folder / "architect.log",
                encoding="utf-8",
            )

            file_handler.setFormatter(formatter)

            self.logger.addHandler(file_handler)

    def info(
        self,
        message: str,
    ):

        self.logger.info(message)

    def warning(
        self,
        message: str,
    ):

        self.logger.warning(message)

    def error(
        self,
        message: str,
    ):

        self.logger.error(message)
