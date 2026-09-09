"""Visión: lo que ve la cámara, en palabras.

«¿Qué ves?», «lee lo que tengo en la mano», «¿cuántas personas hay?». La cara
ya tiene la cámara encendida (para seguirte con la mirada); a la orden toma
un fotograma, lo manda a ``/mirar`` y aquí se describe con un modelo con
visión (OpenAI, ``ARCHITECT_MODELO_VISION``, por defecto ``gpt-4o-mini``).

Describe escenas, objetos y texto. No identifica a nadie por su cara: eso
no lo hace ni lo intenta.
"""

from __future__ import annotations

import base64
import os
import re
from typing import Any

from ai_architect.core.texto import sin_adornos

MODELO = "gpt-4o-mini"

PIDE = (
    "que ves",
    "que estas viendo",
    "que hay en la camara",
    "que hay delante",
    "mira esto",
    "mira lo que tengo",
    "mira la camara",
    "describe lo que ves",
    "describe la escena",
    "lee esto",
    "lee lo que ves",
    "lee lo que tengo",
    "que dice aqui",
    "que dice esto",
    "cuantas personas ves",
    "cuantas personas hay",
    "hay alguien",
    "que tengo en la mano",
    "que objeto es este",
    "que es esto",
    "abre los ojos",
    "usa la camara",
)

GUION = (
    "Eres los ojos de Architect, un asistente personal en español. Describe en una o dos "
    "frases, claras y concretas, lo que se ve en la imagen y responde a la pregunta si la hay. "
    "Si hay texto legible, léelo. No identifiques a ninguna persona por su nombre ni "
    "describas rasgos que sirvan para identificarla; di solo cuántas personas hay y qué hacen."
)

_ultima: dict[str, Any] = {}


def modelo() -> str:
    return os.getenv("ARCHITECT_MODELO_VISION", "").strip() or MODELO


def disponible() -> bool:
    from ai_architect.voz.hablar import _asegurar_entorno

    _asegurar_entorno()

    return bool(os.getenv("OPENAI_API_KEY"))


def _cliente() -> Any:
    from ai_architect.voz.escuchar import _con_openai

    return _con_openai()


def _a_uri(imagen: bytes | str) -> str:
    if isinstance(imagen, str):
        if imagen.startswith("data:"):
            return imagen

        return "data:image/jpeg;base64," + imagen.strip()

    return "data:image/jpeg;base64," + base64.b64encode(imagen).decode("ascii")


def describir(imagen: bytes | str, pregunta: str = "") -> dict[str, Any]:
    """Qué hay en la imagen. Nunca lanza: devuelve ``ok`` y ``texto`` o ``error``."""
    if not imagen:
        return {"ok": False, "error": "no llegó ninguna imagen"}

    if not disponible():
        return {
            "ok": False,
            "error": "para ver necesito OPENAI_API_KEY (modelo con visión)",
        }

    contenido: list[dict[str, Any]] = [
        {"type": "text", "text": pregunta.strip() or "¿Qué ves?"},
        {"type": "image_url", "image_url": {"url": _a_uri(imagen), "detail": "low"}},
    ]

    try:
        respuesta = _cliente().chat.completions.create(
            model=modelo(),
            messages=[
                {"role": "system", "content": GUION},
                {"role": "user", "content": contenido},
            ],
            max_tokens=200,
            temperature=0.2,
        )
        texto = str(respuesta.choices[0].message.content or "").strip()

    except Exception as e:  # noqa: BLE001 - sin red o sin modelo se dice
        return {"ok": False, "error": f"no pude mirar: {e}"}

    if not texto:
        return {"ok": False, "error": "el modelo no dijo nada de la imagen"}

    _ultima.update({"pregunta": pregunta, "texto": texto})

    return {"ok": True, "texto": texto, "modelo": modelo()}


def ultima() -> dict[str, Any]:
    return dict(_ultima)


def por_voz(frase: str) -> dict[str, Any] | None:
    """«Qué ves», «lee esto», «cuántas personas hay»: la cara toma la foto."""
    limpia = re.sub(r"^(?:architect|arquitecto)[,:]?\s*", "", sin_adornos(frase))

    if not limpia:
        return None

    if not (limpia in PIDE or any(limpia.startswith(p) for p in PIDE)):
        return None

    if not disponible():
        return {"respuesta": "Para ver necesito la clave de OpenAI (OPENAI_API_KEY)."}

    pregunta = re.sub(r"^(?:architect|arquitecto)[,:]?\s*", "", frase.strip())

    return {"respuesta": "Déjame mirar.", "mirar": pregunta or "¿Qué ves?"}
