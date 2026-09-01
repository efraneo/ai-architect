"""
=========================================================
Metrics Store
=========================================================
"""

from __future__ import annotations

import json
from pathlib import Path


class MetricsStore:
    def __init__(
        self,
        database="memory/metrics.json",
    ):

        self.database = Path(database)

        self.database.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.database.exists():
            self.database.write_text(
                "{}",
                encoding="utf-8",
            )

    def save(
        self,
        metrics: dict,
    ):

        self.database.write_text(
            json.dumps(
                metrics,
                indent=4,
            ),
            encoding="utf-8",
        )

    def load(self):

        return json.loads(self.database.read_text(encoding="utf-8"))
