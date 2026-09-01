"""
=========================================================
Memory Models

Domain models for the Memory subsystem.
=========================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class ExperienceOutcome(StrEnum):
    """
    Final outcome of an execution.
    """

    SUCCESS = "SUCCESS"

    FAILURE = "FAILURE"

    RETRY = "RETRY"

    MANUAL_REVIEW = "MANUAL_REVIEW"


class ExperienceType(StrEnum):
    """
    Kind of stored experience.
    """

    EXECUTION = "EXECUTION"

    DECISION = "DECISION"

    REFACTOR = "REFACTOR"

    SECURITY = "SECURITY"

    TESTING = "TESTING"

    ARCHITECTURE = "ARCHITECTURE"

    LEARNING = "LEARNING"


@dataclass(slots=True)
class Experience:
    """
    One stored execution experience.
    """

    id: str

    repository: str

    filename: str

    instruction: str

    provider: str

    experience_type: ExperienceType

    outcome: ExperienceOutcome

    confidence: float

    score: float

    risk: float

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    created_at: datetime = field(
        default_factory=datetime.utcnow,
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:

        data = asdict(self)

        data["experience_type"] = self.experience_type.value

        data["outcome"] = self.outcome.value

        data["created_at"] = self.created_at.isoformat()

        return data


@dataclass(slots=True)
class LearningPattern:
    """
    Pattern discovered from previous executions.
    """

    name: str

    description: str

    confidence: float

    occurrences: int

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )


@dataclass(slots=True)
class MemorySnapshot:
    """
    Complete memory state.
    """

    experiences: list[Experience] = field(
        default_factory=list,
    )

    patterns: list[LearningPattern] = field(
        default_factory=list,
    )

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    created_at: datetime = field(
        default_factory=datetime.utcnow,
    )

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "created_at": (self.created_at.isoformat()),
            "experiences": [experience.to_dict() for experience in self.experiences],
            "patterns": [
                {
                    "name": pattern.name,
                    "description": pattern.description,
                    "confidence": pattern.confidence,
                    "occurrences": pattern.occurrences,
                    "metadata": pattern.metadata,
                }
                for pattern in self.patterns
            ],
            "metadata": self.metadata,
        }
