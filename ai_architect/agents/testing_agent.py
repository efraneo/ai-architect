from __future__ import annotations

from pathlib import Path
from typing import Any

from .base_agent import BaseAgent


class TestingAgent(BaseAgent):
    name = "Testing Agent"

    def review(
        self,
        project: str,
    ) -> dict[str, Any]:
        project_path = Path(project)

        test_files = list(
            project_path.rglob(
                "test_*.py",
            )
        )

        pytest_files = list(
            project_path.rglob(
                "*pytest*.py",
            )
        )

        unittest_files = list(
            project_path.rglob(
                "*unittest*.py",
            )
        )

        source_files = list(
            project_path.rglob(
                "*.py",
            )
        )

        production = [file for file in source_files if "test" not in file.name.lower()]

        coverage = min(
            len(test_files) * 5,
            100,
        )

        missing = max(
            0,
            len(production) - len(test_files),
        )

        return {
            "python_files": len(source_files),
            "production_files": len(production),
            "tests": len(test_files),
            "pytest_files": len(pytest_files),
            "unittest_files": len(unittest_files),
            "coverage_estimate": coverage,
            "missing_tests": missing,
            "status": "OK",
        }

    def run(
        self,
        context,
    ):
        return self.review(context)
