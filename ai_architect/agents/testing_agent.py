from __future__ import annotations

from pathlib import Path
from typing import Any

from .base_agent import BaseAgent
from .herramientas_externas import correr, modulo_disponible, python_de
from .scope import archivos_py


class TestingAgent(BaseAgent):
    name = "Testing Agent"

    def review(
        self,
        project: str,
    ) -> dict[str, Any]:
        project_path = Path(project)

        source_files = archivos_py(project_path)

        test_files = [f for f in source_files if f.name.startswith("test_")]

        pytest_files = [f for f in source_files if "pytest" in f.name]

        unittest_files = [f for f in source_files if "unittest" in f.name]

        production = [file for file in source_files if "test" not in file.name.lower()]

        coverage = min(
            len(test_files) * 5,
            100,
        )

        # Pruebas de verdad, contadas por pytest y no por el nombre del archivo.
        recogidas = _contar_con_pytest(project_path)

        missing = max(
            0,
            len(production) - len(test_files),
        )

        return {
            "python_files": len(source_files),
            "production_files": len(production),
            "tests": len(test_files),
            "pruebas_recogidas": recogidas,
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


def _contar_con_pytest(raiz: Path) -> int | None:
    """``pytest --collect-only -q`` y la última línea: «N tests collected»."""
    if not modulo_disponible(raiz, "pytest"):
        return None

    codigo, out, _ = correr(
        [
            python_de(raiz),
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        raiz,
        120,
    )

    if codigo not in (0, 5):
        return None

    import re

    m = re.search(r"(\d+) tests? collected", out)

    return int(m.group(1)) if m else None
