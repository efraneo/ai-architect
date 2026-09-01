"""
=========================================================
Reviewer Models
=========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Severity(StrEnum):
    INFO = "INFO"

    WARNING = "WARNING"

    ERROR = "ERROR"

    CRITICAL = "CRITICAL"


@dataclass(slots=True)
class ReviewIssue:
    file: str

    line: int

    severity: Severity

    rule: str

    message: str


@dataclass(slots=True)
class ReviewReport:
    issues: list[ReviewIssue] = field(default_factory=list)

    score: float = 100.0

    def add(
        self,
        issue: ReviewIssue,
    ) -> None:

        self.issues.append(issue)

    @property
    def total_issues(
        self,
    ) -> int:

        return len(self.issues)

    @property
    def approved(
        self,
    ) -> bool:

        return not any(
            issue.severity
            in (
                Severity.ERROR,
                Severity.CRITICAL,
            )
            for issue in self.issues
        )
