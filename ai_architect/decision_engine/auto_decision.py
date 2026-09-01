"""
Auto Decision

Institutional Autonomous Decision Coordinator
"""

from __future__ import annotations

from typing import Any

from ai_architect.core.context import AIContext

from .confidence_engine import ConfidenceEngine
from .execution_policy import ExecutionPolicy
from .quality_score import QualityScore
from .risk_engine import RiskEngine
from .scoring_engine import ScoringEngine


class AutoDecision:
    """
    Institutional autonomous decision system.

    Pipeline

        AIContext
             │
             ▼
        Quality Engine
             │
             ▼
         Risk Engine
             │
             ▼
      Confidence Engine
             │
             ▼
       Scoring Engine
             │
             ▼
      Execution Policy
             │
             ▼
        Final Decision
    """

    def __init__(self) -> None:
        self.quality = QualityScore()
        self.risk = RiskEngine()
        self.confidence = ConfidenceEngine()
        self.scoring = ScoringEngine()
        self.policy = ExecutionPolicy()

    def evaluate(
        self,
        context: AIContext,
    ):
        quality = self.quality.evaluate(
            context,
        )

        risk = self.risk.evaluate(
            context,
        )

        confidence = self.confidence.evaluate(
            context,
            quality,
            risk,
        )

        score = self.scoring.evaluate(
            quality,
            confidence,
            risk,
        )

        report = self.policy.evaluate(
            score=score,
            confidence=confidence,
            risk=risk,
            tests_ok=context.tests.get(
                "success",
                False,
            ),
        )

        return report

    def should_commit(
        self,
        report,
    ) -> bool:
        return self.policy.should_commit(
            report,
        )

    def should_retry(
        self,
        report,
    ) -> bool:
        return self.policy.should_retry(
            report,
        )

    def requires_review(
        self,
        report,
    ) -> bool:
        return self.policy.requires_review(
            report,
        )

    def rejected(
        self,
        report,
    ) -> bool:
        return self.policy.rejected(
            report,
        )

    def summary(
        self,
        report,
    ) -> str:
        score = report.metrics.get(
            "score",
            0.0,
        )

        grade = report.metrics.get(
            "grade",
            "-",
        )

        risk = report.metrics.get(
            "risk",
            "-",
        )

        return (
            f"{report.decision.value} | "
            f"Grade={grade} | "
            f"Score={float(score):.2f} | "
            f"Risk={risk} | "
            f"Confidence={report.confidence:.3f}"
        )

    def diagnostics(
        self,
        report,
    ) -> dict[str, Any]:
        data = report.to_dict()

        if isinstance(data, dict):
            return data

        return {
            "decision": report.decision.value,
            "approved": report.approved,
            "confidence": report.confidence,
            "reason": report.reason,
        }
