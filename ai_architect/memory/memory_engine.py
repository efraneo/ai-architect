"""
Memory Engine

Central Memory Coordinator
"""

from __future__ import annotations

import uuid
from pathlib import Path

from ai_architect.memory.backends.json_backend import (
    JsonMemoryBackend,
)
from ai_architect.memory.experience_store import (
    ExperienceStore,
)
from ai_architect.memory.knowledge_graph import (
    KnowledgeGraph,
)
from ai_architect.memory.learning_engine import (
    LearningEngine,
)
from ai_architect.memory.models import (
    Experience,
    ExperienceOutcome,
    ExperienceType,
    LearningPattern,
    MemorySnapshot,
)
from ai_architect.memory.pattern_miner import (
    PatternMiner,
)
from ai_architect.memory.vector_memory import (
    VectorMemory,
)


class MemoryEngine:
    """
    Central facade for the Memory subsystem.

    Coordinates

        • Experience Store
        • Learning Engine
        • Pattern Miner
        • Vector Memory
        • Knowledge Graph
    """

    ###############################################################
    # Initialization
    ###############################################################

    def __init__(
        self,
        storage: str | Path = ".ai_architect/memory.json",
    ) -> None:
        backend = JsonMemoryBackend(
            storage,
        )

        self.store = ExperienceStore(
            backend,
        )

        self.learning = LearningEngine()

        self.patterns = PatternMiner()

        self.vector = VectorMemory()

        self.graph = KnowledgeGraph()

    ###############################################################
    # Snapshot
    ###############################################################

    def snapshot(
        self,
    ) -> MemorySnapshot:
        return self.store.load()

    ###############################################################
    # Record
    ###############################################################

    def record(
        self,
        *,
        repository: str,
        filename: str,
        instruction: str,
        provider: str,
        outcome: ExperienceOutcome,
        confidence: float,
        score: float | None = None,
        risk: float = 0.0,
        experience_type: ExperienceType = ExperienceType.EXECUTION,
        metadata: dict | None = None,
    ) -> Experience:
        """
        Creates and stores a new execution experience.

        This is the high-level write operation used by
        subsystems such as ProjectLoop and SmartEditor.

        The actual persistence and learning refresh are
        delegated to remember().
        """

        experience = Experience(
            id=uuid.uuid4().hex,
            repository=repository,
            filename=filename,
            instruction=instruction,
            provider=provider,
            experience_type=experience_type,
            outcome=outcome,
            confidence=confidence,
            score=confidence if score is None else score,
            risk=risk,
            metadata=metadata or {},
        )

        self.remember(
            experience,
        )

        return experience

    ###############################################################
    # Remember
    ###############################################################

    def remember(
        self,
        experience: Experience,
        embedding: list[float] | None = None,
    ) -> None:
        """
        Stores an Experience and refreshes the learning state.
        """

        #
        # Persistent storage
        #

        self.store.append(
            experience,
        )

        #
        # Vector memory
        #

        if embedding is not None:
            self.vector.add(
                experience,
                embedding,
            )

        #
        # Refresh learning
        #

        self.refresh()

    ###############################################################
    # Refresh
    ###############################################################

    def refresh(
        self,
    ) -> list[LearningPattern]:
        """
        Recomputes learning patterns from stored experiences.
        """

        snapshot = self.store.load()

        patterns = self.learning.learn(
            snapshot,
        )

        snapshot.patterns = patterns

        self.store.save(
            snapshot,
        )

        return patterns

    ###############################################################
    # Pattern Summary
    ###############################################################

    def patterns_summary(
        self,
    ) -> list[LearningPattern]:
        return self.snapshot().patterns

    ###############################################################
    # Recommendations
    ###############################################################

    def recommendations(
        self,
    ) -> list[str]:
        return self.learning.recommendations(
            self.snapshot(),
        )

    ###############################################################
    # Similarity Search
    ###############################################################

    def similar(
        self,
        embedding: list[float],
        limit: int = 5,
    ):
        return self.vector.search(
            embedding,
            limit,
        )

    ###############################################################
    # Clear
    ###############################################################

    def clear(
        self,
    ) -> None:
        self.store.clear()

        self.vector.clear()

        self.graph.clear()

    ###############################################################
    # Statistics
    ###############################################################

    def statistics(
        self,
    ) -> dict:
        snapshot = self.snapshot()

        return {
            "experiences": len(
                snapshot.experiences,
            ),
            "patterns": len(
                snapshot.patterns,
            ),
            "graph_nodes": (self.graph.node_count()),
            "graph_edges": (self.graph.edge_count()),
            "vectors": (self.vector.count()),
        }
