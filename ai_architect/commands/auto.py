"""
=========================================================
Auto Command

Varias mejoras en una sola pasada.
=========================================================

``autonomous/`` estaba huérfano: nueve módulos que nadie construía. Esto los
pone a trabajar -- cola, orden, ejecución, monitor y la puerta de aprobación
-- sobre lo único que sabe mejorar el proyecto: ``ImprovementEngine``.

Cada instrucción es una tarea. Se ordenan por prioridad, se ejecutan una a
una y cada resultado pasa por la aprobación. **Ninguna toca el repositorio**
salvo que ``AUTO_COMMIT`` esté encendido, que es la misma puerta que ya
protege a ``architect improve``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_architect.autonomous.autonomous_engine import AutonomousEngine
from ai_architect.improver.improvement_engine import ImprovementEngine


def run(
    project: str,
    instructions: list[str],
    engine: ImprovementEngine | None = None,
    apply: bool = False,
) -> dict:
    """Ejecuta varias instrucciones sobre el mismo repositorio.

    Parameters
    ----------
    project:
        Raíz del repositorio.
    instructions:
        Las mejoras a pedir, en orden de prioridad: la primera es la más
        prioritaria.
    engine:
        Inyectable, para no llamar a un proveedor en las pruebas.

    Returns
    -------
    dict
        Informe serializable.
    """

    repository = Path(project).resolve()

    if not repository.exists():
        return {
            "success": False,
            "repository": str(repository),
            "error": "Repository not found.",
        }

    if not instructions:
        return {
            "success": False,
            "repository": str(repository),
            "error": "No instructions given.",
        }

    mejorador = engine or ImprovementEngine()

    # La primera instrucción es la más prioritaria. El planificador ordena de
    # mayor a menor, así que la prioridad baja según la posición.
    total = len(instructions)

    tareas: list[dict[str, Any]] = [
        {
            "name": instruccion,
            "priority": total - posicion,
            "risk": 0,
            "callback": _tarea(mejorador, repository, instruccion, apply),
        }
        for posicion, instruccion in enumerate(instructions)
    ]

    informe = AutonomousEngine().execute(tareas)

    resultados = informe["results"]
    resultados = resultados if isinstance(resultados, list) else []

    return {
        "success": True,
        "repository": str(repository),
        "total_tasks": total,
        "executed": len(resultados),
        "approved": informe.get("approved", 0),
        "tasks": [_resumen(r) for r in resultados],
    }


def _tarea(
    mejorador: ImprovementEngine,
    repository: Path,
    instruccion: str,
    apply: bool = False,
):
    """Cierra sobre la instrucción: sin esto, todas las tareas correrían la
    última (el fallo clásico de capturar la variable del bucle)."""

    def ejecutar() -> dict[str, Any]:
        return mejorador.improve(
            repository,
            instruction=instruccion,
            apply=apply,
        )

    return ejecutar


def _resumen(resultado: dict[str, Any]) -> dict[str, Any]:
    """Lo justo para saber qué pasó, sin volcar el parche entero."""
    salida = resultado.get("result")
    salida = salida if isinstance(salida, dict) else {}

    decision = salida.get("decision")
    decision = decision if isinstance(decision, dict) else {}

    return {
        "instruction": salida.get("instruction") or resultado.get("task"),
        "success": resultado.get("success", False),
        "approved": resultado.get("approved", False),
        "reason": resultado.get("approval_reason", ""),
        "confidence": decision.get("confidence"),
        "patch_id": salida.get("patch_id"),
        "committed": salida.get("committed", False),
    }
