"""
=========================================================
Execution Policy

Institutional Execution Policy
=========================================================
"""

from __future__ import annotations

from ai_architect.core.enums import RiskLevel

from .confidence_engine import ConfidenceReport
from .decision_report import (
    DecisionReport,
    DecisionType,
)
from .models import RiskAssessment
from .scoring_engine import ScoreReport


class ExecutionPolicy:
    """
    Institutional execution policy.

    This class represents the single source of truth
    for every autonomous execution decision.

    Possible outcomes

        • ACCEPT
        • RETRY
        • MANUAL_REVIEW
        • REJECT
    """

    ##############################################################
    # Thresholds
    ##############################################################

    MIN_SCORE = 70.0

    MANUAL_SCORE = 85.0

    HIGH_CONFIDENCE = 0.90

    MIN_CONFIDENCE = 0.70

    ##############################################################

    def evaluate(
        self,
        score: ScoreReport,
        confidence: ConfidenceReport,
        risk: RiskAssessment,
        tests_ok: bool,
    ) -> DecisionReport:

        decision = self._decision(
            score,
            confidence,
            risk,
            tests_ok,
        )

        return DecisionReport(
            decision=decision,
            approved=decision == DecisionType.ACCEPT,
            confidence=confidence.value,
            reason=self._reason(
                decision,
                score,
                confidence,
                risk,
                tests_ok,
            ),
            findings=[],
            metrics={
                "score": score.score,
                "grade": score.grade,
                "risk": risk.level.value,
            },
        )

    ##############################################################

    def _decision(
        self,
        score: ScoreReport,
        confidence: ConfidenceReport,
        risk: RiskAssessment,
        tests_ok: bool,
    ) -> DecisionType:

        #
        # Tests always win.
        #

        if not tests_ok:
            return DecisionType.REJECT

        #
        # Critical risk.
        #

        if risk.level == RiskLevel.CRITICAL:
            return DecisionType.REJECT

        #
        # High risk.
        #

        if risk.level == RiskLevel.HIGH:
            if (
                score.score >= self.MANUAL_SCORE
                and confidence.value >= self.HIGH_CONFIDENCE
            ):
                return DecisionType.MANUAL_REVIEW

            return DecisionType.RETRY

        #
        # Repository score.
        #

        if score.score >= 90 and confidence.value >= self.MIN_CONFIDENCE:
            return DecisionType.ACCEPT

        if score.score >= self.MIN_SCORE:
            return DecisionType.MANUAL_REVIEW

        if score.score >= 55:
            return DecisionType.RETRY

        return DecisionType.REJECT

    ##############################################################

    @staticmethod
    def _reason(
        decision: DecisionType,
        score: ScoreReport,
        confidence: ConfidenceReport,
        risk: RiskAssessment,
        tests_ok: bool,
    ) -> str:

        if not tests_ok:
            return "Unit tests failed."

        if decision == DecisionType.ACCEPT:
            return (
                f"Repository grade {score.grade} "
                f"with {risk.level.value} risk "
                f"and confidence "
                f"{confidence.value:.3f}."
            )

        if decision == DecisionType.MANUAL_REVIEW:
            return "Manual validation is recommended before committing changes."

        if decision == DecisionType.RETRY:
            return "Generate another implementation to improve repository quality."

        return "Repository does not satisfy institutional execution policy."

    ##############################################################

    @staticmethod
    def should_commit(
        report: DecisionReport,
    ) -> bool:

        return report.accepted

    ##############################################################

    @staticmethod
    def should_retry(
        report: DecisionReport,
    ) -> bool:

        return report.retry_required

    ##############################################################

    @staticmethod
    def requires_review(
        report: DecisionReport,
    ) -> bool:

        return report.manual_review

    ##############################################################

    @staticmethod
    def rejected(
        report: DecisionReport,
    ) -> bool:

        return report.rejected

    ##############################################################

    @staticmethod
    def summary(
        report: DecisionReport,
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
            f"Score={score:.2f} | "
            f"Risk={risk} | "
            f"Confidence={report.confidence:.3f}"
        )
