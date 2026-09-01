"""
Confidence Engine

Institutional Decision Confidence Engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ai_architect.core.context import AIContext
from ai_architect.core.enums import Confidence

from .quality_score import QualityReport
from .risk_engine import RiskAssessment


@dataclass(slots=True)
class ConfidenceReport:
    """Final confidence evaluation."""

    value: float
    level: Confidence
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "value": self.value,
            "level": self.level.value,
            "reasons": list(self.reasons),
        }


class ConfidenceEngine:
    """
    Calculates execution confidence.

    Inputs:
        - Repository quality
        - Repository risk
        - Validation
        - Tests
        - Learning

    Output:
        ConfidenceReport
    """

    TEST_FAILURE = 0.20
    VALIDATION_WEIGHT = 0.03
    MAX_VALIDATION = 0.20
    HIGH_LEARNING_BONUS = 0.05
    LOW_LEARNING_PENALTY = 0.05

    def evaluate(
        self,
        context: AIContext,
        quality: QualityReport,
        risk: RiskAssessment,
    ) -> ConfidenceReport:
        """Calculate normalized execution confidence."""

        confidence = quality.score / 100.0
        reasons: list[str] = []

        confidence -= risk.score / 200.0

        reasons.extend(risk.reasons)

        confidence += self._tests(
            context,
            reasons,
        )

        confidence += self._validation(
            context,
            reasons,
        )

        confidence += self._learning(
            context,
            reasons,
        )

        confidence = max(
            0.0,
            min(
                1.0,
                round(confidence, 3),
            ),
        )

        return ConfidenceReport(
            value=confidence,
            level=self._level(confidence),
            reasons=reasons,
        )

    def _tests(
        self,
        context: AIContext,
        reasons: list[str],
    ) -> float:
        tests = context.tests

        if tests.get("success", False) is True:
            return 0.0

        reasons.append("Tests failed.")

        return -self.TEST_FAILURE

    def _validation(
        self,
        context: AIContext,
        reasons: list[str],
    ) -> float:
        findings = context.validation.get(
            "findings",
            [],
        )

        if not isinstance(findings, (list, tuple, set)):
            return 0.0

        total = len(findings)

        if total == 0:
            return 0.0

        penalty = min(
            total * self.VALIDATION_WEIGHT,
            self.MAX_VALIDATION,
        )

        reasons.append(
            f"{total} validation findings.",
        )

        return -penalty

    def _learning(
        self,
        context: AIContext,
        reasons: list[str],
    ) -> float:
        learning = context.learning

        if not learning:
            return 0.0

        success_rate = learning.get("success_rate")

        if not isinstance(success_rate, (int, float)):
            return 0.0

        if success_rate >= 90.0:
            reasons.append(
                "Excellent historical performance.",
            )
            return self.HIGH_LEARNING_BONUS

        if success_rate < 50.0:
            reasons.append(
                "Low historical performance.",
            )
            return -self.LOW_LEARNING_PENALTY

        return 0.0

    @staticmethod
    def _level(
        value: float,
    ) -> Confidence:
        if value >= 0.95:
            return Confidence.VERY_HIGH

        if value >= 0.80:
            return Confidence.HIGH

        if value >= 0.60:
            return Confidence.MEDIUM

        if value >= 0.40:
            return Confidence.LOW

        return Confidence.VERY_LOW

    @staticmethod
    def acceptable(
        report: ConfidenceReport,
        minimum: float = 0.70,
    ) -> bool:
        return report.value >= minimum

    @staticmethod
    def summary(
        report: ConfidenceReport,
    ) -> str:
        return f"Confidence={report.level.value} ({report.value:.3f})"
