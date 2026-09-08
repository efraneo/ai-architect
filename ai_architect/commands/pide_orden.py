"""De la intención del modelo a una orden del CLI: leer el JSON, armar los argumentos y escribir el comando equivalente.

``pide`` reexporta estos nombres."""

from __future__ import annotations

import json
import re
from types import SimpleNamespace
from typing import Any

# Comandos que tocan el repositorio del usuario. No se ejecutan sin permiso
# explícito, por muy claro que parezca lo que pidió.
MODIFICAN = {"execute"}


# Banderas que convierten un comando inofensivo en uno que escribe.
BANDERAS_QUE_ESCRIBEN = ("apply", "write")


def _leer_json(texto: str) -> dict[str, Any] | None:
    """El JSON de la respuesta, aunque venga envuelto en explicación."""
    if not texto:
        return None

    try:
        return dict(json.loads(texto))

    except (ValueError, TypeError):
        # No vino limpio; abajo se intenta rescatarlo de dentro del texto.
        pass

    # Un modelo puede envolverlo en ```json o rodearlo de texto.
    coincidencia = re.search(r"\{.*\}", texto, re.DOTALL)

    if coincidencia is None:
        return None

    try:
        return dict(json.loads(coincidencia.group(0)))

    except (ValueError, TypeError):
        return None


def _argumentos(intencion: dict[str, Any], repositorio: str) -> SimpleNamespace:
    """Los argumentos que espera la tabla del CLI, con valores por defecto."""
    instrucciones = intencion.get("instructions")

    return SimpleNamespace(
        project=str(intencion.get("project") or repositorio),
        file=intencion.get("file") or None,
        instruction=str(intencion.get("instruction") or "Improve code quality"),
        instructions=list(instrucciones) if isinstance(instrucciones, list) else None,
        apply=bool(intencion.get("apply", False)),
        ai=bool(intencion.get("ai", False)),
        version_name=str(intencion.get("version_name") or ""),
        write=bool(intencion.get("write", False)),
        since=intencion.get("since") or None,
        peticion=str(intencion.get("peticion") or ""),
        patch=intencion.get("patch") or None,
        dry_run=bool(intencion.get("dry_run", False)),
        json=False,
    )


def _como_se_escribe(nombre: str, args: SimpleNamespace) -> str:
    """El comando equivalente, para que se vea qué se va a ejecutar."""
    partes = [f"architect {nombre} {args.project}"]

    if args.file:
        partes.append(f"--file {args.file}")

    if nombre == "improve" and args.instruction:
        partes.append(f'--instruction "{args.instruction}"')

    if args.instructions:
        partes.append("--instructions " + " ".join(f'"{i}"' for i in args.instructions))

    if args.patch:
        partes.append(f"--patch {args.patch}")

    for bandera in ("apply", "ai", "write", "dry_run"):
        if getattr(args, bandera, False):
            partes.append(f"--{bandera.replace('_', '-')}")

    return " ".join(partes)


def _error(mensaje: str, **extra: Any) -> dict[str, Any]:
    return {
        "success": False,
        "executed": False,
        "error": mensaje,
        "explanation": mensaje,
        **extra,
    }
