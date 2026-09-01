"""
=========================================================
Release Agent

What has to be in place before publishing.
=========================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base_agent import BaseAgent


class ReleaseAgent(BaseAgent):
    name = "Release Agent"

    CHANGELOGS = ("CHANGELOG.md", "CHANGELOG", "CHANGELOG.rst")

    VERSIONES = ("VERSION", "VERSION.txt")

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

        def alguno(nombres: tuple[str, ...]) -> bool:
            return any((root / nombre).exists() for nombre in nombres)

        changelog = alguno(self.CHANGELOGS)

        # A version in pyproject.toml counts: not every project keeps a
        # VERSION file, and the Licence Agent already covers the licence.
        version = alguno(self.VERSIONES) or (root / "pyproject.toml").exists()

        findings: list[dict[str, str]] = []

        if not changelog:
            findings.append(
                {
                    "type": "sin_changelog",
                    "issue": "no hay CHANGELOG: nadie sabe qué cambió entre versiones",
                }
            )

        if not version:
            findings.append(
                {
                    "type": "sin_version",
                    "issue": "no hay versión declarada",
                }
            )

        return {
            "agent": self.name,
            "changelog": changelog,
            "version": version,
            "release_ready": not findings,
            "findings": findings,
            "status": "OK",
        }

    def capabilities(
        self,
    ) -> list[str]:
        return [
            "Changelog Detection",
            "Version Detection",
            "Release Readiness",
        ]
