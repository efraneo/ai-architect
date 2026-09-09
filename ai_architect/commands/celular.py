"""
=========================================================
Celular

Mandar el teléfono desde el PC: llamar, colgar, bloquear, poner música…
=========================================================

    architect celular --frase "bloquea el celular"
    architect celular --frase "pon Tití me preguntó"
    architect celular --frase "llama a Juan"
    architect celular                       qué órdenes entiende

Va por el bot de Telegram a una automatización del teléfono (docs/CELULAR.md).
Por voz, estas mismas frases salen al instante; llamar pide un «sí».
"""

from __future__ import annotations

from typing import Any

from ai_architect.canales import celular


def run(frase: str = "") -> dict[str, Any]:
    texto = (frase or "").strip()

    if not texto:
        cuerpo = "\n".join(f"{a}: {d}" for a, d in celular.ACCIONES.items())

        return {
            "success": True,
            "executed": False,
            "command": "celular",
            "instant": True,
            "actions": dict(celular.ACCIONES),
            "contacts": len(celular.contactos()),
            "explanation": f"Entiendo {len(celular.ACCIONES)} órdenes para el celular; ver docs/CELULAR.md.",
            "panel": {"tipo": "texto", "titulo": "Celular", "cuerpo": cuerpo},
        }

    entendido = celular.entender(texto)

    if entendido is None:
        return {
            "success": False,
            "executed": False,
            "command": "celular",
            "error": "no entendí qué hacer con el celular",
            "explanation": "No entendí qué hacer con el celular. Prueba «bloquea el celular» o «pon música de X».",
        }

    accion, argumento = entendido

    if accion == "desbloquear":
        return {
            "success": False,
            "executed": False,
            "command": "celular",
            "error": "desbloquear no lo permite el teléfono",
            "explanation": "Desbloquear no lo permite el teléfono: solo con tu cara, huella o clave.",
        }

    salida = celular.ordenar(accion, argumento)

    return {
        "success": bool(salida.get("ok")),
        "executed": bool(salida.get("ok")),
        "command": "celular",
        "instant": True,
        "result": salida,
        "explanation": (
            f"Mandado al celular: {salida['texto']}"
            if salida.get("ok")
            else f"No pude: {salida.get('error')}"
        ),
        **({} if salida.get("ok") else {"error": str(salida.get("error"))}),
    }
