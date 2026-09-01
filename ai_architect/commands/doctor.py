"""
=========================================================
Doctor Command

Lo primero que conviene ejecutar.
=========================================================

Antes esto devolvía ``"status": "healthy"`` **fijo**, junto a la versión de
Python y la plataforma. Respondía que todo iba bien sin una sola clave de
proveedor configurada y sin git instalado. Un chequeo que no puede dar mal
no sirve para diagnosticar nada.

Ahora pregunta de verdad, y sigue sin costar nada: ninguna comprobación
llama a un proveedor ni sale a la red.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from typing import Any

from ai_architect.core.health import Health

TIEMPO_LIMITE = 10


def run() -> dict[str, Any]:
    salud = Health()

    _proveedores(salud)
    _agentes(salud)
    _git(salud)

    informe = salud.report()

    return {
        "success": True,
        "python": sys.version,
        "platform": platform.platform(),
        "healthy": informe["healthy"],
        "status": "healthy" if informe["healthy"] else "degraded",
        "components": informe["components"],
    }


def _proveedores(salud: Health) -> None:
    """El proveedor por defecto: ¿tiene clave?

    ``ProviderManager.health()`` ya respondía ``not_configured``; nadie
    miraba esa respuesta.
    """
    try:
        from ai_architect.providers.provider_manager import ProviderManager

        salud.register(ProviderManager(), name="provider")

    except Exception as e:  # noqa: BLE001 - el diagnóstico no puede reventar
        salud.check("provider", False, str(e))


def _agentes(salud: Health) -> None:
    """¿Se pueden construir los agentes?

    Doce de ellos no se podían instanciar y nadie se enteró, porque nadie los
    construía. Esto lo habría dicho.
    """
    try:
        from ai_architect.agents.agent_manager import AgentManager

        salud.register(AgentManager(), name="agents")

    except Exception as e:  # noqa: BLE001
        salud.check("agents", False, str(e))


def _git(salud: Health) -> None:
    """¿Está git instalado? Sin él no hay commits, ni ramas, ni parches."""
    if not shutil.which("git"):
        salud.check("git", False, "git no está en el PATH")
        return

    try:
        resultado = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=TIEMPO_LIMITE,
        )

    except (OSError, subprocess.SubprocessError) as e:
        salud.check("git", False, str(e))
        return

    salud.check(
        "git",
        resultado.returncode == 0,
        resultado.stdout.strip(),
    )
