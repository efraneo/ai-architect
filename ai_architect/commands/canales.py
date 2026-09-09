"""
=========================================================
Canales

Por dónde te habla Architect además del micrófono, y cómo conectarlos.
=========================================================

    architect canales                      qué hay configurado y qué falta
    architect canales --probar telegram    manda un mensaje de prueba
    architect canales --probar correo      (a tu propio buzón)
    architect telegram                     atiende órdenes desde el celular

Las claves van en ``~/.ai_architect/.env``. Nunca en el repositorio.
"""

from __future__ import annotations

from typing import Any

from ai_architect import canales


def run(probar: str = "") -> dict[str, Any]:
    estado = canales.estado()

    if probar:
        return _probar(probar.strip().lower())

    lineas = []

    for canal, datos in estado.items():
        if datos["configurado"]:
            lineas.append(f"✓ {canal}: listo")
        else:
            lineas.append(
                f"· {canal}: falta {', '.join(datos['falta'])} — {datos['como']}"
            )

    listos = [c for c, d in estado.items() if d["configurado"]]
    dicho = (
        f"Canales listos: {', '.join(listos)}."
        if listos
        else "No hay ningún canal configurado. Pon las claves en ~/.ai_architect/.env."
    )

    return {
        "success": True,
        "executed": False,
        "command": "canales",
        "instant": True,
        "channels": estado,
        "explanation": dicho,
        "panel": {"tipo": "texto", "titulo": "Canales", "cuerpo": "\n".join(lineas)},
    }


def _probar(canal: str) -> dict[str, Any]:
    if canal == "telegram":
        from ai_architect.canales import telegram

        salida = telegram.enviar(
            "Architect: prueba de canal. Si lees esto, el celular está conectado."
        )
        ok = bool(salida.get("ok"))
        detalle = "" if ok else str(salida.get("description", ""))

    elif canal == "correo":
        from ai_architect.canales import correo

        salida = correo.enviar(
            canales.valor("CORREO_USUARIO"),
            "Architect: prueba de canal",
            "Si lees esto, el correo está conectado.",
        )
        ok = bool(salida.get("ok"))
        detalle = "" if ok else str(salida.get("error", ""))

    elif canal == "whatsapp":
        return {
            "success": False,
            "executed": False,
            "command": "canales",
            "error": 'WhatsApp se prueba enviando a un número: architect hacer "mándale un WhatsApp a 57300… diciendo hola" --si',
            "explanation": "WhatsApp se prueba con una orden a un número concreto.",
        }

    else:
        return {
            "success": False,
            "executed": False,
            "command": "canales",
            "error": f"no conozco el canal {canal!r} (telegram, correo, whatsapp)",
            "explanation": f"No conozco el canal {canal}.",
        }

    return {
        "success": ok,
        "executed": ok,
        "command": "canales",
        "instant": True,
        "explanation": f"Prueba de {canal}: {'enviada' if ok else 'falló: ' + detalle}.",
        **({} if ok else {"error": detalle}),
    }
