"""
=========================================================
Improvement Notice

El aviso de "mejora terminada".
=========================================================

Vive aquí y no en ``improver/`` por dos razones: dar forma a un mensaje es
trabajo del notificador, y ``improvement_engine.py`` tiene un tope de 600
líneas que el propio proyecto se comprueba en las pruebas.
"""

from __future__ import annotations

import os
from typing import Any


def notificaciones_activas() -> bool:
    """¿Avisar por Telegram al terminar?

    Apagado por defecto: un aviso es una llamada de red a un servicio
    externo, y eso no se hace sin que lo pidan.
    """
    return os.getenv("NOTIFY", "false").strip().lower() == "true"


def redactar(resultado: dict[str, Any]) -> str:
    """Lo que pasó, en tres líneas."""
    estado = "aprobado" if resultado.get("approved") else "sin aprobar"

    pruebas = resultado.get("tests")
    pruebas = pruebas if isinstance(pruebas, dict) else {}

    if not pruebas.get("executed", True):
        suite = "sin ejecutar"
    else:
        suite = "verde" if pruebas.get("success") else "rojo"

    return "\n".join(
        [
            str(resultado.get("instruction", "")),
            f"parche {resultado.get('patch_id', '')} ({estado})",
            f"archivos: {resultado.get('files', 0)} | "
            f"pruebas: {suite} | "
            f"{resultado.get('duration', 0)} s",
        ]
    )


def avisar(
    resultado: dict[str, Any],
    notificador: Any = None,
) -> None:
    """Avisa de cómo fue la mejora, si está encendido.

    Anota el desenlace en ``resultado`` y **nunca lanza**: el parche ya está
    generado y guardado en disco, así que un aviso que no sale no puede
    tumbar la mejora.
    """
    if not notificaciones_activas():
        return

    try:
        if notificador is None:
            # Se importa aquí para que el aviso, que es opcional, no arrastre
            # el cliente HTTP en cada ejecución.
            from .notifier_manager import NotifierManager

            notificador = NotifierManager(os.getenv("TELEGRAM_ENV", ".env"))

        enviado = notificador.success("Mejora terminada", redactar(resultado))

        resultado["notified"] = bool(getattr(enviado, "success", False))

    except Exception as e:  # noqa: BLE001 - avisar es secundario
        resultado["notified"] = False
        resultado["notify_error"] = str(e)
