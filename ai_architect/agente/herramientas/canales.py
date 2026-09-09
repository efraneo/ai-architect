"""Los canales como herramientas del agente: mandar un Telegram, un correo, un
WhatsApp, o leer el correo. Solo entran en la caja los que están configurados,
y los que envían piden permiso (sin ``--si`` quedan en la cola)."""

from __future__ import annotations

from typing import Any

from ai_architect.agente.herramientas_base import BaseTool, ToolSpec
from ai_architect.agente.tipos import ToolResult


class EnviarTelegram(BaseTool):
    tool_id = "enviar_telegram"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="enviar_telegram",
            description="Manda un mensaje de texto al celular del usuario por Telegram.",
            parameters={
                "type": "object",
                "properties": {
                    "texto": {"type": "string", "description": "El mensaje."}
                },
                "required": ["texto"],
            },
            category="canales",
            requires_confirmation=True,
        )

    def execute(self, **params: Any) -> ToolResult:
        from ai_architect.canales import telegram

        salida = telegram.enviar(str(params.get("texto", "")))

        return ToolResult(
            tool_name="enviar_telegram",
            content=(
                "Enviado."
                if salida.get("ok")
                else f"No se envió: {salida.get('description')}"
            ),
            success=bool(salida.get("ok")),
        )


class EnviarCorreo(BaseTool):
    tool_id = "enviar_correo"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="enviar_correo",
            description="Manda un correo de texto plano desde la cuenta del usuario.",
            parameters={
                "type": "object",
                "properties": {
                    "para": {"type": "string", "description": "Destinatario."},
                    "asunto": {"type": "string", "description": "Asunto."},
                    "cuerpo": {"type": "string", "description": "El texto del correo."},
                },
                "required": ["para", "asunto", "cuerpo"],
            },
            category="canales",
            requires_confirmation=True,
        )

    def execute(self, **params: Any) -> ToolResult:
        from ai_architect.canales import correo

        salida = correo.enviar(
            str(params.get("para", "")),
            str(params.get("asunto", "")),
            str(params.get("cuerpo", "")),
        )

        return ToolResult(
            tool_name="enviar_correo",
            content=(
                f"Enviado a {salida.get('para')}."
                if salida.get("ok")
                else f"No se envió: {salida.get('error')}"
            ),
            success=bool(salida.get("ok")),
        )


class LeerCorreo(BaseTool):
    tool_id = "leer_correo"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="leer_correo",
            description="Lee los últimos correos de la bandeja de entrada del usuario (de, asunto, fecha, texto).",
            parameters={
                "type": "object",
                "properties": {
                    "cuantos": {
                        "type": "integer",
                        "description": "Cuántos (por defecto 5).",
                    }
                },
            },
            category="canales",
        )

    def execute(self, **params: Any) -> ToolResult:
        from ai_architect.canales import correo

        salida = correo.leer(int(params.get("cuantos") or 5))

        if not salida.get("ok"):
            return ToolResult(
                tool_name="leer_correo",
                content=f"No pude leer: {salida.get('error')}",
                success=False,
            )

        lineas = [
            f"- {c['fecha']} · {c['de']} · {c['asunto']}\n  {c['texto'][:300]}"
            for c in salida["correos"]
        ]

        return ToolResult(
            tool_name="leer_correo",
            content="\n".join(lineas) or "No hay correos.",
            success=True,
        )


class EnviarWhatsApp(BaseTool):
    tool_id = "enviar_whatsapp"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="enviar_whatsapp",
            description="Manda un mensaje de WhatsApp a un número en formato internacional (ej. 573001234567).",
            parameters={
                "type": "object",
                "properties": {
                    "numero": {
                        "type": "string",
                        "description": "Número con indicativo.",
                    },
                    "texto": {"type": "string", "description": "El mensaje."},
                },
                "required": ["numero", "texto"],
            },
            category="canales",
            requires_confirmation=True,
        )

    def execute(self, **params: Any) -> ToolResult:
        from ai_architect.canales import whatsapp

        salida = whatsapp.enviar(
            str(params.get("numero", "")), str(params.get("texto", ""))
        )

        return ToolResult(
            tool_name="enviar_whatsapp",
            content=(
                f"Enviado a {salida.get('para')}."
                if salida.get("ok")
                else f"No se envió: {salida.get('error')}"
            ),
            success=bool(salida.get("ok")),
        )


def herramientas_de_canales() -> list[BaseTool]:
    """Las de los canales configurados, nada más."""
    from ai_architect import canales

    lista: list[BaseTool] = []

    if canales.configurado("telegram"):
        lista.append(EnviarTelegram())

    if canales.configurado("correo"):
        lista.append(EnviarCorreo())

        if canales.valor("CORREO_IMAP_HOST"):
            lista.append(LeerCorreo())

    if canales.configurado("whatsapp"):
        lista.append(EnviarWhatsApp())

    return lista
