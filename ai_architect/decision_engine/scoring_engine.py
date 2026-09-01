"""
Scoring Engine

Institutional Decision Scoring Engine.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .confidence_engine import ConfidenceReport
from .quality_score import QualityReport
from .risk_engine import RiskAssessment


@dataclass(slots=True)
class ScoreReport:
    """Final institutional repository score."""

    score: float
    approved: bool
    quality: float
    confidence: float
    risk: float
    grade: str
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return asdict(self)


class ScoringEngine:
    """
    Final scoring engine.

    Formula:

        Quality ............. 45%
        Confidence .......... 35%
        Risk ................ 20% inverse

    Result:
        0 -> 100
    """

    QUALITY_WEIGHT = 0.45
    CONFIDENCE_WEIGHT = 0.35
    RISK_WEIGHT = 0.20

    APPROVAL_SCORE = 70.0

    def evaluate(
        self,
        quality: QualityReport,
        confidence: ConfidenceReport,
        risk: RiskAssessment,
    ) -> ScoreReport:
        """Calculate the final institutional score."""

        quality_score = float(quality.score)

        confidence_score = confidence.value * 100.0

        risk_score = max(
            0.0,
            100.0 - risk.score,
        )

        final_score = (
            quality_score * self.QUALITY_WEIGHT
            + confidence_score * self.CONFIDENCE_WEIGHT
            + risk_score * self.RISK_WEIGHT
        )

        final_score = round(
            final_score,
            2,
        )

        reasons: list[str] = []

        reasons.extend(quality.reasons)
        reasons.extend(confidence.reasons)
        reasons.extend(risk.reasons)

        return ScoreReport(
            score=final_score,
            approved=final_score >= self.APPROVAL_SCORE,
            quality=round(quality_score, 2),
            confidence=round(confidence_score, 2),
            risk=round(risk_score, 2),
            grade=self._grade(final_score),
            reasons=self._deduplicate(reasons),
        )

    @staticmethod
    def _deduplicate(
        reasons: list[str],
    ) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []

        for reason in reasons:
            if reason in seen:
                continue

            seen.add(reason)
            result.append(reason)

        return result

    @staticmethod
    def _grade(
        score: float,
    ) -> str:
        if score >= 97.0:
            return "A+"

        if score >= 92.0:
            return "A"

        if score >= 85.0:
            return "B"

        if score >= 75.0:
            return "C"

        if score >= 65.0:
            return "D"

        return "F"

    @staticmethod
    def acceptable(
        report: ScoreReport,
        minimum: float = 70.0,
    ) -> bool:
        return report.score >= minimum

    @staticmethod
    def summary(
        report: ScoreReport,
    ) -> str:
        return (
            f"Score={report.score:.2f} "
            f"| Grade={report.grade} "
            f"| Quality={report.quality:.1f} "
            f"| Confidence={report.confidence:.1f} "
            f"| Risk={report.risk:.1f}"
        )
