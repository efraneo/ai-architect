"""
Repository Memory

Persistent Repository State
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast


class RepositoryMemory:
    """
    Stores persistent information about one repository.

    This is NOT execution history.

    This is NOT knowledge.

    It stores repository metadata and long-term state.
    """

    FILE_NAME = ".quant_repository.json"

    def __init__(
        self,
        repository: str,
    ) -> None:
        self.repository = Path(repository)
        self.file = self.repository / self.FILE_NAME
        self.data = self._load()

    # -----------------------------------------------------

    def _default(self) -> dict[str, Any]:
        now = datetime.utcnow().isoformat()

        return {
            "created": now,
            "last_updated": now,
            "repository": self.repository.name,
            "settings": {},
            "metadata": {},
            "metrics": {},
            "preferences": {},
            "custom": {},
        }

    # -----------------------------------------------------

    def _load(self) -> dict[str, Any]:
        if self.file.exists():
            try:
                with self.file.open(
                    "r",
                    encoding="utf-8",
                ) as f:
                    data = json.load(f)

                if isinstance(data, dict):
                    return cast(
                        dict[str, Any],
                        data,
                    )

            except (
                OSError,
                json.JSONDecodeError,
            ):
                pass

        return self._default()

    # -----------------------------------------------------

    def save(self) -> None:
        self.data["last_updated"] = datetime.utcnow().isoformat()

        with self.file.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                self.data,
                f,
                indent=4,
                ensure_ascii=False,
            )

    # -----------------------------------------------------

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self.data.get(
            key,
            default,
        )

    # -----------------------------------------------------

    def set(
        self,
        key: str,
        value: Any,
    ) -> None:
        self.data[key] = value
        self.save()

    # -----------------------------------------------------

    def update_section(
        self,
        section: str,
        values: dict[str, Any],
    ) -> None:
        current = self.data.get(
            section,
        )

        if not isinstance(
            current,
            dict,
        ):
            current = {}
            self.data[section] = current

        current.update(
            values,
        )

        self.save()

    # -----------------------------------------------------

    def get_section(
        self,
        section: str,
    ) -> dict[str, Any]:
        value = self.data.get(
            section,
            {},
        )

        if not isinstance(
            value,
            dict,
        ):
            return {}

        return dict(value)

    # -----------------------------------------------------

    def remove(
        self,
        key: str,
    ) -> bool:
        if key not in self.data:
            return False

        del self.data[key]

        self.save()

        return True

    # -----------------------------------------------------

    def reset(self) -> None:
        self.data = self._default()
        self.save()

    # -----------------------------------------------------

    def summary(self) -> dict[str, Any]:
        return {
            "repository": self.repository.name,
            "created": self.data.get(
                "created",
            ),
            "last_updated": self.data.get(
                "last_updated",
            ),
            "sections": sorted(
                self.data.keys(),
            ),
        }
