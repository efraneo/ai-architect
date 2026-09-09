"""El motor de inferencia que usa el agente, montado sobre los proveedores de AI-architect.

OpenJarvis define ``InferenceEngine.generate(messages, model=..., tools=...)`` y devuelve un
diccionario con ``content``, ``tool_calls`` y ``usage``. Los proveedores de AI-architect solo
saben ``generate(prompt) -> str``. Este adaptador une las dos cosas:

- Con OpenAI y una lista de ``tools``, llama al cliente con *function calling* nativo, que es
  lo más fiable para elegir herramientas.
- Con cualquier otro proveedor (Claude, Gemini, Ollama…) aplana la conversación en un solo
  prompt y devuelve texto; el agente ReAct se encarga de pedir herramientas en JSON.

El gasto se anota igual que en el resto de la casa (``core.gasto``).
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from ai_architect.agente.tipos import Message, Role


class InferenceEngine(ABC):
    """Contrato mínimo que esperan el orquestador y el agente ReAct."""

    engine_id: str = "motor"
    is_cloud: bool = True

    @abstractmethod
    def generate(
        self,
        messages: Sequence[Message],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> dict[str, Any]: ...


def _aplanar(messages: Sequence[Message]) -> str:
    """La conversación como un solo prompt, para proveedores sin function calling."""
    partes: list[str] = []
    for m in messages:
        rol = m.role.value if isinstance(m.role, Role) else str(m.role)
        if rol == "tool":
            partes.append(
                f"[resultado de {m.name or 'herramienta'}]\n{m.content or ''}"
            )
        elif rol == "assistant" and m.tool_calls:
            llamadas = ", ".join(f"{tc.name}({tc.arguments})" for tc in m.tool_calls)
            partes.append(f"[assistant pidió: {llamadas}]\n{m.content or ''}")
        else:
            partes.append(f"[{rol}]\n{m.content or ''}")
    return "\n\n".join(partes)


def _a_openai(m: Message) -> dict[str, Any]:
    """Un mensaje en el formato del *chat completions* de OpenAI.

    ``_message_to_dict`` (de OpenJarvis) serializa para trazas, no para la API:
    las llamadas a herramientas van como ``{"id","name","arguments"}`` y OpenAI
    exige ``{"id","type":"function","function":{"name","arguments"}}``. Con lo
    primero contestaba 400 «Missing required parameter: tool_calls[0].type» y
    ``hacer`` fallaba en la primera herramienta. Se vio en la primera prueba real.
    """
    rol = m.role.value
    d: dict[str, Any] = {"role": rol, "content": m.content or ""}

    if rol == "assistant" and m.tool_calls:
        d["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.name, "arguments": tc.arguments or "{}"},
            }
            for tc in m.tool_calls
        ]
        if not m.content:
            d["content"] = None

    if rol == "tool":
        d["tool_call_id"] = m.tool_call_id or ""

    if m.name and rol != "tool":
        d["name"] = m.name

    return d


class MotorArquitecto(InferenceEngine):
    """Adapta un proveedor de AI-architect (o un doble de pruebas) al contrato del agente.

    ``proveedor`` puede ser un ``ProviderManager``, un ``BaseProvider`` o cualquier objeto con
    ``generate(prompt) -> str``. Si trae un cliente de OpenAI (``.client`` o ``.provider.client``)
    y se le pasan ``tools``, usa function calling nativo.
    """

    engine_id = "arquitecto"

    def __init__(self, proveedor: Any = None) -> None:
        if proveedor is None:
            from ai_architect.providers.provider_manager import ProviderManager

            proveedor = ProviderManager()
        self.proveedor = proveedor

    # --- lo que hay debajo ------------------------------------------------

    def _base(self) -> Any:
        return getattr(self.proveedor, "provider", self.proveedor)

    def _cliente_openai(self) -> Any | None:
        base = self._base()
        if type(base).__name__ != "OpenAIProvider":
            return None
        try:
            return base.client
        except Exception:  # noqa: BLE001 - sin clave no hay cliente
            return None

    def soporta_herramientas(self) -> bool:
        return self._cliente_openai() is not None

    @property
    def modelo(self) -> str:
        base = self._base()
        return str(
            getattr(base, "model", "") or getattr(self.proveedor, "model", "") or ""
        )

    # --- generar ------------------------------------------------------------

    def generate(
        self,
        messages: Sequence[Message],
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> dict[str, Any]:
        tools = kwargs.get("tools")
        cliente = self._cliente_openai() if tools else None
        if cliente is not None:
            return self._con_function_calling(
                cliente, messages, model, temperature, max_tokens, tools
            )
        prompt = _aplanar(messages)
        texto = str(self.proveedor.generate(prompt))
        return {
            "content": texto,
            "tool_calls": [],
            "finish_reason": "stop",
            "usage": {},
        }

    def _con_function_calling(
        self,
        cliente: Any,
        messages: Sequence[Message],
        model: str,
        temperature: float,
        max_tokens: int,
        tools: Any,
    ) -> dict[str, Any]:
        peticion: dict[str, Any] = {
            "model": model or self.modelo,
            "messages": [_a_openai(m) for m in messages],
            "tools": list(tools),
            "tool_choice": "auto",
        }
        if not str(peticion["model"]).lower().startswith("gpt-5"):
            peticion["temperature"] = temperature
            peticion["max_tokens"] = max_tokens
        respuesta = cliente.chat.completions.create(**peticion)
        eleccion = respuesta.choices[0] if respuesta.choices else None
        mensaje = eleccion.message if eleccion is not None else None
        contenido = (mensaje.content if mensaje is not None else "") or ""
        llamadas = []
        for tc in getattr(mensaje, "tool_calls", None) or []:
            fn = getattr(tc, "function", None)
            llamadas.append(
                {
                    "id": getattr(tc, "id", "") or "",
                    "name": getattr(fn, "name", "") or "",
                    "arguments": getattr(fn, "arguments", "{}") or "{}",
                }
            )
        uso = getattr(respuesta, "usage", None)
        usage = {
            "prompt_tokens": getattr(uso, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(uso, "completion_tokens", 0) or 0,
        }
        try:
            from ai_architect.core import gasto

            gasto.registrar(
                str(peticion["model"]),
                json.dumps(peticion["messages"], ensure_ascii=False),
                contenido + json.dumps(llamadas),
            )
        except Exception:  # noqa: BLE001 - contar el gasto nunca tumba la respuesta
            pass
        return {
            "content": contenido,
            "tool_calls": llamadas,
            "finish_reason": getattr(eleccion, "finish_reason", "stop") or "stop",
            "usage": usage,
        }
