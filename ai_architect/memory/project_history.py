"""
Project History

Persistent Execution History
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class ProjectHistory:
    """
    Stores every execution performed by
    QUANT AI Architect.

    This history is later consumed by the
    Learning Engine, Decision Engine and
    Knowledge Engine.
    """

    def __init__(
        self,
        storage: str = ".quant",
    ) -> None:
        self.root = Path(storage)

        self.root.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.history_file = self.root / "history.json"

    def append(
        self,
        execution: dict[str, Any],
    ) -> None:
        history = self.load()

        entry = dict(execution)

        entry["timestamp"] = datetime.utcnow().isoformat()

        history.append(
            entry,
        )

        self.history_file.write_text(
            json.dumps(
                history,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def load(
        self,
    ) -> list[dict[str, Any]]:
        if not self.history_file.exists():
            return []

        try:
            data = json.loads(
                self.history_file.read_text(
                    encoding="utf-8",
                )
            )

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return []

        if not isinstance(
            data,
            list,
        ):
            return []

        return [item for item in data if isinstance(item, dict)]

    def last(
        self,
        count: int = 10,
    ) -> list[dict[str, Any]]:
        if count <= 0:
            return []

        return self.load()[-count:]

    def successful(
        self,
    ) -> list[dict[str, Any]]:
        return [
            item
            for item in self.load()
            if item.get(
                "success",
                False,
            )
        ]

    def failed(
        self,
    ) -> list[dict[str, Any]]:
        return [
            item
            for item in self.load()
            if not item.get(
                "success",
                False,
            )
        ]

    def clear(self) -> None:
        if self.history_file.exists():
            self.history_file.unlink()

    def statistics(
        self,
    ) -> dict[str, Any]:
        history = self.load()

        total = len(history)

        successful = len(
            self.successful(),
        )

        failed = total - successful

        confidences = [
            float(
                item.get(
                    "confidence",
                    0.0,
                )
            )
            for item in history
        ]

        average_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            "executions": total,
            "successful": successful,
            "failed": failed,
            "success_rate": round(
                ((successful / total) * 100 if total else 0.0),
                2,
            ),
            "average_confidence": round(
                average_confidence,
                3,
            ),
            "last_execution": (history[-1] if history else None),
        }

    def providers(
        self,
    ) -> dict[str, int]:
        result: dict[str, int] = {}

        for item in self.load():
            provider = str(
                item.get(
                    "provider",
                    "unknown",
                )
            )

            result[provider] = (
                result.get(
                    provider,
                    0,
                )
                + 1
            )

        return result

    def files(
        self,
    ) -> dict[str, int]:
        result: dict[str, int] = {}

        for item in self.load():
            filename = str(
                item.get(
                    "file",
                    "unknown",
                )
            )

            result[filename] = (
                result.get(
                    filename,
                    0,
                )
                + 1
            )

        return result
