"""
=========================================================
Decision Context

Decision Engine Shared Context
=========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ai_architect.decision_engine.confidence_engine import (
    ConfidenceReport,
)
from ai_architect.decision_engine.models import RiskAssessment
from ai_architect.decision_engine.scoring_engine import (
    ScoreReport,
)
from ai_architect.execution.repository_metrics import (
    RepositoryMetrics,
)


@dataclass(slots=True)
class DecisionContext:
    """
    Shared context used across the Decision Engine.
    """

    repository: str = ""

    provider: str = ""

    score: ScoreReport | None = None

    confidence: ConfidenceReport | None = None

    risk: RiskAssessment | None = None

    metrics: RepositoryMetrics = field(
        default_factory=RepositoryMetrics,
    )

    tests_ok: bool = False

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    def add_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:

        self.metadata[key] = value
