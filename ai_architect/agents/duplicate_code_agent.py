"""
Duplicate Code Agent.
"""

from __future__ import annotations

from hashlib import md5
from pathlib import Path

from .base_agent import BaseAgent


class DuplicateCodeAgent(BaseAgent):
    name = "Duplicate Code Agent"

    def review(
        self,
        project: str,
    ) -> dict[str, object]:
        hashes: dict[str, str] = {}
        duplicates: list[tuple[str, str]] = []

        for file in Path(project).rglob("*.py"):
            text = file.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            digest = md5(
                text.encode(),
            ).hexdigest()

            if digest in hashes:
                duplicates.append(
                    (
                        hashes[digest],
                        str(file),
                    )
                )
            else:
                hashes[digest] = str(file)

        return {
            "duplicates": duplicates,
            "total": len(duplicates),
        }
