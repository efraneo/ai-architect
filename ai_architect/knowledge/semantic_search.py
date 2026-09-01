"""
=========================================================
Semantic Search
=========================================================
"""

from __future__ import annotations

from pathlib import Path


class SemanticSearch:
    def search(
        self,
        project: str,
        text: str,
    ) -> list:

        matches = []

        keyword = text.lower()

        for file in Path(project).rglob("*.py"):
            source = file.read_text(
                encoding="utf-8",
                errors="ignore",
            ).lower()

            if keyword in source:
                matches.append(str(file))

        return matches
