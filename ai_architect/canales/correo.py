"""El correo: enviar por SMTP y leer los últimos por IMAP, con la biblioteca estándar.

Variables: ``CORREO_SMTP_HOST`` (y ``CORREO_SMTP_PUERTO``, 465 por defecto: SSL
directo; 587 usa STARTTLS), ``CORREO_USUARIO``, ``CORREO_CLAVE``,
``CORREO_DESDE`` (si no, el usuario) y ``CORREO_IMAP_HOST`` para leer.
"""

from __future__ import annotations

import email
import imaplib
import smtplib
import ssl
from email.header import decode_header, make_header
from email.message import EmailMessage
from typing import Any

from ai_architect.canales import valor

TIEMPO_LIMITE = 30


def configurado() -> bool:
    return bool(
        valor("CORREO_SMTP_HOST") and valor("CORREO_USUARIO") and valor("CORREO_CLAVE")
    )


def puede_leer() -> bool:
    return configurado() and bool(valor("CORREO_IMAP_HOST"))


def enviar(para: str, asunto: str, cuerpo: str) -> dict[str, Any]:
    """Manda un correo de texto plano. Nunca lanza."""
    if not configurado():
        return {
            "ok": False,
            "error": "falta CORREO_SMTP_HOST, CORREO_USUARIO o CORREO_CLAVE",
        }

    if not para.strip() or "@" not in para:
        return {"ok": False, "error": f"destinatario inválido: {para!r}"}

    mensaje = EmailMessage()
    mensaje["From"] = valor("CORREO_DESDE") or valor("CORREO_USUARIO")
    mensaje["To"] = para.strip()
    mensaje["Subject"] = asunto.strip() or "(sin asunto)"
    mensaje.set_content(cuerpo)

    host = valor("CORREO_SMTP_HOST")
    puerto = int(valor("CORREO_SMTP_PUERTO") or 465)

    try:
        if puerto == 465:
            with smtplib.SMTP_SSL(
                host,
                puerto,
                timeout=TIEMPO_LIMITE,
                context=ssl.create_default_context(),
            ) as smtp:
                smtp.login(valor("CORREO_USUARIO"), valor("CORREO_CLAVE"))
                smtp.send_message(mensaje)

        else:
            with smtplib.SMTP(host, puerto, timeout=TIEMPO_LIMITE) as smtp:
                smtp.starttls(context=ssl.create_default_context())
                smtp.login(valor("CORREO_USUARIO"), valor("CORREO_CLAVE"))
                smtp.send_message(mensaje)

    except (smtplib.SMTPException, OSError) as e:
        return {"ok": False, "error": str(e)}

    return {"ok": True, "para": para.strip(), "asunto": mensaje["Subject"]}


def _texto(mensaje: email.message.Message) -> str:
    if mensaje.is_multipart():
        for parte in mensaje.walk():
            if parte.get_content_type() == "text/plain":
                carga = parte.get_payload(decode=True)

                if not isinstance(carga, bytes):
                    return ""

                return carga.decode(parte.get_content_charset() or "utf-8", "replace")

        return ""

    carga = mensaje.get_payload(decode=True)

    if not isinstance(carga, bytes):
        return ""

    return carga.decode(mensaje.get_content_charset() or "utf-8", "replace")


def _cabecera(valor_crudo: Any) -> str:
    try:
        return str(make_header(decode_header(str(valor_crudo or ""))))

    except Exception:  # noqa: BLE001 - una cabecera rara no impide leer el resto
        return str(valor_crudo or "")


def leer(cuantos: int = 5) -> dict[str, Any]:
    """Los últimos ``cuantos`` correos de la bandeja de entrada, resumidos."""
    if not puede_leer():
        return {
            "ok": False,
            "error": "falta CORREO_IMAP_HOST (y el usuario/clave)",
            "correos": [],
        }

    try:
        with imaplib.IMAP4_SSL(
            valor("CORREO_IMAP_HOST"), timeout=TIEMPO_LIMITE
        ) as imap:
            imap.login(valor("CORREO_USUARIO"), valor("CORREO_CLAVE"))
            imap.select("INBOX", readonly=True)

            _, datos = imap.search(None, "ALL")
            ids = (datos[0] or b"").split()[-max(1, cuantos) :]
            correos = []

            for identificador in reversed(ids):
                _, crudo = imap.fetch(identificador, "(RFC822)")
                partes = [p for p in crudo if isinstance(p, tuple)]

                if not partes:
                    continue

                mensaje = email.message_from_bytes(partes[0][1])
                correos.append(
                    {
                        "de": _cabecera(mensaje.get("From")),
                        "asunto": _cabecera(mensaje.get("Subject")),
                        "fecha": str(mensaje.get("Date") or ""),
                        "texto": " ".join(_texto(mensaje).split())[:600],
                    }
                )

    except (imaplib.IMAP4.error, OSError) as e:
        return {"ok": False, "error": str(e), "correos": []}

    return {"ok": True, "correos": correos}
