"""
=========================================================
Avatar

La cara que responde.
=========================================================

Un rostro de puntos, en el navegador. No hay servidor ni dependencias: es
un HTML que se abre con ``file://`` y se dibuja solo con canvas.

**Cómo se sincroniza la boca.** El navegador no puede reproducir el audio
él mismo —las políticas de autoarranque lo bloquean sin un clic previo, y
pedir un clic cada vez rompe el flujo—. Así que el sonido lo pone Python y
la cara solo anima: se le pasa por la URL cuántos milisegundos va a durar,
y ese número no es una estimación, sale de la cabecera del WAV.

Queda un desfase, y conviene decirlo: entre que se lanza el navegador y
pinta el primer fotograma pasa un rato que nadie puede medir de antemano.
Por eso se espera ``ESPERA_NAVEGADOR`` antes de reproducir. Con la pestaña
ya abierta el desfase es inapreciable; la primera vez, arrancando Chrome
en frío, puede irse medio segundo.
"""

from __future__ import annotations

import time
import webbrowser
from pathlib import Path
from typing import Any

from ai_architect.core import perfil
from ai_architect.voz import hablar as motor_de_voz

ROSTRO = Path(__file__).resolve().parent.parent / "avatar" / "rostro.html"

# Lo que se le da al navegador para arrancar y pintar antes de que suene.
ESPERA_NAVEGADOR = 1.4

# Con la pestaña ya abierta no hace falta esperar casi nada.
ESPERA_PESTANA = 0.35

# Se recuerda si ya se abrió en esta sesión para no esperar de más.
_abierto = False


def run(
    decir: str = "",
    abrir: bool = True,
    esperar: float | None = None,
) -> dict[str, Any]:
    """Muestra la cara. Con ``decir``, además habla y mueve la boca."""
    global _abierto

    if not ROSTRO.is_file():
        return {
            "success": False,
            "error": f"no encuentro el rostro en {ROSTRO}",
        }

    preparado = motor_de_voz.preparar(decir) if decir.strip() else None

    milisegundos = int((preparado or {}).get("segundos", 0) * 1000)

    url = ROSTRO.as_uri()

    if milisegundos:
        url += f"?ms={milisegundos}"

    if abrir:
        pausa = ESPERA_PESTANA if _abierto else ESPERA_NAVEGADOR

        webbrowser.open(url)

        _abierto = True

        if preparado:
            time.sleep(esperar if esperar is not None else pausa)

    hablado = motor_de_voz.emitir(preparado) if preparado else False

    return {
        "success": True,
        "url": url,
        "spoke": hablado,
        "engine": (preparado or {}).get("motor", ""),
        "seconds": round((preparado or {}).get("segundos", 0.0), 2),
        "explanation": _explicar(decir, preparado, hablado),
    }


def _explicar(
    decir: str,
    preparado: dict[str, Any] | None,
    hablado: bool,
) -> str:
    """Qué se le dice al usuario en la terminal mientras mira la cara."""
    partes = [f"{perfil.encabezar()} Abrí el rostro en el navegador."]

    if not decir.strip():
        partes.append("Pulsa espacio para que mueva la boca.")

    elif hablado:
        segundos = (preparado or {}).get("segundos", 0.0)

        partes.append(f'Dije "{decir.strip()}" en {segundos:.1f} s.')

    else:
        motivo = (preparado or {}).get("motivo") or "no hay ninguna voz disponible"

        partes.append(f"La cara está, pero no pude hablar: {motivo}.")

    return " ".join(partes)
