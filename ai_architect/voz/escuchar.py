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
#
# Medido el 8 sep 2026 con 3,9 s de audio: gpt-4o-mini-transcribe 1,2 s,
# gpt-4o-transcribe 1,3 s, whisper-1 4,2 s. El «mini» entiende igual de bien el
# español de estas órdenes y es el más barato: va primero.
MODELOS = ("gpt-4o-mini-transcribe", "gpt-4o-transcribe", "whisper-1")

# Un solo cliente para toda la sesión: crear uno por frase abría una conexión
# nueva cada vez, y la primera llamada de la sesión tardaba hasta 7 s.
_cliente: Any = None


def _con_openai() -> Any:
    global _cliente

    if _cliente is None:
        from openai import OpenAI

        _cliente = OpenAI()

    return _cliente


def calentar() -> None:
    """Abre la conexión antes de que haga falta, en segundo plano.

    La primera transcripción de la sesión pagaba el arranque del cliente y la
    conexión TLS: 7 s en la primera prueba real. Con esto se paga al abrir la
    cara, mientras el usuario todavía no ha dicho nada.
    """
    import threading

    def _calentar() -> None:
        try:
            _con_openai().models.retrieve(MODELOS[0])

        except Exception:  # noqa: BLE001 - es un calentamiento, no una comprobación
            pass

    if disponible():
        threading.Thread(target=_calentar, daemon=True).start()


IDIOMA = "es"

# El límite de la API son 25 MB. Con lo que manda el navegador —opus, solo
# lo que suena— una orden normal no llega a 100 KB.
LIMITE_BYTES = 24 * 1024 * 1024

# Lo que se espera oír. No es una lista cerrada: es una pista, y basta para
# que "revisa el repositorio" deje de transcribirse como "revista el
# repositorio". Sin esto el error más común son justo los nombres de los
# comandos, que es lo único que de verdad hay que acertar.
CONTEXTO = (
    "Órdenes habladas a Architect, un asistente de programación en español, "
    "al que se llama por su nombre: Architect, Arquitecto. "
    "Vocabulario probable: Architect, revisa, analiza, agentes, mejora, ejecuta, "
    "changelog, doctor, parche, diff, repositorio, commit, rama, pruebas, "
    "cobertura, dependencias, seguridad, secretos, complejidad, refactor, "
    "puntuación, incidencias, entorno, arquitecto, pásalo a Word, "
    "escritorio, documentos, ciérrala, amplíala, tabla, gráfica, resumen."
)


def es_alucinacion(texto: str) -> bool:
    """Si lo «oído» es en realidad el contexto que se le dio al transcriptor."""
    from difflib import SequenceMatcher

    plano = " ".join((texto or "").lower().split())

    if not plano:
        return False

    if plano.startswith("órdenes habladas") or plano.startswith("ordenes habladas"):
        return True

    if "vocabulario probable" in plano:
        return True

    contexto = " ".join(CONTEXTO.lower().split())

    return len(plano) > 40 and SequenceMatcher(None, plano, contexto).ratio() > 0.5


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
        cliente = _con_openai()

    except ImportError:
        return {"texto": "", "modelo": "", "error": "falta el paquete openai"}

    archivo = Path(tempfile.gettempdir()) / f"arquitecto-oido{sufijo}"

    try:
        archivo.write_bytes(datos)

    except OSError as e:
        return {"texto": "", "modelo": "", "error": str(e)}

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

        texto = str(getattr(respuesta, "text", "") or "").strip()

        if es_alucinacion(texto):
            # Con solo ruido, el transcriptor devuelve su propio contexto
            # («Órdenes habladas a Architect… Vocabulario probable…») como si
            # alguien lo hubiera dicho. En la prueba real eso llegó cinco veces
            # seguidas y, como traía «pásalo a Word», cada vez creaba un Word.
            return {"texto": "", "modelo": modelo, "error": "ruido"}

        return {"texto": texto, "modelo": modelo, "error": ""}

    return {"texto": "", "modelo": "", "error": ultimo or "no pude transcribir"}


def disponible() -> bool:
    """Si hay con qué transcribir aquí. Si no, se usa el oído del navegador."""
    import os

    from ai_architect.voz.hablar import _asegurar_entorno

    _asegurar_entorno()

    return bool(os.getenv("OPENAI_API_KEY"))
