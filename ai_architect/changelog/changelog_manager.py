"""
=========================================================
ChangeLog Manager
=========================================================
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import ChangeLogEntry


class ChangeLogManager:
    def __init__(
        self,
        database: str | Path,
    ):

        self.database = Path(database)

        self.database.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.database.exists():
            self.database.write_text(
                "[]",
                encoding="utf-8",
            )

    def load(self):

        data = json.loads(self.database.read_text(encoding="utf-8"))

        return data

    def append(
        self,
        entry: ChangeLogEntry,
    ):

        data = self.load()

        data.append(asdict(entry))

        self.database.write_text(
            json.dumps(
                data,
                indent=4,
                default=str,
            ),
            encoding="utf-8",
        )
