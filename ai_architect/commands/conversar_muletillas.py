"""Las muletillas de la conversación: lo que dice mientras trabaja.

Separado de ``conversar`` para que el flujo se lea de una vez; ``conversar``
reexporta estos nombres y las pruebas siguen usándolos desde allí.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from ai_architect.voz import hablar as motor_de_voz

# Lo que dice mientras trabaja. Una cara callada durante tres segundos
# parece colgada; con esto se sabe que te oyó y está en ello.
#
# Varias y al azar para que no suene a grabación. Se sintetizan una sola vez
# al arrancar —con Piper son milisegundos— porque generarlas en el momento
# añadiría justo la espera que vienen a tapar.
RELLENOS = (
    "Dame un segundo.",
    "Voy con eso.",
    "Un momento, lo miro.",
    "Enseguida te digo.",
    "Déjame ver.",
)

# Por debajo de esto no da tiempo ni a abrir la boca: decir "dame un
# segundo" y contestar en el mismo aliento queda peor que no decir nada.
#
# Sube de 0,9 a 1,8 por algo que se vio en uso: "cierra la ventana" se
# resuelve al instante, pero **sintetizar la respuesta también cuenta**, y
# Piper tarda casi un segundo. Con el listón en 0,9 saltaba la muletilla
# para contestar "Cerrada" — un "enseguida te digo" delante de una palabra.
# Lo que de verdad tarda —los agentes, una revisión— se pasa de 1,8 de
# sobra, así que no se pierde nada.
MERECE_RELLENO = 1.8

_rellenos_listos: list[dict[str, Any]] = []


def preparar_rellenos() -> int:
    """Deja las muletillas sintetizadas antes de que hagan falta."""
    _rellenos_listos.clear()

    for frase in RELLENOS:
        listo = motor_de_voz.preparar(frase)

        if listo.get("archivo") or listo.get("motor") == "windows":
            # Cada una en su archivo: comparten el temporal de `hablar` y
            # la última pisaría a todas las anteriores.
            copia = _apartar(listo, len(_rellenos_listos))

            if copia:
                _rellenos_listos.append(copia)

    return len(_rellenos_listos)


def _apartar(listo: dict[str, Any], indice: int) -> dict[str, Any] | None:
    origen = listo.get("archivo")

    if origen is None:
        return dict(listo)

    destino = Path(origen).with_name(f"arquitecto-relleno-{indice}.wav")

    try:
        destino.write_bytes(Path(origen).read_bytes())

    except OSError:
        return None

    return {**listo, "archivo": destino}


def soltar_relleno() -> dict[str, Any] | None:
    """Dice una muletilla ya preparada. Devuelve cuál dijo."""
    if not _rellenos_listos:
        return None

    elegido = random.choice(_rellenos_listos)

    motor_de_voz.emitir(elegido)

    return elegido
