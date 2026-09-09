from __future__ import annotations

from pathlib import Path
from typing import Any

from .base_agent import BaseAgent
from .herramientas_externas import correr_json, python_de


class DependencyAgent(BaseAgent):
    name = "Dependency Agent"

    def _desactualizados(self, raiz: Path) -> list[dict[str, Any]]:
        """``pip list --outdated`` en el intérprete del proyecto (los diez primeros)."""
        datos = correr_json(
            [
                python_de(raiz),
                "-m",
                "pip",
                "list",
                "--outdated",
                "--format",
                "json",
                "--disable-pip-version-check",
            ],
            raiz,
            90,
        )

        if not isinstance(datos, list):
            return []

        return [
            {
                "type": "desactualizado",
                "issue": f"{d.get('name')} {d.get('version')} → hay {d.get('latest_version')}",
            }
            for d in datos[:10]
            if isinstance(d, dict)
        ]

    def capabilities(self) -> list[str]:
        """Lo que sabe hacer, dicho para que el director reparta solo.

        Estaba vacio en todos los agentes, y por eso el director tenia la
        lista escrita a mano en otro archivo: dos sitios que se
        desincronizan en cuanto alguien anade un agente.
        """
        return [
            "dependencias",
            "librerias y versiones",
            "vulnerabilidades conocidas de los paquetes",
            "licencias",
            "paquetes desactualizados (pip list --outdated)",
        ]

    DEPENDENCY_FILES = [
        "requirements.txt",
        "pyproject.toml",
        "poetry.lock",
        "Pipfile",
        "Pipfile.lock",
        "setup.py",
        "setup.cfg",
    ]

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
        project_path = Path(project)

        dependencies: list[str] = []
        dependency_files: list[str] = []

        for filename in self.DEPENDENCY_FILES:
            file = project_path / filename

            if not file.exists():
                continue

            dependency_files.append(str(file))

            try:
                lines = file.read_text(
                    encoding="utf-8",
                    errors="ignore",
                ).splitlines()

            except Exception:
                continue

            for line in lines:
                line = line.strip()

                if not line or line.startswith("#") or line.startswith("["):
                    continue

                dependencies.append(line)

        # Fallos publicados de verdad, no "hay librerias antiguas". Eso
        # ultimo vale para cualquier proyecto de mas de un ano y no dice
        # si hay que hacer algo hoy.
        from ai_architect.herramientas import cve

        vulnerabilidades = cve.revisar(project)

        return {
            "agent": self.name,
            "dependency_files": dependency_files,
            "dependency_count": len(dependencies),
            "dependencies": sorted(set(dependencies)),
            "vulnerabilities": vulnerabilidades["vulnerables"],
            "vulnerability_detail": vulnerabilidades.get("detalle", []),
            "vulnerability_note": vulnerabilidades["nota"],
            "desactualizados": self._desactualizados(project_path),
            "findings": [
                *self._desactualizados(project_path),
                *(
                    f"{v['paquete']} {v['version']}: {', '.join(v['fallos'][:3])}"
                    for v in vulnerabilidades["vulnerables"]
                ),
            ],
            "status": "OK" if dependency_files else "NOT_FOUND",
        }
