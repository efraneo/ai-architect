"""State and compatibility helpers for the approval subsystem."""

from __future__ import annotations


class ApprovalState:
    """Store the current explicit approval decision."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        """Reset the approval decision."""
        self.patch_id = ""
        self.approved = False
        self.reason = ""

    def approve(
        self,
        patch_id: str,
        reason: str = "",
    ) -> None:
        """Record an explicit approval decision."""
        self.patch_id = str(patch_id)
        self.approved = True
        self.reason = reason

    def reject(
        self,
        patch_id: str = "",
        reason: str = "",
    ) -> None:
        """Record an explicit rejection decision."""
        self.patch_id = str(patch_id)
        self.approved = False
        self.reason = reason

    def summary(self) -> dict:
        """Return the current approval state."""
        return {
            "patch_id": self.patch_id,
            "approved": self.approved,
            "reason": self.reason,
        }

    def health(self) -> dict:
        """Return the health status of the approval state."""
        return {
            "healthy": True,
            "approved": self.approved,
            "has_patch": bool(self.patch_id),
        }

    def ready(self) -> bool:
        """Return whether the state is initialized."""
        return True

    def diagnostics(self) -> dict:
        """Return diagnostic information."""
        return {
            "engine": self.__class__.__name__,
            "ready": self.ready(),
            "approved": self.approved,
            "has_patch": bool(self.patch_id),
        }

    def configuration(self) -> dict:
        """Return approval-state configuration."""
        return {
            "explicit_approval": True,
            "default_approved": False,
            "reason_supported": True,
        }

    def version(self) -> str:
        """Return the approval-state API version."""
        return "1.0"

    def is_approved(self) -> bool:
        """Return the current approval decision."""
        return self.approved

    def has_decision(self) -> bool:
        """Return whether a patch has an approval decision."""
        return bool(self.patch_id)

    def export(self) -> dict:
        """Export the current approval state."""
        return self.summary()

    def import_state(
        self,
        state: dict,
    ) -> None:
        """Restore approval state from a dictionary."""
        self.patch_id = str(
            state.get(
                "patch_id",
                "",
            )
        )
        self.approved = bool(
            state.get(
                "approved",
                False,
            )
        )
        self.reason = str(
            state.get(
                "reason",
                "",
            )
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"patch_id={self.patch_id!r}, "
            f"approved={self.approved})"
        )

    def __str__(self) -> str:
        return "QUANT AI Architect Approval State"
