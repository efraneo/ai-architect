"""
Approval Engine.

Coordinates explicit approval decisions for reviewed artifacts.
"""

from __future__ import annotations

from ai_architect.reviewer.approval_state import ApprovalState
from ai_architect.reviewer.models import ReviewReport


class ApprovalEngine:
    """Coordinate explicit approval decisions."""

    def __init__(self) -> None:
        self.state = ApprovalState()

    def evaluate(
        self,
        report: ReviewReport | None,
        patch_id: str = "",
    ) -> bool:
        """
        Evaluate a review report without mutating any Patch.

        A report is approvable only when it exists and is approved.
        """
        if report is None:
            self.reject(
                patch_id,
                "No review report available.",
            )
            return False

        if not report.approved:
            self.reject(
                patch_id,
                "Review report is not approved.",
            )
            return False

        self.approve(
            patch_id,
            "Review report approved.",
        )
        return True

    def approve(
        self,
        patch_id: str,
        reason: str = "",
    ) -> bool:
        """Record an explicit approval decision."""
        self.state.approve(
            patch_id,
            reason,
        )
        return True

    def reject(
        self,
        patch_id: str = "",
        reason: str = "",
    ) -> bool:
        """Record an explicit rejection decision."""
        self.state.reject(
            patch_id,
            reason,
        )
        return False

    def approved(self) -> bool:
        """Return the current approval decision."""
        return self.state.is_approved()

    def has_decision(self) -> bool:
        """Return whether a decision has been recorded."""
        return self.state.has_decision()

    def summary(self) -> dict:
        """Return the current approval summary."""
        return self.state.summary()

    def health(self) -> dict:
        """Return approval subsystem health."""
        return self.state.health()

    def ready(self) -> bool:
        """Return whether the approval engine is ready."""
        return self.state.ready()

    def diagnostics(self) -> dict:
        """Return approval diagnostics."""
        return {
            "engine": self.__class__.__name__,
            "ready": self.ready(),
            "approved": self.approved(),
            "has_decision": self.has_decision(),
        }

    def configuration(self) -> dict:
        """Return approval configuration."""
        return {
            "explicit_approval": True,
            "review_required": True,
            "patch_mutation": False,
            "default_approved": False,
        }

    def version(self) -> str:
        """Return the approval-engine API version."""
        return "1.0"

    def reset(self) -> None:
        """Reset the current approval decision."""
        self.state.reset()

    def export(self) -> dict:
        """Export the current approval state."""
        return self.state.export()

    def import_state(
        self,
        state: dict,
    ) -> None:
        """Restore the approval state."""
        self.state.import_state(
            state,
        )

    def __call__(
        self,
        report: ReviewReport | None,
        patch_id: str = "",
    ) -> bool:
        return self.evaluate(
            report,
            patch_id,
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"state={self.state.__class__.__name__})"
        )

    def __str__(self) -> str:
        return "QUANT AI Architect Approval Engine"
