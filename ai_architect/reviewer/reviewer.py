"""
=========================================================
Reviewer

High-level Reviewer facade.

Coordinates review and approval evaluation without
mutating Patch approval state.
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from ai_architect.reviewer.approval_engine import ApprovalEngine
from ai_architect.reviewer.models import ReviewReport
from ai_architect.reviewer.review_engine import ReviewEngine


class Reviewer:
    """High-level coordinator for review and approval evaluation."""

    def __init__(self) -> None:
        self.engine = ReviewEngine()
        self.approval = ApprovalEngine()

    def review(
        self,
        repository: str | Path,
    ) -> ReviewReport:
        """Review a repository and store the resulting report."""
        report = self.engine.review(repository)
        self.approval.reset()
        return report

    def evaluate(
        self,
        report: ReviewReport | None,
        patch_id: str = "",
    ) -> bool:
        """
        Evaluate whether a review report is approvable.

        This operation does not mutate a Patch object.
        """
        return self.approval.evaluate(
            report,
            patch_id,
        )

    def review_and_evaluate(
        self,
        repository: str | Path,
        patch_id: str = "",
    ) -> ReviewReport:
        """
        Review a repository and evaluate its approval state.

        The resulting ReviewReport is returned. The approval
        decision is available through the approval subsystem.
        """
        report = self.review(repository)

        self.evaluate(
            report,
            patch_id,
        )

        return report

    def approved(self) -> bool:
        """Return the current approval decision."""
        return self.approval.approved()

    def has_decision(self) -> bool:
        """Return whether an approval decision exists."""
        return self.approval.has_decision()

    def summary(self) -> dict:
        """Return the combined reviewer summary."""
        return {
            "review": self.engine.summary(),
            "approval": self.approval.summary(),
        }

    def statistics(self) -> dict:
        """Return combined reviewer statistics."""
        review_stats = self.engine.statistics()

        return {
            **review_stats,
            "approval": self.approval.summary(),
        }

    def health(self) -> dict:
        """Return the health of the complete reviewer subsystem."""
        review_health = self.engine.health()
        approval_health = self.approval.health()

        return {
            "review": review_health,
            "approval": approval_health,
            "healthy": bool(
                review_health.get("healthy", False)
                and approval_health.get("healthy", False)
            ),
        }

    def ready(self) -> bool:
        """Return whether all reviewer components are ready."""
        return bool(self.engine.ready() and self.approval.ready())

    def configuration(self) -> dict:
        """Return reviewer configuration."""
        return {
            "review_engine": self.engine.__class__.__name__,
            "approval_engine": self.approval.__class__.__name__,
            "approval_mutates_patch": False,
        }

    def diagnostics(self) -> dict:
        """Return reviewer diagnostics."""
        return {
            "engine": self.__class__.__name__,
            "ready": self.ready(),
            "approved": self.approved(),
            "has_decision": self.has_decision(),
            "review": self.engine.diagnostics(),
            "approval": self.approval.diagnostics(),
        }

    def reset(self) -> None:
        """Reset review and approval state."""
        self.engine.reset()
        self.approval.reset()

    def version(self) -> str:
        """Return the Reviewer API version."""
        return "1.0"

    def __call__(
        self,
        repository: str | Path,
    ) -> ReviewReport:
        return self.review(repository)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"engine={self.engine.__class__.__name__}, "
            f"approval={self.approval.__class__.__name__})"
        )

    def __str__(self) -> str:
        return "QUANT AI Architect Reviewer"
