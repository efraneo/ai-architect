"""
=========================================================
Patch Validator

Institutional Patch Validator
=========================================================
"""

from __future__ import annotations

from ai_architect.patch_generator.models import Patch


class PatchValidator:
    """
    Validates generated patches before execution.

    Structural validity and approval are intentionally
    treated as separate concepts.
    """

    # ========================================================
    # Approval
    # ========================================================

    def approved(
        self,
        patch: Patch,
    ) -> bool:
        if patch is None:
            return False

        if not patch.approved:
            return False

        return self.validate_structure(
            patch,
        )

    # ========================================================
    # Validation
    # ========================================================

    def validate(
        self,
        patch: Patch,
    ) -> dict:
        structural = self.validate_structure(
            patch,
        )

        if patch is None:
            return {
                "approved": False,
                "structurally_valid": False,
                "files": 0,
                "has_diff": False,
            }

        return {
            "approved": self.approved(
                patch,
            ),
            "structurally_valid": structural,
            "files": patch.total_files,
            "has_diff": self.validate_diff(
                patch,
            ),
        }

    # ========================================================
    # Diff
    # ========================================================

    def validate_diff(
        self,
        patch: Patch,
    ) -> bool:
        if patch is None:
            return False

        return bool(
            patch.diff.strip(),
        )

    # ========================================================
    # Metadata
    # ========================================================

    def validate_metadata(
        self,
        patch: Patch,
    ) -> bool:
        if patch is None:
            return False

        return all(
            (
                bool(patch.id),
                bool(patch.title.strip()),
                bool(patch.description.strip()),
                patch.created_at is not None,
            )
        )

    # ========================================================
    # Files
    # ========================================================

    def validate_files(
        self,
        patch: Patch,
    ) -> bool:
        if patch is None:
            return False

        if not patch.files:
            return False

        for item in patch.files:
            if not item.path:
                return False

            if not item.action:
                return False

            if item.additions < 0:
                return False

            if item.deletions < 0:
                return False

        return True

    # ========================================================
    # Actions
    # ========================================================

    def validate_actions(
        self,
        patch: Patch,
    ) -> bool:
        if patch is None:
            return False

        valid = {
            "CREATE",
            "MODIFY",
            "DELETE",
        }

        return all(str(item.action).upper() in valid for item in patch.files)

    # ========================================================
    # Structural Validation
    # ========================================================

    def validate_structure(
        self,
        patch: Patch,
    ) -> bool:
        if patch is None:
            return False

        return (
            self.validate_metadata(
                patch,
            )
            and self.validate_files(
                patch,
            )
            and self.validate_actions(
                patch,
            )
            and self.validate_diff(
                patch,
            )
        )

    # ========================================================
    # Issues
    # ========================================================

    def issues(
        self,
        patch: Patch,
    ) -> list[str]:
        errors: list[str] = []

        if not self.validate_metadata(
            patch,
        ):
            errors.append(
                "Invalid metadata.",
            )

        if not self.validate_files(
            patch,
        ):
            errors.append(
                "Invalid file list.",
            )

        if not self.validate_actions(
            patch,
        ):
            errors.append(
                "Unsupported patch action.",
            )

        if not self.validate_diff(
            patch,
        ):
            errors.append(
                "Missing patch diff.",
            )

        if patch is not None and not patch.approved:
            errors.append(
                "Patch is not approved.",
            )

        return errors

    # ========================================================
    # Report
    # ========================================================

    def report(
        self,
        patch: Patch,
    ) -> dict:
        errors = self.issues(
            patch,
        )

        return {
            "approved": len(errors) == 0,
            "errors": errors,
            "total_errors": len(errors),
        }

    # ========================================================
    # Summary
    # ========================================================

    def summary(
        self,
        patch: Patch,
    ) -> dict:
        if patch is None:
            return {
                "id": "",
                "approved": False,
                "structurally_valid": False,
                "files": 0,
            }

        return {
            "id": patch.id,
            "approved": self.approved(
                patch,
            ),
            "structurally_valid": self.validate_structure(
                patch,
            ),
            "files": patch.total_files,
        }

    # ========================================================
    # Score
    # ========================================================

    def score(
        self,
        patch: Patch,
    ) -> float:
        deductions = (
            len(
                self.issues(
                    patch,
                )
            )
            * 25
        )

        return max(
            0.0,
            100.0 - deductions,
        )

    # ========================================================
    # Statistics
    # ========================================================

    def statistics(
        self,
    ) -> dict:
        return {
            "validator": self.__class__.__name__,
            "supported_actions": [
                "CREATE",
                "MODIFY",
                "DELETE",
            ],
        }

    def health(
        self,
    ) -> dict:
        return {
            "healthy": True,
            "ready": True,
        }

    def configuration(
        self,
    ) -> dict:
        return {
            "require_diff": True,
            "require_metadata": True,
            "require_files": True,
            "strict_actions": True,
            "require_approval": True,
        }

    # ========================================================
    # Version
    # ========================================================

    def version(
        self,
    ) -> str:
        return "1.2"

    # ========================================================
    # Convenience
    # ========================================================

    def __call__(
        self,
        patch: Patch,
    ) -> bool:
        return self.approved(
            patch,
        )

    # ========================================================

    def __repr__(
        self,
    ) -> str:
        return f"{self.__class__.__name__}()"

    def __str__(
        self,
    ) -> str:
        return "QUANT AI Architect Patch Validator"
