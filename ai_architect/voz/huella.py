"""La huella de voz: que las órdenes sensibles vengan de quien manda.

Seguridad biométrica opcional. Con ``resemblyzer`` instalado (un modelo de
embeddings de voz pequeño, libre), Architect aprende la voz del dueño con
«aprende mi voz» y, desde entonces, compara cada audio que le llega con esa
huella. Lo sensible (permisos, «adelante», desbloquear el celular o la casa)
solo se acepta si la voz se parece lo bastante.

Sin ``resemblyzer`` no se finge nada: ``comparar`` devuelve ``None`` («no
puedo saberlo»), el resto de Architect sigue como siempre, y el agente de
voz lo cuenta como algo que falta. Se instala con «instala la huella de voz»
(``pip install resemblyzer``).

La huella es una lista de 256 números en ``huella.json``, en la carpeta de
Architect: no es la voz, no sirve para reconstruirla y no sale de la máquina.
"""

from __future__ import annotations

import io
import json
import math
import os
import wave
from pathlib import Path
from typing import Any

from ai_architect.core.texto import sin_adornos

ARCHIVO = "huella.json"

UMBRAL = 0.75
MINIMO_SEGUNDOS = 1.2

APRENDER = (
    "aprende mi voz",
    "memoriza mi voz",
    "registra mi voz",
    "graba mi voz",
    "reconoce mi voz",
    "guarda mi huella de voz",
)

OLVIDAR = ("olvida mi voz", "borra mi huella de voz", "borra mi voz")

SENSIBLES = (
    "adelante",
    "desbloquea",
    "abre la puerta",
    "abre el porton",
    "abre el garaje",
    "quita la alarma",
    "desactiva la alarma",
    "transfiere",
    "paga",
)

_ultimo_parecido: float | None = None
_codificador: Any = None


def ruta() -> Path:
    from ai_architect.agente.rutas_agente import get_config_dir

    return Path(get_config_dir()) / ARCHIVO


def umbral() -> float:
    try:
        return float(os.getenv("ARCHITECT_HUELLA_UMBRAL", "") or UMBRAL)

    except ValueError:
        return UMBRAL


def disponible() -> bool:
    try:
        import resemblyzer  # noqa: F401

    except ImportError:
        return False

    return True


def aprendida() -> bool:
    return bool(_cargar())


def _cargar() -> list[float]:
    try:
        datos = json.loads(ruta().read_text(encoding="utf-8"))

    except (OSError, ValueError):
        return []

    return (
        [float(x) for x in datos.get("huella", [])] if isinstance(datos, dict) else []
    )


def _guardar(vector: list[float], muestras: int) -> None:
    ruta().parent.mkdir(parents=True, exist_ok=True)
    ruta().write_text(
        json.dumps({"huella": vector, "muestras": muestras}, ensure_ascii=False),
        encoding="utf-8",
    )


# --- el audio -----------------------------------------------------------------------------


def _wav_a_muestras(datos: bytes) -> tuple[list[float], int]:
    """Un WAV PCM (lo que manda la cara) a valores entre -1 y 1 y su frecuencia."""
    with wave.open(io.BytesIO(datos), "rb") as w:
        canales = w.getnchannels()
        ancho = w.getsampwidth()
        frecuencia = w.getframerate()
        crudo = w.readframes(w.getnframes())

    if ancho != 2:
        raise ValueError(f"WAV de {ancho * 8} bits: solo sé leer 16 bits")

    import array

    enteros = array.array("h")
    enteros.frombytes(crudo[: len(crudo) - len(crudo) % 2])
    valores = [x / 32768.0 for x in enteros]

    if canales > 1:
        valores = valores[::canales]

    return valores, frecuencia


def _vector(datos: bytes) -> list[float] | None:
    """El embedding de la voz, o ``None`` si no hay con qué o el audio es muy corto."""
    if not disponible():
        return None

    global _codificador

    import numpy as np
    from resemblyzer import VoiceEncoder, preprocess_wav

    valores, frecuencia = _wav_a_muestras(datos)

    if len(valores) < MINIMO_SEGUNDOS * frecuencia:
        return None

    if _codificador is None:
        _codificador = VoiceEncoder(verbose=False)

    onda = preprocess_wav(np.asarray(valores, dtype=np.float32), source_sr=frecuencia)

    return [float(x) for x in _codificador.embed_utterance(onda)]


def _coseno(a: list[float], b: list[float]) -> float:
    punto = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0

    return punto / (na * nb)


# --- aprender y comparar ------------------------------------------------------------------


def aprender(datos: bytes) -> dict[str, Any]:
    """Suma este audio a la huella (media móvil). Cuantas más frases, mejor."""
    if not disponible():
        return {
            "ok": False,
            "error": "para reconocer tu voz necesito el paquete resemblyzer (pip install resemblyzer)",
        }

    try:
        nuevo = _vector(datos)

    except Exception as e:  # noqa: BLE001 - un audio raro no revienta
        return {"ok": False, "error": f"no pude leer el audio: {e}"}

    if nuevo is None:
        return {"ok": False, "error": "el audio es muy corto; dime una frase más larga"}

    try:
        anterior = json.loads(ruta().read_text(encoding="utf-8"))
        vieja = [float(x) for x in anterior.get("huella", [])]
        muestras = int(anterior.get("muestras", 0))

    except (OSError, ValueError, AttributeError):
        vieja, muestras = [], 0

    if vieja and len(vieja) == len(nuevo):
        vector = [
            (v * muestras + n) / (muestras + 1)
            for v, n in zip(vieja, nuevo, strict=False)
        ]
        muestras += 1

    else:
        vector, muestras = nuevo, 1

    _guardar(vector, muestras)

    return {"ok": True, "muestras": muestras}


def comparar(datos: bytes) -> float | None:
    """Cuánto se parece este audio a la huella (0 a 1), o ``None`` si no se puede saber."""
    global _ultimo_parecido

    huella = _cargar()

    if not huella:
        _ultimo_parecido = None

        return None

    try:
        vector = _vector(datos)

    except Exception:  # noqa: BLE001
        _ultimo_parecido = None

        return None

    if vector is None or len(vector) != len(huella):
        _ultimo_parecido = None

        return None

    _ultimo_parecido = _coseno(huella, vector)

    return _ultimo_parecido


def ultimo_parecido() -> float | None:
    return _ultimo_parecido


def es_sensible(frase: str) -> bool:
    limpia = sin_adornos(frase)

    return any(
        limpia == s or limpia.startswith(s + " ") or limpia.startswith(s)
        for s in SENSIBLES
    )


def autoriza(frase: str) -> tuple[bool, str]:
    """Si la última voz oída puede dar esta orden. Sin huella aprendida o sin
    ``resemblyzer`` no se bloquea nada: no se puede saber, y se dice."""
    if not es_sensible(frase) or not aprendida() or not disponible():
        return True, ""

    parecido = _ultimo_parecido

    if parecido is None:
        return True, ""

    if parecido >= umbral():
        return True, ""

    return (
        False,
        f"Esa orden solo la acepto con la voz de quien me configuró (parecido {parecido:.2f}).",
    )


def olvidar() -> bool:
    try:
        ruta().unlink()

    except OSError:
        return False

    return True


def estado() -> dict[str, Any]:
    return {
        "disponible": disponible(),
        "aprendida": aprendida(),
        "umbral": umbral(),
        "ultimo_parecido": _ultimo_parecido,
    }


def por_voz(frase: str, ultimo_audio: bytes | None = None) -> dict[str, Any] | None:
    """«Aprende mi voz» con el audio recién oído; «olvida mi voz»."""
    limpia = sin_adornos(frase)

    if not limpia:
        return None

    if limpia in OLVIDAR:
        return {
            "respuesta": (
                "Listo, olvidé tu huella de voz."
                if olvidar()
                else "No tenía huella guardada."
            )
        }

    if limpia not in APRENDER:
        return None

    if not disponible():
        return {
            "respuesta": (
                "Para reconocer tu voz me falta el paquete resemblyzer. "
                "Dime «instala la huella de voz» y lo instalo."
            ),
            "mejora": "huella de voz sin resemblyzer",
        }

    if not ultimo_audio:
        return {
            "respuesta": "Dímelo por el micrófono, con una frase larga, y aprendo tu voz."
        }

    salida = aprender(ultimo_audio)

    if not salida.get("ok"):
        return {"respuesta": str(salida.get("error"))}

    return {
        "respuesta": f"Aprendida tu voz ({salida['muestras']} muestra(s)). Repítelo un par de veces más y la afino."
    }
