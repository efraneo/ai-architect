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
from .herramientas_externas import correr_json, hay


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

        ci_github = self._ci_en_github(Path(project))

        if ci_github and ci_github.get("conclusion") == "failure":
            findings.append(
                {
                    "type": "ci",
                    "issue": f"el último run de GitHub Actions falló: {ci_github.get('displayTitle', '')[:80]}",
                }
            )

        return {
            "ci_github": ci_github,
            "agent": self.name,
            "docker": docker,
            "continuous_integration": ci,
            "pyproject": empaquetado,
            "findings": findings,
            "status": "OK",
        }

    def _ci_en_github(self, raiz: Path) -> dict[str, Any] | None:
        """El último run de GitHub Actions, si `gh` está y el repo tiene remoto."""
        if not hay("gh"):
            return None

        datos = correr_json(
            [
                "gh",
                "run",
                "list",
                "--limit",
                "1",
                "--json",
                "conclusion,status,displayTitle,createdAt",
            ],
            raiz,
            60,
        )

        if not isinstance(datos, list) or not datos:
            return None

        return dict(datos[0])

    def capabilities(
        self,
    ) -> list[str]:
        return [
            "devops",
            "Docker Detection",
            "CI Detection",
            "Packaging Detection",
            "ultimo resultado de GitHub Actions (gh)",
        ]
