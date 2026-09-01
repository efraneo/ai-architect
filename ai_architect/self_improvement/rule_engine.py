"""
=========================================================
Rule Engine
=========================================================
"""

from __future__ import annotations


class RuleEngine:
    def __init__(self):

        self.rules = [
            {
                "name": "MAX_FILE_LINES",
                "value": 600,
            },
            {
                "name": "MAX_COMPLEXITY",
                "value": 10,
            },
            {
                "name": "TESTS_REQUIRED",
                "value": True,
            },
            {
                "name": "AUTO_CHANGELOG",
                "value": True,
            },
            {
                "name": "BRANCH_REQUIRED",
                "value": True,
            },
        ]

    def validate(
        self,
        file_lines: int,
        complexity: int,
    ):

        violations = []

        if file_lines > 600:
            violations.append("MAX_FILE_LINES")

        if complexity > 10:
            violations.append("MAX_COMPLEXITY")

        return violations

    def all(self):

        return self.rules
