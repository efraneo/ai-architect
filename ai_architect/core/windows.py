"""
=========================================================
Windows

Que las tareas corran con el programa cerrado.
=========================================================

Las tareas programadas se ejecutan mientras la conversación está abierta,
y eso deja fuera justo el caso que se pidió: "revisa el repositorio cada
noche". A las diez de la noche el arquitecto está cerrado.

Hace falta que alguien lo despierte, y en Windows eso ya existe y se llama
Programador de tareas. Esto lo registra por él, con ``schtasks``, que viene
en el sistema y no añade dependencias.

**Lo que se registra es una sola línea**: ``architect tareas --correr``.
El Programador se encarga de la hora; el arquitecto, de qué hacer. Cada
uno lo suyo, y así lo programado se cambia hablando sin volver a tocar
Windows.

**Por qué no se registra solo.** Crear una tarea del sistema es un cambio
que sobrevive a desinstalar el programa si nadie lo limpia. Se hace cuando
se pide, se dice qué se creó y hay una orden para quitarlo.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

# Cómo se llama en el Programador de tareas. Con prefijo para que se
# reconozca de un vistazo entre las doscientas que trae Windows.
TAREA = "AI-Architect - tareas programadas"

TIEMPO_LIMITE = 30

# Cada cuánto despierta. Cinco minutos: las tareas se apuntan a una hora
# concreta y con este paso ninguna se retrasa de forma perceptible.
CADA_MINUTOS = 5


def disponible() -> bool:
    """Si esto es un Windows con ``schtasks``."""
    return sys.platform == "win32"


def ejecutable() -> str:
    """Con qué se despierta al arquitecto.

    Instalado como ``.exe`` es él mismo. Desde el código fuente hay que
    llamar al intérprete del entorno, o el Programador arrancaría el Python
    del sistema — que no tiene el paquete instalado.
    """
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'

    return f'"{sys.executable}" -m ai_architect.cli'


def registrar(project: str = ".") -> dict[str, Any]:
    """Crea la tarea en Windows. Reemplaza la anterior si la hubiera."""
    if not disponible():
        return {
            "success": False,
            "error": "esto solo funciona en Windows; en Linux o macOS sería cron",
        }

    carpeta = Path(project).resolve()

    orden = f'{ejecutable()} tareas "{carpeta}" --correr'

    hecho = _schtasks(
        [
            "/Create",
            "/TN",
            TAREA,
            "/TR",
            orden,
            "/SC",
            "MINUTE",
            "/MO",
            str(CADA_MINUTOS),
            # Sin ventana: una consola abriéndose cada cinco minutos es
            # insoportable, y es la razón por la que la gente desactiva
            # estas cosas.
            "/F",
        ]
    )

    if not hecho["success"]:
        return {
            "success": False,
            "error": (
                f"no pude registrarla: {hecho['detalle']}. "
                "Puede que haga falta abrir la terminal como administrador."
            ),
        }

    return {
        "success": True,
        "task": TAREA,
        "command": orden,
        "explanation": (
            f"Registrado en el Programador de tareas de Windows como «{TAREA}». "
            f"Cada {CADA_MINUTOS} minutos mira si toca alguna, y ejecuta las que "
            "hayas programado hablando. Funciona con el arquitecto cerrado.\n\n"
            "Para quitarlo: architect tareas --desregistrar"
        ),
    }


def quitar() -> dict[str, Any]:
    """Borra la tarea del sistema. Lo programado hablando no se toca."""
    if not disponible():
        return {"success": False, "error": "esto solo funciona en Windows"}

    hecho = _schtasks(["/Delete", "/TN", TAREA, "/F"])

    if not hecho["success"]:
        return {
            "success": False,
            "error": f"no estaba registrada, o no pude quitarla: {hecho['detalle']}",
        }

    return {
        "success": True,
        "explanation": (
            "Quitada del Programador de tareas. Lo que tengas programado "
            "sigue guardado y se ejecutará mientras la conversación esté abierta."
        ),
    }


def esta_registrada() -> bool:
    return _schtasks(["/Query", "/TN", TAREA])["success"] if disponible() else False


def _schtasks(argumentos: list[str]) -> dict[str, Any]:
    try:
        salida = subprocess.run(
            ["schtasks", *argumentos],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=TIEMPO_LIMITE,
        )

    except (OSError, subprocess.SubprocessError) as e:
        return {"success": False, "detalle": str(e)}

    return {
        "success": salida.returncode == 0,
        "detalle": (salida.stderr or salida.stdout or "").strip()[:200],
    }
