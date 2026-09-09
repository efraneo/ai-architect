"""WhatsApp por la Cloud API de Meta: enviar mensajes de texto.

Recibir necesita un webhook público con HTTPS, que un PC de escritorio no
tiene; por eso aquí solo se envía. Para hablarle desde el celular está
Telegram, que funciona sin abrir ningún puerto.

Variables: ``WHATSAPP_TOKEN`` (permanente, de la app de Meta) y
``WHATSAPP_PHONE_ID`` (el Phone Number ID, no el número).
"""

from __future__ import annotations

import re
from typing import Any

import requests

from ai_architect.canales import valor

TIEMPO_LIMITE = 20
VERSION = "v21.0"


def configurado() -> bool:
    return bool(valor("WHATSAPP_TOKEN") and valor("WHATSAPP_PHONE_ID"))


def normalizar(numero: str) -> str:
    """Solo dígitos, con indicativo y sin «+»: es lo que espera Meta."""
    return re.sub(r"\D", "", numero or "")


def enviar(numero: str, texto: str) -> dict[str, Any]:
    """Un mensaje de texto a un número en formato internacional. Nunca lanza."""
    if not configurado():
        return {"ok": False, "error": "falta WHATSAPP_TOKEN o WHATSAPP_PHONE_ID"}

    destino = normalizar(numero)

    if len(destino) < 8:
        return {"ok": False, "error": f"número inválido: {numero!r}"}

    url = f"https://graph.facebook.com/{VERSION}/{valor('WHATSAPP_PHONE_ID')}/messages"

    try:
        respuesta = requests.post(
            url,
            headers={"Authorization": f"Bearer {valor('WHATSAPP_TOKEN')}"},
            json={
                "messaging_product": "whatsapp",
                "to": destino,
                "type": "text",
                "text": {"body": texto[:4000]},
            },
            timeout=TIEMPO_LIMITE,
        )

    except requests.RequestException as e:
        return {"ok": False, "error": str(e)}

    if not respuesta.ok:
        return {"ok": False, "error": respuesta.text[:300]}

    return {"ok": True, "para": destino}
