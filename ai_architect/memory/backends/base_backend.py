"""
=========================================================
Memory Backend

Abstract Storage Backend
=========================================================
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai_architect.memory.models import (
    Experience,
    MemorySnapshot,
)


class MemoryBackend(ABC):
    """
    Abstract persistence backend.

    Every storage implementation must inherit
    from this interface.

    Supported backends

        • JSON

        • SQLite

        • PostgreSQL

        • ChromaDB

        • LanceDB

        • Milvus

        • Weaviate

        • Redis

    The MemoryEngine never knows which backend
    is being used.
    """

    ###########################################################

    @abstractmethod
    def load(
        self,
    ) -> MemorySnapshot:
        """
        Load complete memory snapshot.
        """
        raise NotImplementedError

    ###########################################################

    @abstractmethod
    def save(
        self,
        snapshot: MemorySnapshot,
    ) -> None:
        """
        Persist complete snapshot.
        """
        raise NotImplementedError

    ###########################################################

    @abstractmethod
    def append(
        self,
        experience: Experience,
    ) -> None:
        """
        Store one experience.
        """
        raise NotImplementedError

    ###########################################################

    @abstractmethod
    def clear(
        self,
    ) -> None:
        """
        Remove all stored data.
        """
        raise NotImplementedError

    ###########################################################

    @abstractmethod
    def exists(
        self,
    ) -> bool:
        """
        Returns True if backend storage exists.
        """
        raise NotImplementedError

    ###########################################################

    @abstractmethod
    def count(
        self,
    ) -> int:
        """
        Number of stored experiences.
        """
        raise NotImplementedError
