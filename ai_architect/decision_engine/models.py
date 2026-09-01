"""
=========================================================
Decision Engine Models

Shared domain models for the Decision Engine.
=========================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ai_architect.core.enums import (
    Confidence,
    Decision,
    RiskLevel,
)


@dataclass(slots=True)
class QualityAssessment:
    """
    Repository quality evaluation.
    """

    score: float

    confidence: float

    grade: str

    reasons: list[str] = field(
        default_factory=list,
    )

    def to_dict(self) -> dict[str, Any]:

        return asdict(self)


@dataclass(slots=True)
class RiskAssessment:
    """
    Repository execution risk.
    """

    score: float

    level: RiskLevel

    reasons: list[str] = field(
        default_factory=list,
    )

    def to_dict(self) -> dict[str, Any]:

        data = asdict(self)

        data["level"] = self.level.value

        return data


@dataclass(slots=True)
class ConfidenceAssessment:
    """
    Final confidence after all evaluations.
    """

    value: float

    level: Confidence

    reasons: list[str] = field(
        default_factory=list,
    )

    def to_dict(self) -> dict[str, Any]:

        data = asdict(self)

        data["level"] = self.level.value

        return data


@dataclass(slots=True)
class ScoreAssessment:
    """
    Weighted score used for decision making.
    """

    score: float

    approved: bool

    quality: float

    confidence: float

    risk: float

    reasons: list[str] = field(
        default_factory=list,
    )

    def to_dict(self) -> dict[str, Any]:

        return asdict(self)


@dataclass(slots=True)
class PolicyDecision:
    """
    Result after applying execution policies.
    """

    decision: Decision

    approved: bool

    minimum_confidence: float

    reason: str

    def to_dict(self) -> dict[str, Any]:

        data = asdict(self)

        data["decision"] = self.decision.value

        return data


@dataclass(slots=True)
class DecisionReport:
    """
    Final decision returned by the Decision Engine.
    """

    decision: Decision

    approved: bool

    quality: QualityAssessment

    risk: RiskAssessment

    confidence: ConfidenceAssessment

    score: ScoreAssessment

    policy: PolicyDecision

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    def to_dict(self) -> dict[str, Any]:

        return {
            "decision": self.decision.value,
            "approved": self.approved,
            "quality": self.quality.to_dict(),
            "risk": self.risk.to_dict(),
            "confidence": self.confidence.to_dict(),
            "score": self.score.to_dict(),
            "policy": self.policy.to_dict(),
            "metadata": self.metadata,
        }
