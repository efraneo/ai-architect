"""
=========================================================
AI Architect Settings
=========================================================
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


class Settings:
    def __init__(self, env_file: str | Path):

        load_dotenv(env_file)

        self.project_root = Path(
            os.getenv(
                "PROJECT_ROOT",
                "../QUANT_TITAN_PRO",
            )
        )

        self.max_file_lines = int(
            os.getenv(
                "MAX_FILE_LINES",
                600,
            )
        )

        self.max_complexity = int(
            os.getenv(
                "MAX_COMPLEXITY",
                10,
            )
        )

        self.auto_commit = (
            os.getenv(
                "AUTO_COMMIT",
                "false",
            ).lower()
            == "true"
        )

        self.run_tests = (
            os.getenv(
                "RUN_TESTS",
                "true",
            ).lower()
            == "true"
        )

        self.telegram_env = os.getenv(
            "TELEGRAM_ENV",
            "../telegram_quant_titan.env",
        )

        self.log_level = os.getenv(
            "LOG_LEVEL",
            "INFO",
        )
