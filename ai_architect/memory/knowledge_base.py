"""
Knowledge Base

Persistent Knowledge Repository
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast


class KnowledgeBase:
    """
    Stores reusable engineering knowledge.

    Unlike ExperienceMemory, this repository stores
    permanent knowledge instead of execution history.
    """

    FILE_NAME = ".quant_knowledge.json"

    def __init__(
        self,
        repository: str,
    ) -> None:
        self.repository = Path(repository)
        self.file = self.repository / self.FILE_NAME
        self.knowledge = self._load()

    # -----------------------------------------------------

    def _default(self) -> dict[str, Any]:
        return {
            "created": datetime.utcnow().isoformat(),
            "items": [],
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
        with self.file.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                self.knowledge,
                f,
                indent=4,
                ensure_ascii=False,
            )

    # -----------------------------------------------------

    def add(
        self,
        *,
        category: str,
        title: str,
        description: str,
        tags: list[str] | None = None,
        source: str = "manual",
        confidence: float = 1.0,
    ) -> None:
        items = self._items()

        items.append(
            {
                "timestamp": (datetime.utcnow().isoformat()),
                "category": category,
                "title": title,
                "description": description,
                "tags": list(tags or []),
                "source": source,
                "confidence": float(
                    confidence,
                ),
            }
        )

        self.knowledge["items"] = items

        self.save()

    # -----------------------------------------------------

    def _items(self) -> list[dict[str, Any]]:
        items = self.knowledge.get(
            "items",
            [],
        )

        if not isinstance(
            items,
            list,
        ):
            return []

        return [item for item in items if isinstance(item, dict)]

    # -----------------------------------------------------

    def all(
        self,
    ) -> list[dict[str, Any]]:
        return list(
            self._items(),
        )

    # -----------------------------------------------------

    def search(
        self,
        keyword: str,
    ) -> list[dict[str, Any]]:
        keyword = keyword.lower()

        results: list[dict[str, Any]] = []

        for item in self._items():
            title = str(
                item.get(
                    "title",
                    "",
                )
            )

            description = str(
                item.get(
                    "description",
                    "",
                )
            )

            raw_tags = item.get(
                "tags",
                [],
            )

            tags = (
                raw_tags
                if isinstance(
                    raw_tags,
                    list,
                )
                else []
            )

            if (
                keyword in title.lower()
                or keyword in description.lower()
                or any(keyword in str(tag).lower() for tag in tags)
            ):
                results.append(item)

        return results

    # -----------------------------------------------------

    def by_category(
        self,
        category: str,
    ) -> list[dict[str, Any]]:
        return [
            item
            for item in self._items()
            if item.get(
                "category",
            )
            == category
        ]

    # -----------------------------------------------------

    def remove(
        self,
        title: str,
    ) -> bool:
        items = self._items()

        before = len(items)

        remaining = [
            item
            for item in items
            if item.get(
                "title",
            )
            != title
        ]

        changed = len(remaining) != before

        if changed:
            self.knowledge["items"] = remaining
            self.save()

        return changed

    # -----------------------------------------------------

    def statistics(
        self,
    ) -> dict[str, Any]:
        items = self._items()

        categories: dict[str, int] = {}

        for item in items:
            category = str(
                item.get(
                    "category",
                    "unknown",
                )
            )

            categories[category] = (
                categories.get(
                    category,
                    0,
                )
                + 1
            )

        return {
            "entries": len(items),
            "categories": categories,
        }

    # -----------------------------------------------------

    def clear(self) -> None:
        self.knowledge = self._default()
        self.save()

    # -----------------------------------------------------

    def summary(
        self,
    ) -> dict[str, Any]:
        return {
            "repository": str(
                self.repository,
            ),
            "statistics": self.statistics(),
        }
