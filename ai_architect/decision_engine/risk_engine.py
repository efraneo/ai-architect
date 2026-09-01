"""
Risk Engine

Institutional Repository Risk Assessment.
"""

from __future__ import annotations

from typing import Any

from ai_architect.core.context import AIContext
from ai_architect.core.enums import RiskLevel

from .models import RiskAssessment


class RiskEngine:
    """
    Institutional execution risk evaluator.

    The engine is deterministic. It converts repository,
    validation, and task metrics into a normalized risk score.
    """

    SECURITY_WEIGHT = 60.0
    DUPLICATE_WEIGHT = 5.0
    OVERSIZED_WEIGHT = 5.0
    COMPLEXITY_WEIGHT = 1.5
    VALIDATION_WEIGHT = 3.0
    CORE_WEIGHT = 15.0
    DATABASE_WEIGHT = 10.0
    AUTH_WEIGHT = 20.0
    MAX_SCORE = 100.0

    def evaluate(
        self,
        context: AIContext,
    ) -> RiskAssessment:
        """Evaluate repository execution risk."""

        score = 0.0
        reasons: list[str] = []

        metrics = context.metrics
        validation = context.validation
        task = context.task

        score += self._security(metrics, reasons)
        score += self._duplicates(metrics, reasons)
        score += self._oversized(metrics, reasons)
        score += self._complexity(metrics, reasons)
        score += self._validation(validation, reasons)
        score += self._task(task, reasons)

        score = min(score, self.MAX_SCORE)

        return RiskAssessment(
            score=round(score, 2),
            level=self._level(score),
            reasons=reasons,
        )

    def _security(
        self,
        metrics: dict[str, Any],
        reasons: list[str],
    ) -> float:
        findings = metrics.get("security_findings", 0)

        if not isinstance(findings, (int, float)) or findings <= 0:
            return 0.0

        penalty = min(
            float(findings) * self.SECURITY_WEIGHT,
            60.0,
        )

        reasons.append(f"{findings} security findings")

        return penalty

    def _duplicates(
        self,
        metrics: dict[str, Any],
        reasons: list[str],
    ) -> float:
        duplicates = metrics.get("duplicates", 0)

        if not isinstance(duplicates, (int, float)) or duplicates <= 0:
            return 0.0

        penalty = min(
            float(duplicates) * self.DUPLICATE_WEIGHT,
            15.0,
        )

        reasons.append(f"{duplicates} duplicated blocks")

        return penalty

    def _oversized(
        self,
        metrics: dict[str, Any],
        reasons: list[str],
    ) -> float:
        oversized = metrics.get("oversized_files", [])

        if isinstance(oversized, int):
            total = oversized
        elif isinstance(oversized, (list, tuple, set, dict)):
            total = len(oversized)
        else:
            total = 0

        if total <= 0:
            return 0.0

        penalty = min(
            float(total) * self.OVERSIZED_WEIGHT,
            15.0,
        )

        reasons.append(f"{total} oversized modules")

        return penalty

    def _complexity(
        self,
        metrics: dict[str, Any],
        reasons: list[str],
    ) -> float:
        complexity = metrics.get("complexity")

        if complexity is None:
            complexity = metrics.get("average_complexity", 0)

        if not isinstance(complexity, (int, float)) or complexity <= 0:
            return 0.0

        penalty = min(
            float(complexity) * self.COMPLEXITY_WEIGHT,
            25.0,
        )

        reasons.append(f"complexity={complexity}")

        return penalty

    def _validation(
        self,
        validation: dict[str, Any],
        reasons: list[str],
    ) -> float:
        findings = validation.get("findings", [])

        if not isinstance(findings, (list, tuple, set)):
            return 0.0

        total = len(findings)

        if total == 0:
            return 0.0

        penalty = min(
            float(total) * self.VALIDATION_WEIGHT,
            20.0,
        )

        reasons.append(f"{total} validation findings")

        return penalty

    def _task(
        self,
        task: dict[str, Any],
        reasons: list[str],
    ) -> float:
        penalty = 0.0

        if task.get("touches_core", False) is True:
            penalty += self.CORE_WEIGHT
            reasons.append("Core architecture modified.")

        if task.get("database", False) is True:
            penalty += self.DATABASE_WEIGHT
            reasons.append("Database modification.")

        if task.get("authentication", False) is True:
            penalty += self.AUTH_WEIGHT
            reasons.append("Authentication modified.")

        return penalty

    @staticmethod
    def _level(
        score: float,
    ) -> RiskLevel:
        if score >= 70.0:
            return RiskLevel.CRITICAL

        if score >= 45.0:
            return RiskLevel.HIGH

        if score >= 20.0:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    @staticmethod
    def acceptable(
        report: RiskAssessment,
        threshold: float = 45.0,
    ) -> bool:
        return report.score < threshold

    @staticmethod
    def summary(
        report: RiskAssessment,
    ) -> str:
        return f"Risk={report.level.value} ({report.score:.2f})"
