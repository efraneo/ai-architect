"""Cliente MCP (Model Context Protocol) de Architect.

Portado de OpenJarvis (Apache-2.0): ``transport`` (stdio y HTTP), ``client`` (JSON-RPC),
``adaptador`` (cada herramienta remota como ``BaseTool``) y ``loader``.

La configuración vive en ``~/.ai_architect/mcp.json``::

    {"servers": [
      {"name": "archivos", "command": "npx",
       "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:/proyectos"]},
      {"name": "remoto", "url": "https://mi-servidor/mcp", "token": "..."}
    ]}
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from ai_architect.agente.rutas_agente import get_config_dir

__all__ = ["herramientas_mcp", "ruta_config", "servidores_configurados"]


def ruta_config() -> Path:
    return get_config_dir() / "mcp.json"


def servidores_configurados() -> list[dict[str, Any]]:
    """La lista «servers» del mcp.json, o vacía si no hay archivo o está mal."""
    ruta = ruta_config()
    if not ruta.is_file():
        return []
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    lista = datos.get("servers", []) if isinstance(datos, dict) else datos
    return [s for s in lista if isinstance(s, dict)] if isinstance(lista, list) else []


def herramientas_mcp() -> tuple[list[Any], list[Any]]:
    """``(herramientas, clientes)``: conserva los clientes o se cierran las conexiones."""
    servidores = servidores_configurados()
    if not servidores:
        return [], []
    from ai_architect.agente.mcp.loader import load_mcp_tools_from_config

    cfg = SimpleNamespace(enabled=True, servers=servidores)
    return load_mcp_tools_from_config(cfg)
