"""
Backend Agent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class BackendAgent:
    def review(
        self,
        project: str,
    ) -> dict[str, Any]:
        root = Path(project)

        modules = len(list(root.rglob("*.py")))

        return {
            "python_modules": modules,
            "status": "OK",
            "recommendation": ("Keep modules under 600 lines."),
        }
