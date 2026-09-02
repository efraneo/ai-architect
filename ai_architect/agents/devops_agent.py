"""
=========================================================
DevOps Agent

Containerisation, CI and packaging.
=========================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base_agent import BaseAgent


class DevOpsAgent(BaseAgent):
    name = "DevOps Agent"

    def run(
        self,
        context,
    ):
        return self.review(
            context,
        )

    def review(
        self,
        project: str,
    ) -> dict[str, Any]:
        root = Path(project)

        docker = (root / "Dockerfile").exists()

        workflows = root / ".github" / "workflows"

        ci = workflows.is_dir() and any(
            workflows.glob("*.yml"),
        )

        empaquetado = (root / "pyproject.toml").exists()

        findings: list[dict[str, str]] = []

        if not ci:
            findings.append(
                {
                    "type": "sin_ci",
                    "issue": "no hay flujos de trabajo en .github/workflows",
                }
            )

        if not empaquetado:
            findings.append(
                {
                    "type": "sin_pyproject",
                    "issue": "no hay pyproject.toml: el proyecto no se puede empaquetar",
                }
            )

        return {
            "agent": self.name,
            "docker": docker,
            "continuous_integration": ci,
            "pyproject": empaquetado,
            "findings": findings,
            "status": "OK",
        }

    def capabilities(
        self,
    ) -> list[str]:
        return [
            "devops",
            "Docker Detection",
            "CI Detection",
            "Packaging Detection",
        ]
