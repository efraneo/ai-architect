"""
=========================================================
Bug Hunter Agent
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from .base_agent import BaseAgent


class BugHunterAgent(BaseAgent):
    name = "Bug Hunter Agent"

    PATTERNS = (
        "except:",
        "pass",
        "todo",
        "fixme",
        "print(",
    )

    def review(
        self,
        project: str,
    ) -> dict:

        findings = []

        for file in Path(project).rglob("*.py"):
            source = file.read_text(
                encoding="utf-8",
                errors="ignore",
            ).lower()

            for pattern in self.PATTERNS:
                if pattern in source:
                    findings.append(
                        {
                            "file": str(file),
                            "pattern": pattern,
                        }
                    )

        return {
            "issues": findings,
            "total": len(findings),
        }
