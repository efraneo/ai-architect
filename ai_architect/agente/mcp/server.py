# mypy: ignore-errors
# Portado de OpenJarvis (https://github.com/openjarvis) — Apache License 2.0.
# Copyright de los autores de OpenJarvis. Archivo modificado para AI-architect (8 sep 2026):
# imports reescritos y acoplamientos a Rust/config sustituidos por piezas propias.
# La licencia completa está en ai_architect/agente/LICENCIA-OpenJarvis.txt.

"""MCP Server — wraps OpenJarvis tools as MCP-discoverable tools."""

from __future__ import annotations

import logging
from typing import Any

from ai_architect.agente.eventos import EventBus
from ai_architect.agente.herramientas_base import BaseTool, ToolExecutor
from ai_architect.agente.mcp.protocol import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    MCPRequest,
    MCPResponse,
)
from ai_architect.agente.tipos import ToolCall

logger = logging.getLogger(__name__)

_MCP_AGENT_ID = "mcp"

# Tool annotation hints per MCP spec 2025-11-25
_TOOL_ANNOTATIONS: dict[str, dict[str, Any]] = {
    "memory_store": {"destructiveHint": True, "readOnlyHint": False},
    "memory_retrieve": {"readOnlyHint": True, "destructiveHint": False},
    "memory_search": {"readOnlyHint": True, "destructiveHint": False},
    "memory_index": {"destructiveHint": True, "readOnlyHint": False},
    "calculator": {"readOnlyHint": True, "destructiveHint": False},
    "think": {"readOnlyHint": True, "destructiveHint": False},
    "retrieval": {"readOnlyHint": True, "destructiveHint": False},
    "llm": {"readOnlyHint": False, "destructiveHint": False},
    "file_read": {"readOnlyHint": True, "destructiveHint": False},
    "web_search": {"readOnlyHint": True, "destructiveHint": False},
    "code_interpreter": {"destructiveHint": True, "readOnlyHint": False},
    "repl": {"destructiveHint": True, "readOnlyHint": False},
    "channel_send": {"destructiveHint": True, "readOnlyHint": False},
    "channel_list": {"readOnlyHint": True, "destructiveHint": False},
    "channel_status": {"readOnlyHint": True, "destructiveHint": False},
}


class MCPServer:
    """MCP server that exposes OpenJarvis tools via JSON-RPC.

    Parameters
    ----------
    tools:
        List of ``BaseTool`` instances to expose.  If ``None``, auto-discovers
        all registered tools from ``ToolRegistry``.
    """

    SERVER_NAME = "openjarvis"
    SERVER_VERSION = "0.1.0"
    PROTOCOL_VERSION = "2025-11-25"

    def __init__(
        self,
        tools: list[BaseTool] | None = None,
        *,
        bus: EventBus | None = None,
        capability_policy: Any | None = None,
        rate_limiter: Any | None = None,
        agent_id: str = _MCP_AGENT_ID,
    ) -> None:
        """Create an MCP server with the same dispatch gates as other agents.

        ``agent_id`` is deliberately non-empty by default: capability policy,
        rate-limit and audit records must never collapse MCP traffic into the
        anonymous ``""`` identity.  Callers that enable a security profile
        pass its policy and limiter here; ``ToolExecutor`` then applies both
        declared and canonical built-in capability requirements before a tool
        can run.
        """
        if tools is None:
            tools = self._auto_discover_tools()
        self._tools: dict[str, BaseTool] = {t.spec.name: t for t in tools}
        self._executor = ToolExecutor(
            tools,
            bus,
            capability_policy=capability_policy,
            rate_limiter=rate_limiter,
            agent_id=agent_id or _MCP_AGENT_ID,
        )

    @staticmethod
    def _auto_discover_tools() -> list[BaseTool]:
        """Architect no trae las herramientas integradas de OpenJarvis: las que
        sirve este servidor son las que se le pasan al construirlo."""
        return []

    def get_tools(self) -> list[BaseTool]:
        """Return all tool instances (for use by SystemBuilder)."""
        return list(self._tools.values())

    def handle(self, request: MCPRequest) -> MCPResponse:
        """Dispatch an MCP request and return a response."""
        if request.method == "initialize":
            return self._handle_initialize(request)
        elif request.method == "tools/list":
            return self._handle_tools_list(request)
        elif request.method == "tools/call":
            return self._handle_tools_call(request)
        else:
            return MCPResponse.error_response(
                request.id,
                METHOD_NOT_FOUND,
                f"Unknown method: {request.method}",
            )

    def _handle_initialize(self, req: MCPRequest) -> MCPResponse:
        """Handle the initialize handshake."""
        return MCPResponse(
            result={
                "protocolVersion": self.PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {"listChanged": True},
                },
                "serverInfo": {
                    "name": self.SERVER_NAME,
                    "version": self.SERVER_VERSION,
                    "title": "OpenJarvis Tool Server",
                },
            },
            id=req.id,
        )

    def _handle_tools_list(self, req: MCPRequest) -> MCPResponse:
        """Handle tools/list — return specs for all registered tools."""
        tool_list = []
        for tool in self._tools.values():
            s = tool.spec
            entry: dict[str, Any] = {
                "name": s.name,
                "description": s.description,
                "inputSchema": s.parameters,
            }
            # Add annotations if available (MCP spec 2025-11-25)
            annotations = _TOOL_ANNOTATIONS.get(s.name)
            if annotations:
                entry["annotations"] = annotations
            tool_list.append(entry)
        return MCPResponse(result={"tools": tool_list}, id=req.id)

    def _handle_tools_call(self, req: MCPRequest) -> MCPResponse:
        """Handle tools/call — execute a tool and return the result."""
        tool_name = req.params.get("name")
        arguments = req.params.get("arguments", {})

        if not tool_name:
            return MCPResponse.error_response(
                req.id,
                INVALID_PARAMS,
                "Missing required parameter: name",
            )

        if tool_name not in self._tools:
            return MCPResponse.error_response(
                req.id,
                INVALID_PARAMS,
                f"Unknown tool: {tool_name}",
            )

        try:
            import json

            tool_call = ToolCall(
                id=f"mcp-{req.id}",
                name=tool_name,
                arguments=json.dumps(arguments),
            )
            result = self._executor.execute(tool_call)
            return MCPResponse(
                result={
                    "content": [
                        {"type": "text", "text": result.content},
                    ],
                    "isError": not result.success,
                },
                id=req.id,
            )
        except Exception as exc:
            return MCPResponse.error_response(
                req.id,
                INTERNAL_ERROR,
                f"Tool execution error: {exc}",
            )


__all__ = ["MCPServer"]
