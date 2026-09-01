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

from typing import Any

# Lo que se exige de la respuesta. Va al final a propósito: es lo último que
# lee el modelo antes de contestar.
SALIDA = (
    "Generate ONLY a unified diff patch.",
    "Do not explain.",
    "Do not include markdown.",
    "Do not wrap the patch in code fences.",
    "Return valid unified diff format.",
)


def construir(
    analysis: Any,
    plan: Any,
    instruction: str,
    file: str | None = None,
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
