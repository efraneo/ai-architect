"""
=========================================================
Telegram Notifier
=========================================================

Tenía tres cosas que arreglar antes de conectarlo:

- Sin ``TELEGRAM_BOT_TOKEN`` construía la URL igual --
  ``https://api.telegram.org/botNone/sendMessage`` -- y hacía la petición.
  Una llamada de red garantizada a fallar, en cada ejecución.
- ``requests.post`` puede lanzar (red caída, DNS, tiempo agotado) y nadie lo
  recogía: un aviso que no sale tumbaba la mejora entera.
- ``load_dotenv(env_file)`` escribía en el entorno del proceso al construir,
  pudiendo pisar variables ya exportadas a propósito. Y ``python-dotenv``
  **no está declarado en ``pyproject.toml`` ni instalado**: este paquete
  llevaba tiempo siendo inimportable. Ahora lee el archivo él mismo
  (``env_file.py``), sin dependencias nuevas.
"""

from __future__ import annotations

from pathlib import Path

import requests

from ai_architect.core.env_file import valor

from .models import (
    Notification,
    NotificationResult,
)

TIEMPO_LIMITE = 20


class TelegramNotifier:
    def __init__(
        self,
        env_file: str | Path,
    ) -> None:
        # Lo que ya esté en el entorno manda sobre el archivo.
        self.token = valor("TELEGRAM_BOT_TOKEN", env_file)

        self.chat_id = valor("TELEGRAM_CHAT_ID", env_file)

    def configurado(self) -> bool:
        """¿Hay con qué enviar? Sin esto se llamaba a la API con ``None``."""
        return bool(self.token and self.chat_id)

    def send(
        self,
        notification: Notification,
    ) -> NotificationResult:
        if not self.configurado():
            return NotificationResult(
                success=False,
                provider="telegram",
                response="falta TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID",
            )

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"

        text = f"🤖 {notification.title}\n\n{notification.message}"

        try:
            response = requests.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                },
                timeout=TIEMPO_LIMITE,
            )

        except requests.RequestException as e:
            return NotificationResult(
                success=False,
                provider="telegram",
                response=str(e),
            )

        return NotificationResult(
            success=response.ok,
            provider="telegram",
            response=response.text,
        )
