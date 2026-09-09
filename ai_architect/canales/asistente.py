"""Configurar un canal hablando: Architect pide lo que le falta, lo guarda en su
``.env`` y termina la conexión él solo.

Para Telegram, lo único que no puede sacar solo es el token que da @BotFather:
lo pide («pégalo aquí»), y el ``chat_id`` lo descubre él en cuanto le escribes
algo al bot desde el celular. Para el correo pide servidor, usuario y clave.

Los datos van a ``~/.ai_architect/.env`` (nunca al repositorio) y entran en el
entorno al momento. Lo secreto se pide en un campo que no lo muestra.
"""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ai_architect.core.env_file import CARPETA_USUARIO

# Qué pide cada canal, en orden: (clave, cómo se pide, es secreto)
PASOS: dict[str, list[tuple[str, str, bool]]] = {
    "telegram": [
        (
            "TELEGRAM_BOT_TOKEN",
            "Necesito un bot de Telegram. Abre @BotFather, escribe /newbot, dale un "
            "nombre y pega aquí el token que te da.",
            True,
        ),
    ],
    "correo": [
        (
            "CORREO_SMTP_HOST",
            "¿Cuál es el servidor SMTP? (p. ej. smtp.hostinger.com)",
            False,
        ),
        ("CORREO_SMTP_PUERTO", "¿Puerto? (465 o 587)", False),
        ("CORREO_USUARIO", "¿Tu dirección de correo?", False),
        (
            "CORREO_CLAVE",
            "La clave de ese buzón (no se muestra ni se guarda en el repositorio).",
            True,
        ),
        (
            "CORREO_IMAP_HOST",
            "Servidor IMAP para leer, si lo quieres (p. ej. imap.hostinger.com; vacío si no).",
            False,
        ),
    ],
    "whatsapp": [
        (
            "WHATSAPP_TOKEN",
            "El token permanente de tu app de WhatsApp Cloud API (Meta).",
            True,
        ),
        (
            "WHATSAPP_PHONE_ID",
            "El Phone Number ID de esa app (no es el número).",
            False,
        ),
    ],
}

ESPERA_CHAT = 120

# La configuración en curso: canal, pasos que faltan y la orden que la disparó.
_en_curso: dict[str, Any] = {}


def ruta_env() -> Path:
    return CARPETA_USUARIO / ".env"


def guardar_en_env(clave: str, valor: str) -> bool:
    """Escribe (o reemplaza) la variable en ``~/.ai_architect/.env`` y en el entorno."""
    if not clave or not valor:
        return False

    ruta = ruta_env()
    ruta.parent.mkdir(parents=True, exist_ok=True)

    try:
        lineas = ruta.read_text(encoding="utf-8").splitlines() if ruta.is_file() else []

    except OSError:
        lineas = []

    lineas = [ln for ln in lineas if ln.split("=", 1)[0].strip() != clave]
    lineas.append(f"{clave}={valor}")

    try:
        ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    except OSError:
        return False

    os.environ[clave] = valor

    return True


def hay_configuracion_en_curso() -> bool:
    return bool(_en_curso)


def cancelar() -> None:
    _en_curso.clear()


def empezar(canal: str, orden: str = "") -> dict[str, Any]:
    """Arranca la configuración guiada y devuelve la primera pregunta."""
    if canal not in PASOS:
        return {"respuesta": f"No sé configurar «{canal}»."}

    from ai_architect import canales

    faltan = [(k, p, s) for k, p, s in PASOS[canal] if not canales.valor(k)]

    if canal == "telegram" and not faltan and not canales.valor("TELEGRAM_CHAT_ID"):
        _en_curso.update({"canal": canal, "pasos": [], "orden": orden})

        return _terminar_telegram()

    if not faltan:
        cancelar()

        return {"respuesta": f"El canal {canal} ya está configurado."}

    _en_curso.clear()
    _en_curso.update({"canal": canal, "pasos": faltan, "orden": orden})

    return _pedir_siguiente()


def _pedir_siguiente() -> dict[str, Any]:
    clave, pregunta, secreto = _en_curso["pasos"][0]

    return {
        "respuesta": pregunta,
        "pedir": {"clave": clave, "etiqueta": pregunta, "secreto": secreto},
    }


def recibir(clave: str, valor: str) -> dict[str, Any]:
    """Un dato que el usuario acaba de dar. Guarda, y pide el siguiente o termina."""
    if not _en_curso:
        return {"respuesta": "No te había pedido nada."}

    esperado = _en_curso["pasos"][0][0] if _en_curso["pasos"] else ""

    if esperado and clave != esperado:
        return _pedir_siguiente()

    valor = (valor or "").strip()

    if valor:
        guardar_en_env(clave, valor)

    elif esperado and _en_curso["pasos"][0][2]:
        return {
            **_pedir_siguiente(),
            "respuesta": "Eso no puede ir vacío. " + _pedir_siguiente()["respuesta"],
        }

    if _en_curso["pasos"]:
        _en_curso["pasos"].pop(0)

    if _en_curso["pasos"]:
        return _pedir_siguiente()

    canal = _en_curso["canal"]

    if canal == "telegram":
        return _terminar_telegram()

    orden = _en_curso.get("orden", "")
    cancelar()

    return {"respuesta": f"Listo, {canal} configurado.", "orden_pendiente": orden}


def _terminar_telegram() -> dict[str, Any]:
    """Con el token guardado, el chat_id lo descubre él: pide que le escriban al bot."""
    return {
        "respuesta": (
            "Token guardado. Ahora escríbele cualquier cosa al bot desde tu celular; "
            "en cuanto lo vea, quedo conectado y sigo con lo que me pediste."
        ),
        "descubrir": "telegram",
    }


def descubrir_chat_id(
    avisar: Callable[[str], None] | None = None,
    espera: float = ESPERA_CHAT,
    en_hilo: bool = True,
) -> threading.Thread | dict[str, Any]:
    """Espera a que llegue un mensaje al bot y se queda con ese chat como el tuyo."""

    def _buscar() -> dict[str, Any]:
        from ai_architect.canales import telegram

        limite = time.monotonic() + espera
        desde = 0

        while time.monotonic() < limite:
            salida = telegram._llamar("getUpdates", offset=desde, timeout=10)

            for actualizacion in salida.get("result", []) if salida.get("ok") else []:
                desde = int(actualizacion.get("update_id", 0)) + 1
                mensaje = actualizacion.get("message") or {}
                chat = str((mensaje.get("chat") or {}).get("id", ""))

                if chat:
                    guardar_en_env("TELEGRAM_CHAT_ID", chat)
                    orden = _en_curso.get("orden", "")
                    cancelar()
                    telegram.enviar("Architect conectado a este celular.")

                    return {"ok": True, "chat_id": chat, "orden_pendiente": orden}

            time.sleep(1)

        cancelar()

        return {"ok": False, "error": "no llegó ningún mensaje al bot"}

    if not en_hilo:
        return _buscar()

    def _y_avisar() -> None:
        salida = _buscar()

        if avisar is None:
            return

        try:
            if salida.get("ok"):
                avisar(
                    "Celular conectado."
                    + (" Sigo con tu orden." if salida.get("orden_pendiente") else "")
                )

                if salida.get("orden_pendiente"):
                    from ai_architect.commands import respuestas

                    hecho = respuestas.responder(str(salida["orden_pendiente"]))

                    if hecho:
                        avisar(str(hecho.get("respuesta", "")))

            else:
                avisar(
                    "No vi ningún mensaje en el bot. Cuando quieras, escríbele y dime «conéctate al celular»."
                )

        except Exception:  # noqa: BLE001 - el aviso es un extra
            return

    hilo = threading.Thread(
        target=_y_avisar, daemon=True, name="architect-telegram-chat"
    )
    hilo.start()

    return hilo
