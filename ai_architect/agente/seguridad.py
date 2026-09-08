"""Piezas de OpenJarvis que aquí se sustituyen por decisiones propias.

- ``load_config``: OpenJarvis lee un TOML de 31 secciones; AI-architect no. Lanza para que el
  código portado caiga a sus valores por defecto (todos los usos están en ``try/except``).
- ``authorize_secured_operation``: el RBAC por capacidades vivía en Rust. Aquí la única puerta es
  la confirmación humana del ``ToolExecutor``, así que se autoriza y se deja constancia.
- ``get_rust_module``: no hay Rust; lanza ``ImportError`` para que corran los caminos en Python.
"""

from __future__ import annotations

from typing import Any

from ai_architect.agente.tipos import ToolResult


def load_config() -> Any:
    raise RuntimeError("AI-architect no usa la configuración TOML de OpenJarvis")


def authorize_secured_operation(
    operation: str,
    required_capabilities: list[str],
    *,
    bus: Any = None,
    capability_policy: Any = None,  # noqa: ARG001
    rate_limiter: Any = None,  # noqa: ARG001
    agent_id: str = "",
) -> ToolResult:
    return ToolResult(tool_name=operation, content="autorizado", success=True)


def get_rust_module() -> Any:
    raise ImportError("AI-architect no incluye el módulo Rust de OpenJarvis")
