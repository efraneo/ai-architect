"""
=========================================================
Reparar

Las averías del propio Architect, y el «adelante» que las arregla.
=========================================================

    architect reparar                     las averías apuntadas y su estado
    architect reparar --frase adelante    la palabra maestra: repara (o reconstruye) ahora

Nunca se repara solo: sin «adelante» no toca su código. Ver ``autoreparacion``.
"""

from __future__ import annotations

import time
from typing import Any

from ai_architect import autoreparacion


def run(frase: str = "") -> dict[str, Any]:
    texto = (frase or "").strip()

    if texto and autoreparacion.es_palabra_maestra(texto):
        dicho = autoreparacion.adelante(
            avisar=lambda t: print(f"\n{t}", flush=True), en_hilo=False
        )

        return {
            "success": True,
            "executed": True,
            "command": "reparar",
            "explanation": dicho
            + (
                "\n\n" + autoreparacion.ultimo_informe()
                if autoreparacion.ultimo_informe()
                else ""
            ),
        }

    lista = autoreparacion.averias()
    filas = [
        f"{a['id']} · {time.strftime('%d/%m %H:%M', time.localtime(a['cuando']))} · "
        f"{a['comando']} · {a['estado']} · {a['error'][:80]}"
        for a in lista[-10:]
    ]
    pendiente = autoreparacion.pendiente()
    dicho = (
        f"Tengo {len(lista)} avería(s) apuntada(s); "
        + (
            f"la última ({pendiente['comando']}) espera tu «adelante»."
            if pendiente
            else "ninguna pendiente."
        )
        if lista
        else "No tengo averías apuntadas."
    )

    return {
        "success": True,
        "executed": False,
        "command": "reparar",
        "instant": True,
        "failures": lista[-10:],
        "explanation": dicho,
        "panel": {
            "tipo": "texto",
            "titulo": "Averías",
            "cuerpo": "\n".join(filas) or dicho,
        },
    }
