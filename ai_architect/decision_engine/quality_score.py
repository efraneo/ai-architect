"""
=========================================================
Quality Score

Repository Quality Evaluation
=========================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from ai_architect.core.context import AIContext


@dataclass(slots=True)
class QualityReport:
    """
    Repository quality assessment.
    """

    score: float

    confidence: float

    grade: str

    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:

        return asdict(self)


class QualityScore:
    """
    Calculates repository quality.

    Future integrations:

        • Ruff
        • Black
        • Radon
        • Mypy
        • Pyright
        • Coverage
        • Semgrep
        • Bandit
    """

    MAX_SCORE = 100.0

    def evaluate(
        self,
        context: AIContext,
    ) -> QualityReport:

        metrics = context.metrics

        findings = context.validation.get(
            "findings",
            [],
        )

        tests_ok = context.tests.get(
            "success",
            False,
        )

        score = self.MAX_SCORE

        reasons: list[str] = []

        duplicates = metrics.get(
            "duplicates",
            0,
        )

        if duplicates:
            penalty = duplicates * 2

            score -= penalty

            reasons.append(f"{duplicates} duplicated blocks")

        oversized = metrics.get(
            "oversized_files",
            [],
        )

        oversized_count = (
            len(oversized)
            if isinstance(
                oversized,
                list,
            )
            else oversized
        )

        if oversized_count:
            penalty = oversized_count * 3

            score -= penalty

            reasons.append(f"{oversized_count} oversized files")

        complexity = metrics.get(
            "complexity",
            0,
        )

        if complexity:
            penalty = complexity * 1.5

            score -= penalty

            reasons.append(f"complexity={complexity}")

        security = metrics.get(
            "security_findings",
            0,
        )

        if security:
            penalty = security * 10

            score -= penalty

            reasons.append(f"{security} security findings")

        if findings:
            penalty = len(findings) * 2.5

            score -= penalty

            reasons.append(f"{len(findings)} validation findings")

        if not tests_ok:
            score -= 40

            reasons.append("tests failed")

        score = max(
            0.0,
            round(score, 2),
        )

        confidence = round(
            score / self.MAX_SCORE,
            3,
        )

        return QualityReport(
            score=score,
            confidence=confidence,
            grade=self._grade(score),
            reasons=reasons,
        )

    def acceptable(
        self,
        report: QualityReport,
        minimum: float = 70.0,
    ) -> bool:

        return report.score >= minimum

    def summary(
        self,
        report: QualityReport,
    ) -> str:

        return (
            f"{report.grade} | "
            f"{report.score:.2f}/100 | "
            f"Confidence "
            f"{report.confidence:.3f}"
        )

    @staticmethod
    def _grade(
        score: float,
    ) -> str:

        if score >= 95:
            return "A+"

        if score >= 90:
            return "A"

        if score >= 80:
            return "B"

        if score >= 70:
            return "C"

        if score >= 60:
            return "D"

        return "F"
