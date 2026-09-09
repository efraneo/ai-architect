"""
=========================================================
Calidad Agent

Lo que la CI comprueba, comprobado aquí: formato, lint, tipos y documentación.
=========================================================

No opina: corre ``black --check``, ``ruff check`` y ``mypy`` con el intérprete
del proyecto y cuenta. Y mira dos cosas de documentación que ningún linter
mira: módulos sin docstring y comandos del CLI que el README no menciona.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .base_agent import BaseAgent
from .herramientas_externas import correr, modulo_disponible, python_de
from .scope import archivos_py

MAXIMO_HALLAZGOS = 25
LINEAS_PARA_EXIGIR_DOCSTRING = 12


class CalidadAgent(BaseAgent):
    name = "Calidad Agent"

    def run(self, context):
        return self.review(context)

    def review(self, project: str) -> dict[str, Any]:
        raiz = Path(project)
        py = python_de(raiz)
        findings: list[dict[str, Any]] = []
        informe: dict[str, Any] = {"agent": self.name, "status": "OK"}

        paquete = _paquete_principal(raiz)
        objetivos = [paquete] if paquete else ["."]

        # --- formato ---------------------------------------------------------
        if modulo_disponible(raiz, "black"):
            codigo, out, err = correr(
                [py, "-m", "black", "--check", "-q", *objetivos], raiz
            )
            sin_formato = [
                ln.split("would reformat", 1)[1].strip()
                for ln in (out + err).splitlines()
                if "would reformat" in ln
            ]
            informe["black"] = {"ok": codigo == 0, "archivos": len(sin_formato)}

            for archivo in sin_formato[:10]:
                findings.append(
                    {
                        "type": "formato",
                        "file": archivo,
                        "issue": "sin formatear (black)",
                    }
                )

        # --- lint ------------------------------------------------------------
        if modulo_disponible(raiz, "ruff"):
            codigo, out, _ = correr(
                [py, "-m", "ruff", "check", "--output-format", "json", *objetivos], raiz
            )
            avisos = _json(out) or []
            informe["ruff"] = {"ok": codigo == 0, "avisos": len(avisos)}

            for aviso in avisos[:MAXIMO_HALLAZGOS]:
                findings.append(
                    {
                        "type": f"ruff {aviso.get('code', '')}",
                        "file": str(aviso.get("filename", "")),
                        "line": (aviso.get("location") or {}).get("row"),
                        "issue": str(aviso.get("message", ""))[:140],
                    }
                )

        # --- tipos -------------------------------------------------------------
        if paquete and modulo_disponible(raiz, "mypy"):
            codigo, out, _ = correr(
                [py, "-m", "mypy", paquete, "--no-error-summary"], raiz, 300
            )
            errores = [ln for ln in out.splitlines() if ": error:" in ln]
            informe["mypy"] = {"ok": codigo == 0, "errores": len(errores)}

            for linea in errores[:10]:
                sitio, _, mensaje = linea.partition(": error:")
                archivo, _, numero = sitio.rpartition(":")
                findings.append(
                    {
                        "type": "tipos",
                        "file": archivo,
                        "line": int(numero) if numero.isdigit() else None,
                        "issue": mensaje.strip()[:140],
                    }
                )

        # --- documentación -------------------------------------------------------
        sin_doc: list[str] = []

        for modulo in archivos_py(raiz):
            if modulo.name.startswith("test_") or modulo.name == "__init__.py":
                continue

            try:
                texto_modulo = modulo.read_text(encoding="utf-8", errors="replace")

            except OSError:
                continue

            if texto_modulo.count("\n") < LINEAS_PARA_EXIGIR_DOCSTRING:
                continue

            cabeza = texto_modulo[:400].lstrip()

            if not cabeza.startswith(('"""', "'''", "#!", "# ")):
                sin_doc.append(
                    str(modulo.relative_to(raiz))
                    if modulo.is_relative_to(raiz)
                    else str(modulo)
                )

        informe["modulos_sin_docstring"] = len(sin_doc)

        for archivo in sin_doc[:8]:
            findings.append(
                {"type": "docstring", "file": archivo, "issue": "módulo sin docstring"}
            )

        faltan_en_readme = _comandos_sin_documentar(raiz)
        informe["comandos_sin_readme"] = faltan_en_readme

        if faltan_en_readme:
            findings.append(
                {
                    "type": "readme",
                    "issue": "comandos del CLI que el README no menciona: "
                    + ", ".join(faltan_en_readme),
                }
            )

        informe["findings"] = findings

        return informe

    def capabilities(self) -> list[str]:
        return [
            "calidad",
            "formato (black)",
            "lint (ruff)",
            "tipos (mypy)",
            "modulos sin docstring",
            "comandos sin documentar en el README",
        ]


def _paquete_principal(raiz: Path) -> str:
    """La carpeta con ``__init__.py`` que da nombre al proyecto, si la hay."""
    candidatos = [
        d
        for d in raiz.iterdir()
        if d.is_dir()
        and (d / "__init__.py").is_file()
        and not d.name.startswith((".", "_"))
        and d.name not in ("tests", "test", "docs", "build", "dist", "scratchpad")
    ]

    if not candidatos:
        return ""

    candidatos.sort(key=lambda d: -len(list(d.glob("*.py"))))

    return candidatos[0].name


def _comandos_sin_documentar(raiz: Path) -> list[str]:
    cli = raiz / "ai_architect" / "cli.py"
    readme = raiz / "README.md"

    if not cli.is_file() or not readme.is_file():
        return []

    try:
        nombres = re.findall(
            r'Comando\(\s*"([a-z_]+)"', cli.read_text(encoding="utf-8")
        )
        texto = readme.read_text(encoding="utf-8")

    except OSError:
        return []

    return sorted(n for n in set(nombres) if n not in texto)


def _json(texto: str) -> Any:
    import json

    try:
        return json.loads(texto) if texto.strip() else None

    except ValueError:
        return None
