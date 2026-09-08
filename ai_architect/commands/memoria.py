"""
=========================================================
Memoria

Lo que Architect recuerda de ti entre sesiones.
=========================================================

    architect memoria                              lo que sabe
    architect memoria --frase "recuerda que trabajo en Xentris y prefiero pytest"
    architect memoria --frase "olvida todo"

Además aprende solo: de cada conversación saca los hechos durables (nombre, empresa,
preferencias, proyectos) y los guarda como «automáticos»; lo que le dices con «recuerda que»
queda como «de confianza». Todo entra en los prompts de ``pide`` y ``hacer``.
"""

from __future__ import annotations

import re
from typing import Any

from ai_architect.agente import memoria
from ai_architect.core import perfil

OLVIDAR = (
    "olvida todo",
    "olvidalo todo",
    "borra tu memoria",
    "borra la memoria",
    "olvida lo que sabes",
)
RECORDAR = re.compile(
    r"^\s*(recuerda|recuérdame|acuerdate|acuérdate|anota|apunta)\s+(que\s+)?",
    re.IGNORECASE,
)


def run(
    frase: str = "", engine: Any = None
) -> dict[str, Any]:  # noqa: ARG001 - misma firma que los demás
    texto = (frase or "").strip()
    trato = perfil.como_llamarte()

    if not texto:
        lista = memoria.hechos()
        if not lista:
            return _ok(
                f"Todavía no sé nada de ti, {trato}. Dime «recuerda que…» y lo apunto.",
                [],
            )
        cuerpo = "\n".join(
            f"{i + 1}. {f.text}  ({f.trust})" for i, f in enumerate(lista)
        )
        return _ok(
            f"Esto es lo que recuerdo de ti, {trato}: {len(lista)} cosa(s).",
            lista,
            cuerpo,
        )

    if texto.lower().strip(" .!") in OLVIDAR:
        n = memoria.olvidar()
        return _ok(f"Listo, {trato}: olvidé {n} cosa(s).", [])

    hecho = RECORDAR.sub("", texto).strip()
    if memoria.recordar(hecho):
        return _ok(f"Apuntado, {trato}: {hecho}", memoria.hechos())
    return {
        "success": False,
        "executed": False,
        "command": "memoria",
        "error": "No había nada que recordar.",
        "explanation": "No había nada que recordar.",
    }


def _ok(dicho: str, lista: list[Any], cuerpo: str = "") -> dict[str, Any]:
    return {
        "success": True,
        "executed": True,
        "command": "memoria",
        "instant": True,
        "facts": [f.text for f in lista],
        "explanation": dicho,
        "panel": {
            "tipo": "texto",
            "titulo": "Memoria de Architect",
            "cuerpo": cuerpo or dicho,
        },
    }
