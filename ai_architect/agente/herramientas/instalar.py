"""Que el agente pueda procurarse lo que le falta: un paquete de Python o una
skill de GitHub. Pide permiso como todo lo que cambia la máquina."""

from __future__ import annotations

from typing import Any

from ai_architect.agente.herramientas_base import BaseTool, ToolSpec
from ai_architect.agente.tipos import ToolResult


class InstalarTool(BaseTool):
    tool_id = "instalar"

    def __init__(self, requisitos: str | None = "requirements.txt") -> None:
        self._requisitos = requisitos

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="instalar",
            description=(
                "Instala lo que falte: un paquete de Python (pip, y lo apunta en "
                "requirements.txt) o una skill desde una URL de GitHub."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "que": {
                        "type": "string",
                        "enum": ["paquete", "skill"],
                        "description": "«paquete» de PyPI o «skill» de GitHub.",
                    },
                    "nombre": {
                        "type": "string",
                        "description": "El nombre del paquete (con versión si hace falta) o la URL de la skill.",
                    },
                },
                "required": ["que", "nombre"],
            },
            category="sistema",
            # Por decisión de Efraín: lo que necesite para cumplir una orden se lo
            # instala él solo (paquetes, skills). El código propio sigue con «adelante».
            requires_confirmation=False,
            timeout_seconds=600,
        )

    def execute(self, **params: Any) -> ToolResult:
        from ai_architect import instalar

        que = str(params.get("que", ""))
        nombre = str(params.get("nombre", ""))

        if que == "paquete":
            salida = instalar.paquete(nombre, self._requisitos)
            texto = (
                f"Instalado {salida['paquete']}"
                + (
                    " y apuntado en requirements.txt."
                    if salida.get("requirements")
                    else "."
                )
                if salida.get("ok")
                else f"No se pudo instalar: {salida.get('error')}"
            )

        elif que == "skill":
            salida = instalar.skill(nombre)
            texto = (
                f"Skill «{salida['skill']}» instalada en {salida['carpeta']} ({salida['archivos']} archivo(s))."
                if salida.get("ok")
                else f"No se pudo instalar la skill: {salida.get('error')}"
            )

        else:
            return ToolResult(
                tool_name="instalar", content="Di «paquete» o «skill».", success=False
            )

        if salida.get("ok"):
            try:
                from ai_architect.agente import memoria

                memoria.recordar(
                    f"Instaló {que} {nombre[:80]} por su cuenta", fuente="instalar"
                )

            except Exception:  # noqa: BLE001 - la memoria es un extra
                pass

        return ToolResult(
            tool_name="instalar", content=texto, success=bool(salida.get("ok"))
        )
