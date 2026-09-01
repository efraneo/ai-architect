"""
=========================================================
Autonomous Engine

Varias tareas, en orden, con una puerta de aprobación.
=========================================================

``ApprovalEngine`` se construía en el constructor y **no se llamaba nunca**:
el mismo patrón que ya apareció en ``improver`` con el motor de decisión.
Un motor autónomo sin puerta de aprobación no es autónomo, es automático.

Junto a él se construían un ``BranchManager``, un ``MergeManager`` y un
``RollbackManager`` que tampoco se usaban, y que llamaban a git **sin
``cwd``** -- operaban sobre el directorio del proceso, no sobre el
repositorio analizado. El ``rollback`` era un ``git reset --hard HEAD~1``
suelto. Se podaron: ``git/`` ya hace todo eso apuntando al repositorio
correcto, y las ramas se movieron a ``git/branch_manager.py``.
"""

from __future__ import annotations

from typing import Any

from .approval_engine import ApprovalEngine
from .execution_monitor import ExecutionMonitor
from .execution_worker import ExecutionWorker
from .task_queue import TaskQueue
from .task_scheduler import TaskScheduler


class AutonomousEngine:
    def __init__(
        self,
        approval: ApprovalEngine | None = None,
    ) -> None:
        self.queue = TaskQueue()
        self.scheduler = TaskScheduler()
        self.worker = ExecutionWorker()
        self.approval = approval or ApprovalEngine()
        self.monitor = ExecutionMonitor()

    def execute(
        self,
        tasks: list[dict[str, Any]],
    ) -> dict[str, object]:
        ordered = self.scheduler.schedule(tasks)

        for scheduled_task in ordered:
            self.queue.push(scheduled_task)

        results: list[dict[str, object]] = []

        while not self.queue.empty():
            queued_task = self.queue.pop()

            if queued_task is None:
                continue

            result: dict[str, object] = self.worker.execute(
                queued_task,
            )

            self._anotar_aprobacion(queued_task, result)

            self.monitor.register(result)

            results.append(result)

        monitor_report: dict[str, object] = self.monitor.report()

        return {
            "results": results,
            "approved": sum(1 for r in results if r.get("approved")),
            "monitor": monitor_report,
        }

    def _anotar_aprobacion(
        self,
        task: dict[str, Any],
        result: dict[str, object],
    ) -> None:
        """Pasa el resultado por la puerta de aprobación.

        La tarea se ejecutó igual: esto no es un permiso previo, es el
        veredicto sobre lo que salió. Quien llame decide qué hace con lo no
        aprobado -- aquí no se toca ningún repositorio.
        """
        # Sin esto, una tarea que revienta no dice cuál era: el resultado del
        # worker no lleva rastro de la tarea que lo produjo.
        if "name" in task:
            result["task"] = task["name"]

        if not result.get("success"):
            result["approved"] = False
            result["approval_reason"] = "la tarea falló"
            return

        salida = result.get("result")

        # Lo que devuelve ``improve()`` ya trae lo que hace falta; una tarea
        # que devuelve otra cosa no se puede juzgar, y lo que no se sabe no
        # se aprueba.
        if not isinstance(salida, dict):
            result["approved"] = False
            result["approval_reason"] = "la tarea no reportó nada que juzgar"
            return

        decision = salida.get("decision")
        decision = decision if isinstance(decision, dict) else {}

        pruebas = salida.get("tests")
        pruebas = pruebas if isinstance(pruebas, dict) else {}

        ejecucion = {
            "tests_ok": bool(pruebas.get("success", False)),
            "risk": task.get("risk_level", salida.get("risk", "LOW")),
            "confidence": decision.get("confidence", 0),
        }

        result["approved"] = self.approval.approve(ejecucion)
        result["approval_reason"] = self.approval.motivo(ejecucion)
