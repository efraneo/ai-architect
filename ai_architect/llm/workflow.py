"""
=========================================================
LLM Workflow

Coordinates the complete AI editing workflow.
=========================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .smart_editor import SmartEditor


class LLMWorkflow:
    """
    Orquesta el flujo completo del LLM.

    Esta clase mantiene al LLMEngine desacoplado del
    SmartEditor para que en el futuro puedan existir
    distintos workflows (review, refactor, migrate, etc.).
    """

    def __init__(
        self,
        repository: str | Path,
        env_file: str,
    ) -> None:

        self.repository = Path(repository).resolve()

        self.editor = SmartEditor(
            repository=str(self.repository),
            env_file=env_file,
        )

    def execute(
        self,
        file: str,
        task: str,
    ) -> dict[str, Any]:
        """
        Ejecuta una mejora completa sobre un archivo.
        """

        return self.editor.improve(
            file=file,
            instruction=task,
        )

    def review(
        self,
        file: str,
    ) -> dict[str, Any]:
        """
        Punto de extensión para futuras revisiones
        sin modificar código.
        """

        return {
            "success": False,
            "message": "Review workflow not implemented yet.",
            "file": file,
        }

    def refactor(
        self,
        file: str,
        objective: str,
    ) -> dict[str, Any]:
        """
        Punto de extensión para futuras refactorizaciones.
        """

        return self.execute(
            file=file,
            task=objective,
        )
