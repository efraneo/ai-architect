"""
=========================================================
Test Runner Models
=========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class TestStatus(StrEnum):
    PASSED = "PASSED"

    FAILED = "FAILED"

    SKIPPED = "SKIPPED"


@dataclass(slots=True)
class TestCase:
    name: str

    status: TestStatus

    duration: float

    message: str = ""


@dataclass(slots=True)
class TestReport:
    started_at: datetime

    finished_at: datetime | None = None

    tests: list[TestCase] = field(default_factory=list)

    def add(
        self,
        test: TestCase,
    ) -> None:

        self.tests.append(test)

    @property
    def passed(self) -> int:

        return sum(t.status == TestStatus.PASSED for t in self.tests)

    @property
    def failed(self) -> int:

        return sum(t.status == TestStatus.FAILED for t in self.tests)

    @property
    def skipped(self) -> int:

        return sum(t.status == TestStatus.SKIPPED for t in self.tests)

    @property
    def success(self) -> bool:

        return self.failed == 0
