"""
=========================================================
Empaquetado Agent

Que lo que se instala sea lo que hay en el código: versión, spec e instalador.
=========================================================
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .base_agent import BaseAgent
from .herramientas_externas import correr, hay


class EmpaquetadoAgent(BaseAgent):
    name = "Empaquetado Agent"

    def run(self, context):
        return self.review(context)

    def review(self, project: str) -> dict[str, Any]:
        raiz = Path(project)
        findings: list[dict[str, Any]] = []
        informe: dict[str, Any] = {"agent": self.name, "status": "OK"}

        version_py = _version(raiz / "pyproject.toml", r'^version\s*=\s*"([^"]+)"')
        version_iss = _version(
            raiz / "instalador.iss", r'#define\s+Version\s+"([^"]+)"'
        )
        informe["version_pyproject"] = version_py
        informe["version_instalador"] = version_iss

        if version_py and version_iss and version_py != version_iss:
            findings.append(
                {
                    "type": "version",
                    "issue": f"pyproject dice {version_py} y el instalador {version_iss}",
                }
            )

        spec = raiz / "arquitecto.spec"

        if spec.is_file():
            texto = spec.read_text(encoding="utf-8", errors="replace")
            informe["spec_recoge_todo"] = "collect_submodules" in texto

            if "collect_submodules" not in texto:
                findings.append(
                    {
                        "type": "spec",
                        "issue": "el .spec no recoge todos los módulos (collect_submodules)",
                    }
                )

        instalador = raiz / "salida" / "ArquitectoSetup.exe"

        if instalador.is_file():
            fecha = datetime.fromtimestamp(instalador.stat().st_mtime)
            informe["instalador"] = fecha.strftime("%Y-%m-%d %H:%M")

            ultimo = _ultimo_commit(raiz)

            if ultimo and ultimo > fecha:
                findings.append(
                    {
                        "type": "instalador",
                        "issue": (
                            f"el instalador es del {fecha:%d/%m %H:%M} y hay commits posteriores "
                            f"({ultimo:%d/%m %H:%M}): reconstruir"
                        ),
                    }
                )

        else:
            informe["instalador"] = None

        if version_py and hay("git"):
            codigo, out, _ = correr(
                ["git", "tag", "--list", f"v{version_py}"], raiz, 30
            )
            informe["etiqueta"] = bool(out.strip())

            if codigo == 0 and not out.strip():
                findings.append(
                    {
                        "type": "etiqueta",
                        "issue": f"no hay etiqueta v{version_py} en git",
                    }
                )

        informe["findings"] = findings

        return informe

    def capabilities(self) -> list[str]:
        return [
            "empaquetado",
            "version coherente (pyproject e instalador)",
            "spec de PyInstaller completo",
            "instalador al dia respecto al codigo",
            "etiqueta de version en git",
        ]


def _version(archivo: Path, patron: str) -> str:
    try:
        m = re.search(
            patron, archivo.read_text(encoding="utf-8", errors="replace"), re.M
        )

    except OSError:
        return ""

    return m.group(1) if m else ""


def _ultimo_commit(raiz: Path) -> datetime | None:
    if not hay("git"):
        return None

    codigo, out, _ = correr(["git", "log", "-1", "--format=%ct"], raiz, 30)

    if codigo != 0 or not out.strip().isdigit():
        return None

    return datetime.fromtimestamp(int(out.strip()))
