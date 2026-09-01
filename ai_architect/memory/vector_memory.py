"""
=========================================================
Vector Memory

Semantic Experience Retrieval
=========================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from ai_architect.memory.models import (
    Experience,
)


@dataclass(slots=True)
class VectorMatch:
    """
    One semantic search result.
    """

    experience: Experience

    similarity: float


class VectorMemory:
    """
    Semantic memory.

    Version 1

        • In-memory vectors

    Future versions

        • ChromaDB

        • FAISS

        • LanceDB

        • Milvus

        • pgvector

    The public API will remain unchanged.
    """

    ###############################################################

    def __init__(
        self,
    ) -> None:

        self._vectors: dict[
            str,
            list[float],
        ] = {}

        self._experiences: dict[
            str,
            Experience,
        ] = {}

    ###############################################################

    def add(
        self,
        experience: Experience,
        embedding: list[float],
    ) -> None:

        self._vectors[experience.id] = embedding

        self._experiences[experience.id] = experience

    ###############################################################

    def remove(
        self,
        experience_id: str,
    ) -> None:

        self._vectors.pop(
            experience_id,
            None,
        )

        self._experiences.pop(
            experience_id,
            None,
        )

    ###############################################################

    def clear(
        self,
    ) -> None:

        self._vectors.clear()

        self._experiences.clear()

    ###############################################################

    def count(
        self,
    ) -> int:

        return len(
            self._vectors,
        )

    ###############################################################

    def search(
        self,
        embedding: list[float],
        limit: int = 5,
    ) -> list[VectorMatch]:

        matches: list[VectorMatch] = []

        for experience_id, vector in self._vectors.items():
            similarity = self._cosine_similarity(
                embedding,
                vector,
            )

            matches.append(
                VectorMatch(
                    experience=(self._experiences[experience_id]),
                    similarity=round(
                        similarity,
                        4,
                    ),
                )
            )

        matches.sort(
            key=lambda item: item.similarity,
            reverse=True,
        )

        return matches[:limit]

    ###############################################################

    @staticmethod
    def _cosine_similarity(
        a: list[float],
        b: list[float],
    ) -> float:

        if len(a) != len(b):
            return 0.0

        dot = sum(
            x * y
            for x, y in zip(
                a,
                b,
                strict=True,
            )
        )

        norm_a = sqrt(sum(x * x for x in a))

        norm_b = sqrt(sum(y * y for y in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    ###############################################################

    def similar_experiences(
        self,
        embedding: list[float],
        threshold: float = 0.85,
    ) -> list[Experience]:

        return [
            match.experience
            for match in self.search(
                embedding,
                limit=100,
            )
            if match.similarity >= threshold
        ]
