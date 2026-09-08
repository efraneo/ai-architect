"""
=========================================================
MCP

Herramientas de otros servidores (Model Context Protocol) dentro de Architect.
=========================================================

Cliente JSON-RPC portado de OpenJarvis (Apache-2.0): habla con servidores MCP por stdio
(un comando local) o por HTTP. Cada herramienta remota aparece en la caja de ``hacer`` como
una herramienta más, con el nombre del servidor como prefijo.

Configuración en ``~/.ai_architect/mcp.json``:

    {"servers": [
      {"name": "archivos", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:/proyectos"]},
      {"name": "remoto", "url": "https://mi-servidor/mcp", "token": "..."}
    ]}

    architect mcp      lista los servidores y sus herramientas
"""

from __future__ import annotations

from typing import Any

from ai_architect.agente import mcp as mod_mcp


def run() -> dict[str, Any]:
    servidores = mod_mcp.servidores_configurados()
    if not servidores:
        dicho = f"No hay servidores MCP configurados. Crea {mod_mcp.ruta_config()} con una lista «servers»."
        return _salida(dicho, [], [])
    herramientas, clientes = mod_mcp.herramientas_mcp()
    nombres = [h.spec.name for h in herramientas]
    for c in clientes:
        try:
            c.close()
        except Exception:  # noqa: BLE001 - cerrar es cortesía
            pass
    dicho = (
        f"{len(servidores)} servidor(es) MCP, {len(nombres)} herramienta(s): "
        + ", ".join(nombres)
        + "."
        if nombres
        else f"{len(servidores)} servidor(es) configurado(s), pero ninguno respondió con herramientas."
    )
    return _salida(dicho, servidores, nombres)


def _salida(
    dicho: str, servidores: list[dict[str, Any]], nombres: list[str]
) -> dict[str, Any]:
    return {
        "success": True,
        "executed": False,
        "command": "mcp",
        "instant": True,
        "servers": [s.get("name", "?") for s in servidores],
        "tools": nombres,
        "explanation": dicho,
        "panel": {"tipo": "texto", "titulo": "MCP", "cuerpo": dicho},
    }
