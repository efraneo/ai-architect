"""
=========================================================
JSON Memory Backend

JSON Persistence Backend
=========================================================
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ai_architect.memory.backends.base_backend import (
    MemoryBackend,
)
from ai_architect.memory.models import (
    Experience,
    ExperienceOutcome,
    ExperienceType,
    LearningPattern,
    MemorySnapshot,
)


class JsonMemoryBackend(
    MemoryBackend,
):
    """
    JSON implementation of MemoryBackend.

    Advantages

        • Zero dependencies

        • Human readable

        • Git friendly

        • Ideal for local development

    Future production environments should
    migrate to SQLite, PostgreSQL or a
    vector database.
    """

    ###############################################################

    def __init__(
        self,
        storage: str | Path,
    ) -> None:

        self.storage = Path(storage)

        self.storage.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    ###############################################################

    def exists(
        self,
    ) -> bool:

        return self.storage.exists()

    ###############################################################

    def load(
        self,
    ) -> MemorySnapshot:

        if not self.exists():
            return MemorySnapshot()

        with self.storage.open(
            "r",
            encoding="utf-8",
        ) as file:
            raw = json.load(file)

        snapshot = MemorySnapshot()

        #
        # Experiences
        #

        for item in raw.get(
            "experiences",
            [],
        ):
            snapshot.experiences.append(
                Experience(
                    id=item["id"],
                    repository=item["repository"],
                    filename=item["filename"],
                    instruction=item["instruction"],
                    provider=item["provider"],
                    experience_type=ExperienceType(item["experience_type"]),
                    outcome=ExperienceOutcome(item["outcome"]),
                    confidence=item["confidence"],
                    score=item["score"],
                    risk=item["risk"],
                    metadata=item.get(
                        "metadata",
                        {},
                    ),
                    created_at=datetime.fromisoformat(item["created_at"]),
                )
            )

        #
        # Patterns
        #

        for item in raw.get(
            "patterns",
            [],
        ):
            snapshot.patterns.append(
                LearningPattern(
                    name=item["name"],
                    description=item["description"],
                    confidence=item["confidence"],
                    occurrences=item["occurrences"],
                    metadata=item.get(
                        "metadata",
                        {},
                    ),
                )
            )

        snapshot.metadata = raw.get(
            "metadata",
            {},
        )

        return snapshot

    ###############################################################

    def save(
        self,
        snapshot: MemorySnapshot,
    ) -> None:

        with self.storage.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                snapshot.to_dict(),
                file,
                indent=4,
                ensure_ascii=False,
                sort_keys=False,
            )

    ###############################################################

    def append(
        self,
        experience: Experience,
    ) -> None:

        snapshot = self.load()

        snapshot.experiences.append(
            experience,
        )

        self.save(
            snapshot,
        )

    ###############################################################

    def clear(
        self,
    ) -> None:

        self.save(
            MemorySnapshot(),
        )

    ###############################################################

    def count(
        self,
    ) -> int:

        return len(
            self.load().experiences,
        )
