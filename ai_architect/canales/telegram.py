"""El celular: un bot de Telegram.

Dos direcciones. **Hacia ti**: avisos («tengo 2 cambios esperando tu permiso»)
y respuestas. **Desde ti**: lo que le escribas al bot llega como una orden,
igual que si se lo dijeras al micrófono, y «sí»/«no» contestan al permiso
pendiente. Solo se atiende al ``TELEGRAM_CHAT_ID`` configurado: un bot público
que obedece a cualquiera sería una puerta abierta a tu repositorio.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

import requests

from ai_architect.canales import valor

TIEMPO_LIMITE = 20

# Cuánto espera cada sondeo (long polling). Telegram cierra a los 50 s.
ESPERA_SONDEO = 25

API = "https://api.telegram.org/bot{token}/{metodo}"


def configurado() -> bool:
    return bool(valor("TELEGRAM_BOT_TOKEN") and valor("TELEGRAM_CHAT_ID"))


def _llamar(metodo: str, **datos: Any) -> dict[str, Any]:
    url = API.format(token=valor("TELEGRAM_BOT_TOKEN"), metodo=metodo)

    try:
        respuesta = requests.post(
            url, json=datos, timeout=datos.get("timeout", 0) + TIEMPO_LIMITE
        )

    except requests.RequestException as e:
        return {"ok": False, "description": str(e)}

    try:
        return dict(respuesta.json())

    except ValueError:
        return {"ok": False, "description": respuesta.text[:200]}


def enviar(texto: str, chat_id: str = "") -> dict[str, Any]:
    """Un mensaje al celular. Devuelve ``{"ok": bool, ...}``; nunca lanza."""
    if not configurado():
        return {
            "ok": False,
            "description": "falta TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID",
        }

    destino = chat_id or valor("TELEGRAM_CHAT_ID")

    # Telegram corta a 4096 caracteres: lo largo va en trozos.
    trozos = [texto[i : i + 3900] for i in range(0, max(1, len(texto)), 3900)]
    salida: dict[str, Any] = {"ok": True}

    for trozo in trozos:
        salida = _llamar("sendMessage", chat_id=destino, text=trozo or "…")

        if not salida.get("ok"):
            break

    return salida


def recibir(desde: int = 0) -> list[dict[str, Any]]:
    """Los mensajes nuevos del chat autorizado, en orden. ``desde`` es el
    último ``update_id`` visto más uno."""
    if not configurado():
        return []

    salida = _llamar("getUpdates", offset=desde, timeout=ESPERA_SONDEO)

    if not salida.get("ok"):
        return []

    mio = str(valor("TELEGRAM_CHAT_ID"))
    mensajes = []

    for actualizacion in salida.get("result", []):
        mensaje = actualizacion.get("message") or {}
        chat = str((mensaje.get("chat") or {}).get("id", ""))
        texto = str(mensaje.get("text") or "").strip()

        if chat != mio:
            # Otro chat: se marca como visto y se ignora en silencio.
            mensajes.append({"update_id": actualizacion["update_id"], "ajeno": True})

            continue

        mensajes.append(
            {"update_id": actualizacion["update_id"], "texto": texto, "chat": chat}
        )

    return mensajes


def escuchar(
    atender: Callable[[str], str],
    parar: threading.Event | None = None,
    *,
    una_vuelta: bool = False,
) -> int:
    """Atiende lo que llegue al bot hasta que ``parar`` se active.

    ``atender(texto) -> respuesta``. Devuelve cuántos mensajes atendió (útil en
    las pruebas, con ``una_vuelta``).
    """
    parar = parar or threading.Event()
    desde = 0
    atendidos = 0

    while not parar.is_set():
        for mensaje in recibir(desde):
            desde = int(mensaje["update_id"]) + 1

            if mensaje.get("ajeno") or not mensaje.get("texto"):
                continue

            try:
                respuesta = atender(mensaje["texto"])

            except Exception as e:  # noqa: BLE001 - una orden rota no tumba el canal
                respuesta = f"Se me atragantó: {e}"

            if respuesta:
                enviar(respuesta)

            atendidos += 1

        if una_vuelta:
            break

    return atendidos
