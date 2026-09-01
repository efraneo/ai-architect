"""
=========================================================
Experience Store

Persistent Experience Repository
=========================================================
"""

from __future__ import annotations

from ai_architect.memory.backends.base_backend import (
    MemoryBackend,
)
from ai_architect.memory.models import (
    Experience,
    MemorySnapshot,
)


class ExperienceStore:
    """
    Storage facade.

    Delegates persistence to the configured backend.

    Supported backends

        • JSON

        • SQLite

        • PostgreSQL

        • ChromaDB

        • LanceDB

        • Milvus

    The rest of the application never talks
    directly to the backend.
    """

    ###############################################################

    def __init__(
        self,
        backend: MemoryBackend,
    ) -> None:

        self.backend = backend

    ###############################################################

    def exists(
        self,
    ) -> bool:

        return self.backend.exists()

    ###############################################################

    def load(
        self,
    ) -> MemorySnapshot:

        return self.backend.load()

    ###############################################################

    def save(
        self,
        snapshot: MemorySnapshot,
    ) -> None:

        self.backend.save(
            snapshot,
        )

    ###############################################################

    def append(
        self,
        experience: Experience,
    ) -> None:

        self.backend.append(
            experience,
        )

    ###############################################################

    def clear(
        self,
    ) -> None:

        self.backend.clear()

    ###############################################################

    def count(
        self,
    ) -> int:

        return self.backend.count()

    ###############################################################

    def last(
        self,
        limit: int = 10,
    ) -> list[Experience]:

        snapshot = self.load()

        return snapshot.experiences[-limit:]

    ###############################################################

    def successful(
        self,
    ) -> list[Experience]:

        return [
            experience
            for experience in self.load().experiences
            if experience.outcome.value == "SUCCESS"
        ]

    ###############################################################

    def failed(
        self,
    ) -> list[Experience]:

        return [
            experience
            for experience in self.load().experiences
            if experience.outcome.value == "FAILURE"
        ]

    ###############################################################

    def repository(
        self,
        repository: str,
    ) -> list[Experience]:

        return [
            experience
            for experience in self.load().experiences
            if experience.repository == repository
        ]
