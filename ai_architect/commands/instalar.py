"""
=========================================================
Instalar

Que Architect se procure lo que le falta.
=========================================================

    architect instalar --frase "paquete rich"
    architect instalar --frase "skill https://github.com/usuario/repo"
    architect instalar --frase "rich"                  (sin decirlo, es un paquete)
    architect instalar                                 lo instalado hasta ahora

Los paquetes van al entorno actual y se apuntan en ``requirements.txt``; las
skills a ``~/.ai_architect/skills``. En ``hacer``, el agente tiene la misma
herramienta y pide permiso antes de usarla.
"""

from __future__ import annotations

from typing import Any

from ai_architect import instalar as motor


def run(frase: str = "", project: str = ".") -> dict[str, Any]:
    texto = (frase or "").strip()

    if not texto:
        hechos = motor.instalado()
        cuerpo = "\n".join(
            f"{h['que']}: {h['nombre']} {h.get('detalle', '')}".rstrip() for h in hechos
        )

        return {
            "success": True,
            "executed": False,
            "command": "instalar",
            "instant": True,
            "installed": hechos,
            "explanation": (
                f"He instalado {len(hechos)} cosa(s)."
                if hechos
                else "No he instalado nada todavía."
            ),
            "panel": {
                "tipo": "texto",
                "titulo": "Instalado",
                "cuerpo": cuerpo or "nada",
            },
        }

    que, _, nombre = texto.partition(" ")
    que = que.lower()

    if que not in ("paquete", "skill"):
        que, nombre = ("skill" if texto.startswith("http") else "paquete"), texto

    from pathlib import Path

    if que == "paquete":
        salida = motor.paquete(nombre.strip(), Path(project) / "requirements.txt")
        dicho = (
            f"Instalado {salida['paquete']}"
            + (
                " y apuntado en requirements.txt."
                if salida.get("requirements")
                else "."
            )
            if salida.get("ok")
            else f"No pude instalar {nombre.strip()}: {salida.get('error')}"
        )

    else:
        salida = motor.skill(nombre.strip())
        dicho = (
            f"Skill «{salida['skill']}» lista en {salida['carpeta']}."
            if salida.get("ok")
            else f"No pude instalar la skill: {salida.get('error')}"
        )

    return {
        "success": bool(salida.get("ok")),
        "executed": bool(salida.get("ok")),
        "command": "instalar",
        "instant": True,
        "result": salida,
        "explanation": dicho,
        **({} if salida.get("ok") else {"error": str(salida.get("error"))}),
    }
