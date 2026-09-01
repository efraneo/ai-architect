"""
=========================================================
Decision History
=========================================================
"""

from __future__ import annotations

import json
from pathlib import Path


class DecisionHistory:
    def __init__(
        self,
        database="memory/decision_history.json",
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

        return json.loads(self.database.read_text(encoding="utf-8"))

    def append(
        self,
        record: dict,
    ):

        data = self.load()

        data.append(record)

        self.database.write_text(
            json.dumps(
                data,
                indent=4,
            ),
            encoding="utf-8",
        )
