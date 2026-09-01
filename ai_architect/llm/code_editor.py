"""
=========================================================
Code Editor

Safe File Writer
=========================================================
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


class CodeEditor:
    """
    Responsible for writing code safely.

    Every modification creates a backup before replacing
    the original file.
    """

    def __init__(self) -> None:

        self.encoding = "utf-8"

    def write(
        self,
        filename: str | Path,
        source: str,
    ) -> Path:

        target = Path(filename).resolve()

        if not target.exists():
            raise FileNotFoundError(target)

        self._backup(target)

        normalized = self._normalize(source)

        target.write_text(
            normalized,
            encoding=self.encoding,
        )

        return target

    def replace(
        self,
        filename: str | Path,
        source: str,
    ) -> Path:

        return self.write(
            filename,
            source,
        )

    def read(
        self,
        filename: str | Path,
    ) -> str:

        return Path(filename).read_text(
            encoding=self.encoding,
        )

    def _backup(
        self,
        target: Path,
    ) -> Path:

        backup = target.with_suffix(
            target.suffix + f".{datetime.utcnow():%Y%m%d%H%M%S}.bak"
        )

        shutil.copy2(
            target,
            backup,
        )

        return backup

    @staticmethod
    def _normalize(
        source: str,
    ) -> str:

        text = source.replace(
            "\r\n",
            "\n",
        )

        if not text.endswith("\n"):
            text += "\n"

        return text
