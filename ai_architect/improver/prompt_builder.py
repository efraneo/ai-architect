"""
=========================================================
Prompt Builder

Lo que se le pide al proveedor.
=========================================================

Setenta líneas de armar texto vivían dentro de ``ImprovementEngine``. Es el
contenido que más se toca cuando se afina el comportamiento del modelo, y
tenerlo en medio del orquestador obligaba a abrir el módulo central para
cambiar una frase.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Lo que se exige de la respuesta. Va al final a propósito: es lo último que
# lee el modelo antes de contestar.
#
# Probado contra gpt-5.5 con la versión anterior —"Return valid unified diff
# format"— y devolvió su propio formato:
#
#     *** Begin Patch
#     *** Update File: ai_architect/core/env_file.py
#     @@
#      contexto
#     +añadido
#
# Es el formato `apply_patch` que los modelos nuevos emiten por defecto para
# editar ficheros. Correcto en intención, ilegible para `git apply`. Por eso
# ahora se muestra el formato exacto y se nombra el que NO se quiere: decir
# "unified diff" no basta cuando el modelo tiene otro por defecto.
SALIDA = (
    "Return ONLY a unified diff, in the exact format `git apply` accepts.",
    "",
    "Each file MUST start with these two lines:",
    "",
    "    --- a/path/to/file.py",
    "    +++ b/path/to/file.py",
    "",
    "followed by @@ hunks with line numbers, like this:",
    "",
    "    @@ -10,3 +10,4 @@",
    "     unchanged line",
    "    -removed line",
    "    +added line",
    "",
    "DO NOT use the *** Begin Patch / *** Update File format.",
    "DO NOT use @@ without line numbers.",
    "Do not explain. Do not use markdown or code fences.",
)


def construir(
    analysis: Any,
    plan: Any,
    instruction: str,
    file: str | None = None,
    repository: str | Path | None = None,
) -> str:
    """El prompt de una mejora: qué se pide, sobre qué, y qué se espera."""
    summary = analysis.summary

    lineas: list[str] = [
        "You are QUANT AI Architect.",
        "",
        "Improvement Instruction",
        "=======================",
        instruction,
        "",
    ]

    if file is not None:
        lineas.extend(
            [
                "Target File",
                "===========",
                file,
                "",
            ]
        )

        # **Con su contenido y sus números de línea.** Sin esto se le pedía
        # al modelo que parcheara un archivo que no había visto, y por eso
        # devolvía cabeceras imposibles como `@@ -0,0 +1,26 @@` sobre un
        # archivo de 105 líneas: `git apply` las rechaza siempre. El código
        # que escribía era correcto; los números no podían serlo.
        contenido = _leer_archivo(repository, file)

        if contenido:
            lineas.extend(
                [
                    "Current content (with line numbers, for the @@ headers)",
                    "======================================================",
                    contenido,
                    "",
                ]
            )

    lineas.extend(
        [
            "Project Summary",
            "===============",
            f"Files: {summary.total_files}",
            f"Python Files: {summary.python_files}",
            f"Classes: {summary.total_classes}",
            f"Functions: {summary.total_functions}",
            f"Dependencies: {summary.dependency_modules}",
            f"Duplicates: {summary.duplicate_groups}",
            f"Complexity: {summary.average_complexity}",
            "",
            "Recommendations",
            "===============",
        ]
    )

    lineas.extend(f"- {recomendacion}" for recomendacion in analysis.recommendations)

    lineas.extend(
        [
            "",
            "Execution Plan",
            "==============",
        ]
    )

    lineas.extend(f"- {tarea.title}" for tarea in plan.tasks)

    lineas.extend(["", "Output Requirements", "===================="])

    lineas.extend(SALIDA)

    return "\n".join(lineas)


# Un archivo enorme se lleva el presupuesto de contexto entero y no deja
# sitio para la respuesta. Se manda el principio, que es donde están los
# imports y las definiciones, y se avisa de lo que falta.
MAX_LINEAS = 400


def _leer_archivo(repository: str | Path | None, file: str) -> str:
    """El contenido del archivo objetivo, numerado.

    Numerado a propósito: es lo que permite al modelo escribir cabeceras
    ``@@ -10,3 +10,4 @@`` que `git apply` acepte.
    """
    if repository is None:
        return ""

    ruta = Path(repository) / file

    try:
        lineas = ruta.read_text(encoding="utf-8", errors="replace").splitlines()

    except OSError:
        return ""

    recortado = lineas[:MAX_LINEAS]

    numeradas = [f"{numero:>5}| {texto}" for numero, texto in enumerate(recortado, 1)]

    if len(lineas) > MAX_LINEAS:
        numeradas.append(f"... ({len(lineas) - MAX_LINEAS} líneas más, no mostradas)")

    return chr(10).join(numeradas)
