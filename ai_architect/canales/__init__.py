"""
=========================================================
Canales

Por dónde Architect habla contigo además del micrófono: el celular
(Telegram), el correo y WhatsApp.
=========================================================

Cada canal es un módulo pequeño sobre ``requests`` o la biblioteca estándar,
sin SDKs. Se configuran con variables en ``~/.ai_architect/.env`` (o en el
entorno), y **lo que no está configurado no aparece**: ni como herramienta del
agente ni en la lista de ``architect canales``.

    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID          el celular (bot de @BotFather)
    CORREO_SMTP_HOST, CORREO_SMTP_PUERTO,
    CORREO_USUARIO, CORREO_CLAVE, CORREO_DESDE,
    CORREO_IMAP_HOST                                enviar y leer correo
    WHATSAPP_TOKEN, WHATSAPP_PHONE_ID              WhatsApp Cloud API (Meta)

Lo que envía cosas pide permiso, como todo lo que escribe: sin ``--si`` queda
en la cola de aprobaciones.
"""

from __future__ import annotations

import os
from typing import Any

from ai_architect.core.env_file import cargar_todo

VARIABLES: dict[str, tuple[str, ...]] = {
    "telegram": ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"),
    "correo": (
        "CORREO_SMTP_HOST",
        "CORREO_USUARIO",
        "CORREO_CLAVE",
    ),
    "whatsapp": ("WHATSAPP_TOKEN", "WHATSAPP_PHONE_ID"),
    "hogar": ("HOGAR_URL", "HOGAR_TOKEN"),
}

# Cómo se consigue cada cosa, para decirlo cuando falta.
COMO_SE_CONFIGURA = {
    "telegram": (
        "crea un bot con @BotFather (te da el token), escríbele un mensaje y saca tu "
        "chat_id de https://api.telegram.org/bot<TOKEN>/getUpdates"
    ),
    "correo": (
        "los datos SMTP de tu proveedor (Hostinger: smtp.hostinger.com, puerto 465, "
        "usuario y clave del buzón); CORREO_IMAP_HOST para leer (imap.hostinger.com)"
    ),
    "whatsapp": (
        "una app de Meta con WhatsApp Cloud API: token permanente y el Phone Number ID "
        "(developers.facebook.com)"
    ),
    "hogar": (
        "la URL de tu Home Assistant (p. ej. http://homeassistant.local:8123) y un "
        "token de acceso de larga duración (perfil → Tokens)"
    ),
}


def _cargar() -> None:
    try:
        cargar_todo()

    except Exception:  # noqa: BLE001 - sin .env se mira solo el entorno
        pass


def valor(clave: str) -> str:
    _cargar()

    return os.getenv(clave, "") or ""


def configurado(canal: str) -> bool:
    return all(valor(v) for v in VARIABLES.get(canal, ()))


def disponibles() -> list[str]:
    return [c for c in VARIABLES if configurado(c)]


def que_falta(canal: str) -> list[str]:
    return [v for v in VARIABLES.get(canal, ()) if not valor(v)]


def estado() -> dict[str, Any]:
    """Cada canal: si está, qué le falta y cómo se consigue."""
    return {
        canal: {
            "configurado": configurado(canal),
            "falta": que_falta(canal),
            "como": COMO_SE_CONFIGURA[canal],
        }
        for canal in VARIABLES
    }
