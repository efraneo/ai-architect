"""
=========================================================
Quality Gate
=========================================================
"""

from __future__ import annotations


class QualityGate:
    def evaluate(
        self,
        tests_ok: bool,
        coverage: float,
    ) -> tuple[bool, str]:

        if not tests_ok:
            return False, "Tests failed"

        if coverage < 80:
            return (
                False,
                "Coverage below 80%",
            )

        return True, "OK"
