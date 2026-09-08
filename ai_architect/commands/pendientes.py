"""
=========================================================
Pendientes · Aprobar · Rechazar

Los cambios que Architect quiso hacer y esperan tu permiso.
=========================================================

Cuando ``hacer`` corre sin ``--si`` y el agente quiere escribir un archivo, aplicar un parche,
ejecutar un comando o hacer un commit, la acción no se pierde: queda en cola (SQLite,
``~/.ai_architect/approvals.db``, portado de OpenJarvis Apache-2.0) con todo lo necesario
para ejecutarla después.

    architect pendientes                      lo que espera
    architect aprobar --frase abc123          ejecuta esa acción
    architect aprobar --frase todo            ejecuta todas
    architect rechazar --frase abc123         la descarta

Las acciones vencen a las 24 horas.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_architect.agente.aprobaciones import ApprovalStore, PendingAction

TIPO = "hacer"


def almacen(ruta: str = "") -> ApprovalStore:
    return ApprovalStore(ruta)


def encolar(
    repositorio: Path,
    herramienta: str,
    argumentos: dict[str, Any],
    orden: str,
    ruta_db: str = "",
) -> PendingAction:
    """Guarda una acción que el agente quiso hacer sin permiso."""
    descripcion = _describir(herramienta, argumentos)
    return almacen(ruta_db).queue_action(
        action_type=TIPO,
        description=descripcion,
        payload={
            "repositorio": str(repositorio),
            "herramienta": herramienta,
            "argumentos": argumentos,
            "orden": orden[:300],
        },
        permission_key=f"hacer:{herramienta}",
        tier="high" if herramienta in ("shell_exec", "git_commit") else "medium",
    )


def _describir(herramienta: str, args: dict[str, Any]) -> str:
    if herramienta == "file_write":
        return f"escribir {args.get('path', '?')} ({len(str(args.get('content', '')))} caracteres)"
    if herramienta == "apply_patch":
        return f"aplicar un parche ({len(str(args.get('patch', args.get('diff', ''))))} caracteres)"
    if herramienta == "shell_exec":
        return f"ejecutar: {str(args.get('command', ''))[:120]}"
    if herramienta == "git_commit":
        return f"commit: {str(args.get('message', ''))[:120]}"
    return f"{herramienta} {json.dumps(args, ensure_ascii=False)[:120]}"


def listar(ruta_db: str = "") -> dict[str, Any]:
    tienda = almacen(ruta_db)
    tienda.expire_stale()
    acciones = tienda.list_pending()
    filas = [
        f"{a.id} · {a.description} · repo {Path(a.payload.get('repositorio', '')).name}"
        for a in acciones
    ]
    dicho = (
        f"{len(acciones)} acción(es) pendiente(s) de tu permiso."
        if acciones
        else "No hay nada pendiente de aprobar."
    )
    return {
        "success": True,
        "executed": False,
        "command": "pendientes",
        "instant": True,
        "pending": [{**a.to_dict(), "payload": a.payload} for a in acciones],
        "explanation": dicho
        + (" Aprueba con: architect aprobar --frase <id>" if acciones else ""),
        "panel": {
            "tipo": "texto",
            "titulo": "Pendientes",
            "cuerpo": "\n".join(filas) or dicho,
        },
    }


def aprobar(que: str, ruta_db: str = "") -> dict[str, Any]:
    """Ejecuta una acción pendiente (o todas) con el permiso ya dado."""
    tienda = almacen(ruta_db)
    tienda.expire_stale()
    objetivo = (que or "").strip().lower()
    acciones = tienda.list_pending()
    if objetivo in ("todo", "todas", "all"):
        elegidas = acciones
    else:
        elegidas = (
            [a for a in acciones if a.id.startswith(objetivo)] if objetivo else []
        )
    if not elegidas:
        return {
            "success": False,
            "executed": False,
            "command": "aprobar",
            "error": "No encontré esa acción pendiente.",
            "explanation": "No encontré esa acción pendiente. Mira «architect pendientes».",
        }

    hechas: list[str] = []
    for a in elegidas:
        resultado = _ejecutar(a)
        tienda.update_status(a.id, "approved" if resultado.success else "failed")
        marca = "✓" if resultado.success else "✗"
        hechas.append(f"{marca} {a.description}: {str(resultado.content)[:200]}")
    dicho = f"Ejecuté {sum(1 for h in hechas if h.startswith('✓'))} de {len(elegidas)} acción(es)."
    return {
        "success": True,
        "executed": True,
        "command": "aprobar",
        "instant": True,
        "done": hechas,
        "explanation": dicho,
        "panel": {"tipo": "texto", "titulo": "Aprobado", "cuerpo": "\n".join(hechas)},
    }


def rechazar(que: str, ruta_db: str = "") -> dict[str, Any]:
    tienda = almacen(ruta_db)
    objetivo = (que or "").strip().lower()
    acciones = [
        a for a in tienda.list_pending() if objetivo and a.id.startswith(objetivo)
    ]
    if not acciones:
        return {
            "success": False,
            "executed": False,
            "command": "rechazar",
            "error": "No encontré esa acción pendiente.",
            "explanation": "No encontré esa acción pendiente.",
        }
    for a in acciones:
        tienda.update_status(a.id, "denied")
    return {
        "success": True,
        "executed": True,
        "command": "rechazar",
        "instant": True,
        "explanation": f"Descarté {len(acciones)} acción(es).",
    }


def _ejecutar(a: PendingAction) -> Any:
    from ai_architect.agente import caja
    from ai_architect.agente.herramientas_base import ToolExecutor
    from ai_architect.agente.tipos import ToolCall

    repositorio = Path(str(a.payload.get("repositorio", ".")))
    herramientas = caja.herramientas_para(repositorio, con_skills=False, con_mcp=False)
    ejecutor = ToolExecutor(
        herramientas, interactive=True, confirm_callback=lambda _p: True
    )
    llamada = ToolCall(
        id=f"aprobado_{a.id}",
        name=str(a.payload.get("herramienta", "")),
        arguments=json.dumps(a.payload.get("argumentos") or {}),
    )
    return ejecutor.execute(llamada)


def run(accion: str = "listar", que: str = "", ruta_db: str = "") -> dict[str, Any]:
    if accion == "aprobar":
        return aprobar(que, ruta_db)
    if accion == "rechazar":
        return rechazar(que, ruta_db)
    return listar(ruta_db)
