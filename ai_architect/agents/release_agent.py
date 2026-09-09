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

        # La versión declarada y si el changelog habla de ella.
        declarada = _version_declarada(root)

        if declarada and changelog:
            for nombre in self.CHANGELOGS:
                archivo = root / nombre

                if archivo.exists():
                    try:
                        texto = archivo.read_text(encoding="utf-8", errors="replace")

                    except OSError:
                        texto = ""

                    if declarada not in texto:
                        findings.append(
                            {
                                "type": "changelog_atrasado",
                                "issue": f"el CHANGELOG no menciona la versión {declarada}",
                            }
                        )

                    break

        return {
            "agent": self.name,
            "changelog": changelog,
            "version": version,
            "version_declarada": declarada,
            "release_ready": not findings,
            "findings": findings,
            "status": "OK",
        }

    def capabilities(
        self,
    ) -> list[str]:
        return [
            "publicacion",
            "Changelog Detection",
            "Version Detection",
            "Release Readiness",
        ]


def _version_declarada(root: Path) -> str:
    import re

    for nombre in ("pyproject.toml", "VERSION", "VERSION.txt"):
        archivo = root / nombre

        if not archivo.exists():
            continue

        try:
            texto = archivo.read_text(encoding="utf-8", errors="replace")

        except OSError:
            continue

        if nombre == "pyproject.toml":
            m = re.search(r'^version\s*=\s*"([^"]+)"', texto, re.M)

            return m.group(1) if m else ""

        return texto.strip().splitlines()[0].strip() if texto.strip() else ""

    return ""
