"""El celular como herramienta del agente: una para lo inofensivo (música,
bloquear, abrir) y otra para llamar o mandar SMS, que pide permiso."""

from __future__ import annotations

from typing import Any

from ai_architect.agente.herramientas_base import BaseTool, ToolSpec
from ai_architect.agente.tipos import ToolResult


def _ejecutar(nombre: str, accion: str, argumento: str) -> ToolResult:
    from ai_architect.canales import celular

    salida = celular.ordenar(accion, argumento)

    return ToolResult(
        tool_name=nombre,
        content=(
            f"Mandado al celular: {salida['texto']}"
            if salida.get("ok")
            else f"No pude: {salida.get('error')}"
        ),
        success=bool(salida.get("ok")),
    )


class Celular(BaseTool):
    tool_id = "celular"

    @property
    def spec(self) -> ToolSpec:
        from ai_architect.canales import celular

        seguras = [a for a in celular.ACCIONES if a not in celular.CON_PERMISO]

        return ToolSpec(
            name="celular",
            description=(
                "Manda una orden al celular del usuario: "
                + "; ".join(f"{a} ({celular.ACCIONES[a]})" for a in seguras)
                + ". Para llamar usa celular_llamar."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "accion": {"type": "string", "enum": seguras},
                    "argumento": {
                        "type": "string",
                        "description": "Canción/artista, app, URL, volumen 0-100… según la acción.",
                    },
                },
                "required": ["accion"],
            },
            category="canales",
        )

    def execute(self, **params: Any) -> ToolResult:
        return _ejecutar(
            "celular", str(params.get("accion", "")), str(params.get("argumento", ""))
        )


class CelularLlamar(BaseTool):
    tool_id = "celular_llamar"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="celular_llamar",
            description="Llama desde el celular del usuario a un contacto o número, o manda un SMS (mensaje: «número|texto»).",
            parameters={
                "type": "object",
                "properties": {
                    "accion": {"type": "string", "enum": ["llamar", "mensaje"]},
                    "argumento": {
                        "type": "string",
                        "description": "Contacto o número; para SMS «número|texto».",
                    },
                },
                "required": ["accion", "argumento"],
            },
            category="canales",
            requires_confirmation=True,
        )

    def execute(self, **params: Any) -> ToolResult:
        return _ejecutar(
            "celular_llamar",
            str(params.get("accion", "llamar")),
            str(params.get("argumento", "")),
        )
