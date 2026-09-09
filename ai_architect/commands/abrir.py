"""
=========================================================
Abrir

«Abre Word», «abre Chrome», «abre la carpeta del proyecto»: programas del PC.
=========================================================

Sin modelo: un nombre conocido se traduce a su ejecutable (Windows resuelve
«winword», «excel», «chrome»… por sus *App Paths*), una dirección web se abre
en el navegador, y una ruta que exista se abre con lo que Windows tenga
asociado. Lo que no se reconoce se intenta igual con ``os.startfile`` y, si
falla, se dice.

    architect abrir --frase "Word"
"""

from __future__ import annotations

import os
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any

from ai_architect.core.texto import sin_adornos

# Cómo los llama la gente → cómo se lanzan.
PROGRAMAS = {
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "power point": "powerpnt",
    "outlook": "outlook",
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "navegador": "msedge",
    "bloc de notas": "notepad",
    "notepad": "notepad",
    "calculadora": "calc",
    "explorador": "explorer",
    "explorador de archivos": "explorer",
    "terminal": "wt",
    "consola": "cmd",
    "powershell": "powershell",
    "visual studio code": "code",
    "vs code": "code",
    "vscode": "code",
    "code": "code",
    "teams": "ms-teams:",
    "spotify": "spotify:",
    "whatsapp": "whatsapp:",
    "telegram": "tg:",
    "calendario": "outlookcal:",
    "correo": "outlook",
    "paint": "mspaint",
    "configuracion": "ms-settings:",
    "ajustes": "ms-settings:",
    "escritorio": "__escritorio__",
    "documentos": "__documentos__",
    "descargas": "__descargas__",
}


def _carpeta_especial(clave: str) -> Path | None:
    from ai_architect.commands.crear_carpetas import documentos, escritorio

    if clave == "__escritorio__":
        return escritorio()

    if clave == "__documentos__":
        return documentos()

    if clave == "__descargas__":
        return Path.home() / "Downloads"

    return None


def _lanzar(objetivo: str) -> None:
    """Abre lo que sea con lo que el sistema tenga asociado. Lanza si no puede."""
    if sys.platform == "win32":
        os.startfile(objetivo)  # noqa: S606 - es exactamente lo que se pide

        return

    abridor = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen(
        [abridor, objetivo], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def abrir(que: str) -> dict[str, Any]:
    """Abre un programa, una web o una ruta. Devuelve ``{"ok", "que", "explicacion"}``."""
    pedido = (que or "").strip().strip(".")
    plano = sin_adornos(pedido)

    if not plano:
        return {"ok": False, "que": "", "explicacion": "¿Qué abro?"}

    # Una web.
    if pedido.startswith(("http://", "https://")) or (
        "." in pedido and " " not in pedido and not Path(pedido).exists()
    ):
        url = pedido if pedido.startswith("http") else "https://" + pedido

        try:
            webbrowser.open(url)

        except Exception as e:  # noqa: BLE001 - se dice, no se esconde
            return {"ok": False, "que": url, "explicacion": f"No pude abrir {url}: {e}"}

        return {"ok": True, "que": url, "explicacion": f"Abierto: {url}."}

    # Un programa conocido (la clave más larga primero: «google chrome» antes que «chrome»).
    for nombre in sorted(PROGRAMAS, key=len, reverse=True):
        if (
            plano == nombre
            or plano.startswith(nombre + " ")
            or plano.endswith(" " + nombre)
        ):
            objetivo = PROGRAMAS[nombre]
            carpeta = _carpeta_especial(objetivo)

            try:
                _lanzar(str(carpeta) if carpeta else objetivo)

            except OSError as e:
                return {
                    "ok": False,
                    "que": nombre,
                    "explicacion": f"No encontré {nombre} en este equipo ({e}).",
                }

            return {"ok": True, "que": nombre, "explicacion": f"Abriendo {nombre}."}

    # Una ruta que exista.
    ruta = Path(pedido).expanduser()

    if ruta.exists():
        try:
            _lanzar(str(ruta))

        except OSError as e:
            return {
                "ok": False,
                "que": str(ruta),
                "explicacion": f"No pude abrir {ruta}: {e}",
            }

        return {"ok": True, "que": str(ruta), "explicacion": f"Abierto: {ruta.name}."}

    # Lo que sea: Windows conoce más programas que esta lista.
    try:
        _lanzar(pedido)

    except OSError:
        return {
            "ok": False,
            "que": pedido,
            "explicacion": f"No encontré cómo abrir «{pedido}». Dime el programa o la ruta.",
        }

    return {"ok": True, "que": pedido, "explicacion": f"Abriendo {pedido}."}


def run(frase: str = "") -> dict[str, Any]:
    salida = abrir(frase)

    return {
        "success": salida["ok"],
        "executed": salida["ok"],
        "command": "abrir",
        "instant": True,
        "opened": salida["que"],
        "explanation": salida["explicacion"],
        **({} if salida["ok"] else {"error": salida["explicacion"]}),
    }
