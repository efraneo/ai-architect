"""
Approval Engine
"""

from __future__ import annotations

from typing import Any


class ApprovalEngine:
    def approve(
        self,
        execution: dict[str, Any],
    ) -> bool:
        if not execution.get(
            "tests_ok",
            False,
        ):
            return False

        if (
            execution.get(
                "risk",
                "LOW",
            )
            == "CRITICAL"
        ):
            return False

        confidence = execution.get(
            "confidence",
            0,
        )

        return (
            isinstance(
                confidence,
                (int, float),
            )
            and confidence >= 90
        )
