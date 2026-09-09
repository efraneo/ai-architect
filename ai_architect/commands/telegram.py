"""
=========================================================
Telegram

Darle órdenes a Architect desde el celular, y aprobar desde ahí.
=========================================================

    architect telegram [repositorio] [--si]

Se queda atendiendo el bot: cada mensaje tuyo es una orden (va por ``pide``,
como si la dijeras al micrófono) y te contesta ahí. Además:

    pendientes            lo que espera tu permiso
    aprobar <id>|todo     lo aplica
    rechazar <id>         lo descarta
    sí / no               contesta al permiso que acaba de pedir

Solo atiende al chat de ``TELEGRAM_CHAT_ID``. Con la cara abierta
(``conversar``) esto ya corre por dentro si el bot está configurado: no hace
falta lanzarlo aparte.
"""

from __future__ import annotations

import threading
from typing import Any

from ai_architect.canales import telegram
from ai_architect.core import perfil


def atender(texto: str, project: str, si: bool) -> str:
    """Una línea del celular → la respuesta. Sin voz: texto y ya."""
    from ai_architect.commands import conversar, pendientes, pide

    limpio = (texto or "").strip()
    plano = limpio.lower().lstrip("/")

    if plano in ("pendientes", "pending"):
        return str(pendientes.run("listar")["explanation"])

    if plano.startswith("aprobar ") or plano.startswith("rechazar "):
        accion, _, que = plano.partition(" ")

        return str(pendientes.run(accion, que.strip())["explanation"])

    if conversar.hay_permiso_pendiente():
        decision = conversar.decidir_permiso(limpio)

        if decision:
            return str(conversar.resolver_permiso(decision)["respuesta"])

    pide.conciso(True)

    resultado = pide.run(project, frase=limpio, si=si)
    respuesta = str(resultado.get("explanation") or resultado.get("error") or "")

    permiso = conversar._anotar_permiso(resultado)

    if permiso:
        respuesta += (
            "\n\nTengo " + str(len(permiso)) + " cambio(s) esperando tu permiso:\n- "
        )
        respuesta += "\n- ".join(permiso) + "\n\nResponde «sí» o «no»."

    return respuesta


def run(
    project: str = ".", si: bool = False, parar: threading.Event | None = None
) -> dict[str, Any]:
    if not telegram.configurado():
        return {
            "success": False,
            "executed": False,
            "command": "telegram",
            "error": "falta TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en ~/.ai_architect/.env",
            "explanation": "El bot de Telegram no está configurado. Mira «architect canales».",
        }

    print(
        f"{perfil.encabezar()} Atiendo el celular. "
        f"Órdenes que tocan archivos: {'autorizadas' if si else 'NO autorizadas'}. Ctrl+C para terminar.",
        flush=True,
    )

    telegram.enviar("Architect en línea. Dime qué hago.")

    try:
        atendidos = telegram.escuchar(lambda t: atender(t, project, si), parar)

    except KeyboardInterrupt:
        atendidos = 0
        print(f"\n{perfil.despedir()}")

    return {
        "success": True,
        "executed": True,
        "command": "telegram",
        "attended": atendidos,
    }


def en_segundo_plano(project: str, si: bool) -> threading.Event | None:
    """Para `conversar`: el celular atiende mientras la cara está abierta."""
    if not telegram.configurado():
        return None

    parar = threading.Event()

    threading.Thread(
        target=telegram.escuchar,
        args=(lambda t: atender(t, project, si), parar),
        daemon=True,
        name="architect-telegram",
    ).start()

    return parar
