"""
=========================================================
Escuchar

Pasar lo que dices a texto.
=========================================================

Antes lo transcribía Chrome, que manda el audio a Google y entiende el
español como quien lo aprendió de oído. Esto lo hace OpenAI, que es donde
ya hay cuenta, y **se le puede dar contexto**: pasándole las palabras que
van a salir —los nombres de los comandos, "parche", "cobertura",
"repositorio"— deja de oír "revista" donde dices "revisa".

Se piden dos modelos en orden. ``gpt-4o-transcribe`` es el sucesor de
Whisper y entiende mejor el español hablado deprisa; ``whisper-1`` está en
todas las cuentas. Si el primero no está disponible se usa el segundo sin
decir nada, porque al usuario le da igual cuál de los dos le oyó.

Cuesta dinero: unos seis milésimos de dólar por minuto de audio. Solo se
manda lo que suena — el silencio lo recorta el navegador antes de enviarlo,
así que una conversación de una hora con diez órdenes son diez segundos de
audio, no una hora.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

# En orden de preferencia. El primero que responda es el que se usa.
MODELOS = ("gpt-4o-transcribe", "whisper-1")

IDIOMA = "es"

# El límite de la API son 25 MB. Con lo que manda el navegador —opus, solo
# lo que suena— una orden normal no llega a 100 KB.
LIMITE_BYTES = 24 * 1024 * 1024

# Lo que se espera oír. No es una lista cerrada: es una pista, y basta para
# que "revisa el repositorio" deje de transcribirse como "revista el
# repositorio". Sin esto el error más común son justo los nombres de los
# comandos, que es lo único que de verdad hay que acertar.
CONTEXTO = (
    "Órdenes habladas a un asistente de programación en español. "
    "Vocabulario probable: revisa, analiza, agentes, mejora, ejecuta, "
    "changelog, doctor, parche, diff, repositorio, commit, rama, pruebas, "
    "cobertura, dependencias, seguridad, secretos, complejidad, refactor, "
    "puntuación, incidencias, entorno."
)


def transcribir(datos: bytes, sufijo: str = ".webm") -> dict[str, Any]:
    """Convierte el audio en texto. Nunca lanza."""
    if not datos:
        return {"texto": "", "modelo": "", "error": "no llegó audio"}

    if len(datos) > LIMITE_BYTES:
        return {
            "texto": "",
            "modelo": "",
            "error": f"el audio pesa {len(datos) // 1024} KB y no cabe",
        }

    try:
        from openai import OpenAI

    except ImportError:
        return {"texto": "", "modelo": "", "error": "falta el paquete openai"}

    archivo = Path(tempfile.gettempdir()) / f"arquitecto-oido{sufijo}"

    try:
        archivo.write_bytes(datos)

    except OSError as e:
        return {"texto": "", "modelo": "", "error": str(e)}

    cliente = OpenAI()

    ultimo = ""

    for modelo in MODELOS:
        try:
            with archivo.open("rb") as abierto:
                respuesta = cliente.audio.transcriptions.create(
                    model=modelo,
                    file=abierto,
                    language=IDIOMA,
                    prompt=CONTEXTO,
                )

        except Exception as e:  # noqa: BLE001 - se prueba el siguiente modelo
            ultimo = str(e)

            continue

        return {
            "texto": str(getattr(respuesta, "text", "") or "").strip(),
            "modelo": modelo,
            "error": "",
        }

    return {"texto": "", "modelo": "", "error": ultimo or "no pude transcribir"}


def disponible() -> bool:
    """Si hay con qué transcribir aquí. Si no, se usa el oído del navegador."""
    import os

    from ai_architect.voz.hablar import _asegurar_entorno

    _asegurar_entorno()

    return bool(os.getenv("OPENAI_API_KEY"))
