"""
=========================================================
Test Runner

Automatic Test Execution
=========================================================
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class TestResult:
    passed: int

    failed: int

    errors: int

    skipped: int

    duration: float

    success: bool

    output: str


class TestRunner:
    def __init__(self):

        self.timeout = 900

    def run(
        self,
        repository: str | Path,
    ) -> TestResult:

        repository = Path(repository).resolve()

        if shutil.which("pytest") is None:
            return TestResult(
                passed=0,
                failed=0,
                errors=1,
                skipped=0,
                duration=0.0,
                success=False,
                output="pytest is not installed.",
            )

        command = [
            "pytest",
            "-q",
        ]

        result = subprocess.run(
            command,
            cwd=repository,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self.timeout,
            check=False,
        )

        output = result.stdout + "\n" + result.stderr

        stats = self._parse(output)

        stats["success"] = result.returncode == 0

        stats["output"] = output

        return TestResult(**stats)

    def run_file(
        self,
        repository: str | Path,
        filename: str,
    ) -> TestResult:

        repository = Path(repository).resolve()

        command = [
            "pytest",
            filename,
            "-q",
        ]

        result = subprocess.run(
            command,
            cwd=repository,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self.timeout,
            check=False,
        )

        output = result.stdout + "\n" + result.stderr

        stats = self._parse(output)

        stats["success"] = result.returncode == 0

        stats["output"] = output

        return TestResult(**stats)

    def _parse(
        self,
        output: str,
    ) -> dict:

        stats = {
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "duration": 0.0,
        }

        for line in output.splitlines():
            line = line.strip()

            if " passed" in line:
                stats["passed"] = self._number(
                    line,
                    "passed",
                )

            if " failed" in line:
                stats["failed"] = self._number(
                    line,
                    "failed",
                )

            if " error" in line:
                stats["errors"] = self._number(
                    line,
                    "error",
                )

            if " errors" in line:
                stats["errors"] = self._number(
                    line,
                    "errors",
                )

            if " skipped" in line:
                stats["skipped"] = self._number(
                    line,
                    "skipped",
                )

            if " in " in line and "s" in line:
                try:
                    duration = line.split(" in ")[1].split("s")[0].strip()

                    stats["duration"] = float(duration)

                except (ValueError, IndexError):
                    # pytest cambia el formato del resumen entre versiones;
                    # sin duración se sigue pudiendo decidir.
                    pass

        return stats

    @staticmethod
    def _number(
        text: str,
        keyword: str,
    ) -> int:

        for token in text.replace(",", " ").split():
            if token.isdigit():
                return int(token)

        return 0
