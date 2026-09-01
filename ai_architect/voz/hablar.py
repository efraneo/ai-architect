"""
=========================================================
Hablar

Que el arquitecto responda en voz alta.
=========================================================

Hay tres formas de conseguir voz, y ninguna es "la buena" en todas las
máquinas. Por eso esto **detecta lo que hay** en vez de suponer:

1. **Piper** (local, gratis, la mejor para español latino masculino). Hay que
   bajar el binario y una voz, pero luego funciona sin internet y sin coste.
2. **OpenAI** (de pago, buena calidad, suena neutro más que latino).
3. **Windows** (gratis y ya instalado, pero **solo con las voces que tengas**).

Sobre este equipo, al escribir esto, Windows solo tenía voces **femeninas**
en español: Sabina (es-MX), Helena (es-ES) y Zira (en-US). Para una voz
masculina en español hay que instalar Raúl o Pablo desde Configuración →
Hora e idioma → Voz, o usar Piper.

Se dice cuál se está usando y qué falta para la que se quería: fingir que se
tiene una voz masculina latina cuando la que suena es femenina sería
mentirle al usuario en lo primero que va a notar.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path
from typing import Any

TIEMPO_LIMITE = 60

# Dónde se buscan las voces de Piper, si están.
CARPETA_VOCES = Path.home() / ".ai_architect" / "voces"

# Las voces masculinas de español latino que Piper publica de verdad. Se
# comprobó contra el repositorio: `es_AR/daniel` no existe —la argentina es
# `daniela`, femenina—, así que las dos opciones son mexicanas. La primera
# que aparezca es la que se usa, salvo que el perfil diga otra.
VOCES_PIPER = (
    "es_MX-claude-high.onnx",
    "es_MX-ald-medium.onnx",
)

# Donde queda el binario si se instaló con el propio proyecto.
PIPER_LOCAL = (
    CARPETA_VOCES / "piper" / ("piper.exe" if sys.platform == "win32" else "piper")
)

# La voz elegida tras escuchar las cinco masculinas de OpenAI —ash, ballad,
# echo, verse y onyx— y las cuatro de Piper en español.
VOZ_OPENAI = "onyx"

# `gpt-4o-mini-tts` acepta instrucciones de interpretación, y ahí está la
# diferencia: sin ellas la voz suena neutra de informativo. Piper no tiene
# ninguna voz masculina latina salvo dos mexicanas, así que pedir el acento
# es lo más cerca que se llega sin pagar otro servicio.
ACENTO = (
    "Habla en español latinoamericano neutro, con acento colombiano suave. "
    "Tono cálido, cercano y seguro, como un compañero de trabajo. "
    "Ritmo natural, sin sonar a locutor."
)

# El PCM que devuelve OpenAI: 24 kHz, 16 bits, mono.
HERCIOS_OPENAI = 24000


def motores() -> dict[str, Any]:
    """Qué hay disponible en esta máquina, y qué falta.

    Se consulta antes de hablar, y también desde ``architect voz`` para que
    se pueda ver sin ejecutar nada.
    """
    piper = _piper_disponible()

    return {
        "piper": {
            "disponible": bool(piper),
            "voz": piper.name if piper else None,
            "nota": (
                "local, gratis, voz masculina latina"
                if piper
                else f"no instalado. Baja una voz a {CARPETA_VOCES}"
            ),
        },
        "openai": {
            "disponible": bool(os.getenv("OPENAI_API_KEY")),
            "voz": VOZ_OPENAI,
            "nota": "de pago por uso; se le pide acento latinoamericano",
        },
        "windows": {
            "disponible": _windows_disponible(),
            "voz": _voz_windows(),
            "nota": _nota_windows(),
        },
    }


def elegir(preferido: str = "") -> str:
    """El motor que se va a usar. Vacío si no hay ninguno.

    El orden no es caprichoso: primero el que da la voz que se pidió y no
    cuesta dinero, luego el que cuesta, y de último el que suena distinto a
    lo que se quería.
    """
    disponibles = motores()

    if preferido and disponibles.get(preferido, {}).get("disponible"):
        return preferido

    # Lo que eligió el usuario manda sobre el orden por defecto: escuchó las
    # dos y se quedó con una, y eso no lo cambia que mañana aparezca otra.
    from ai_architect.core.perfil import voz_preferida

    suya = voz_preferida()

    if suya and disponibles.get(suya, {}).get("disponible"):
        return suya

    for nombre in ("piper", "openai", "windows"):
        if disponibles[nombre]["disponible"]:
            return nombre

    return ""


def hablar(texto: str, motor: str = "") -> dict[str, Any]:
    """Dice el texto en voz alta. Nunca lanza.

    Que no haya voz no puede impedir que el comando funcione: la respuesta ya
    está escrita en la pantalla.
    """
    limpio = _para_decir(texto)

    if not limpio:
        return {"hablado": False, "motor": "", "motivo": "no había nada que decir"}

    elegido = elegir(motor)

    if not elegido:
        return {
            "hablado": False,
            "motor": "",
            "motivo": (
                "no hay ninguna voz disponible. "
                "Instala Piper, configura OPENAI_API_KEY, "
                "o instala una voz de Windows"
            ),
        }

    try:
        {"piper": _con_piper, "openai": _con_openai, "windows": _con_windows}[elegido](
            limpio
        )

    except Exception as e:  # noqa: BLE001 - sin voz se sigue trabajando
        return {"hablado": False, "motor": elegido, "motivo": str(e)}

    return {"hablado": True, "motor": elegido, "motivo": ""}


def _para_decir(texto: str) -> str:
    """El texto, sin lo que no se dice en voz alta.

    Una respuesta lleva rutas, comandos y símbolos que leídos suenan a ruido.
    """
    lineas = [
        linea
        for linea in str(texto).splitlines()
        if linea.strip() and not linea.strip().startswith(("architect ", "$", "#"))
    ]

    return " ".join(lineas).replace("`", "").replace("*", "").strip()


# --- Piper ------------------------------------------------------------------


def _binario_piper() -> str | None:
    """El ejecutable de Piper, esté en el PATH o instalado con el proyecto."""
    if PIPER_LOCAL.is_file():
        return str(PIPER_LOCAL)

    return shutil.which("piper")


def _piper_disponible() -> Path | None:
    """La voz de Piper que se va a usar, si hay alguna.

    Se respeta la que el usuario haya elegido en su perfil; si no eligió,
    la primera de la lista que esté descargada.
    """
    if _binario_piper() is None:
        return None

    from ai_architect.core.perfil import cargar

    suya = str(cargar().get("voz_piper") or "")

    orden = (suya, *VOCES_PIPER) if suya else VOCES_PIPER

    for nombre in orden:
        voz = CARPETA_VOCES / nombre

        if voz.is_file():
            return voz

    return None


def _con_piper(texto: str) -> None:
    _reproducir(_wav_piper(texto))


def _wav_piper(texto: str) -> Path:
    voz = _piper_disponible()

    if voz is None:
        raise RuntimeError("Piper no está disponible")

    salida = Path(tempfile.gettempdir()) / "arquitecto.wav"

    binario = _binario_piper()

    if binario is None:
        raise RuntimeError("no encontré el ejecutable de Piper")

    subprocess.run(
        [binario, "--model", str(voz), "--output_file", str(salida)],
        input=texto,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
        timeout=TIEMPO_LIMITE,
    )

    return salida


# --- OpenAI -----------------------------------------------------------------


def _con_openai(texto: str) -> None:
    _reproducir(_wav_openai(texto))


def _wav_openai(texto: str) -> Path:
    """Pide el audio crudo y le pone la cabecera aquí.

    Pidiendo ``wav`` la respuesta llega en streaming con el tamaño sin
    rellenar: la cabecera decía que duraba **89.478 segundos** —24 días— y
    `winsound` sencillamente no sonaba. Con ``pcm`` vienen las muestras a
    secas y la cabecera la escribimos nosotros, que sí sale bien.
    """
    from openai import OpenAI

    salida = Path(tempfile.gettempdir()) / "arquitecto.wav"

    respuesta = OpenAI().audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=VOZ_OPENAI,
        input=texto,
        instructions=ACENTO,
        response_format="pcm",
    )

    _escribir_wav(salida, respuesta.read())

    return salida


# --- Para el avatar ---------------------------------------------------------
#
# La cara mueve la boca mientras suena la voz, y para eso hay que saber
# **cuánto** va a sonar antes de empezar. Estimarlo por el número de
# palabras se nota: la boca sigue abriéndose medio segundo después del
# silencio. Con el WAV delante la duración es exacta.


PALABRAS_POR_SEGUNDO = 2.6


def preparar(texto: str, motor: str = "") -> dict[str, Any]:
    """Deja el audio listo y dice cuánto dura, sin reproducirlo todavía."""
    limpio = _para_decir(texto)

    if not limpio:
        return {"archivo": None, "motor": "", "segundos": 0.0, "motivo": "nada"}

    elegido = elegir(motor)

    if not elegido:
        return {"archivo": None, "motor": "", "segundos": 0.0, "motivo": "sin voz"}

    # Las voces de Windows hablan por SAPI directamente: no dejan archivo,
    # así que ahí la duración sí hay que estimarla.
    if elegido == "windows":
        return {
            "archivo": None,
            "motor": elegido,
            "segundos": _estimar(limpio),
            "motivo": "",
            "texto": limpio,
        }

    try:
        archivo = {"piper": _wav_piper, "openai": _wav_openai}[elegido](limpio)

    except Exception as e:  # noqa: BLE001 - sin voz se sigue trabajando
        return {"archivo": None, "motor": elegido, "segundos": 0.0, "motivo": str(e)}

    return {
        "archivo": archivo,
        "motor": elegido,
        "segundos": duracion(archivo),
        "motivo": "",
        "texto": limpio,
    }


def emitir(preparado: dict[str, Any]) -> bool:
    """Reproduce lo que dejó ``preparar``. Devuelve si sonó."""
    try:
        archivo = preparado.get("archivo")

        if archivo is not None:
            _reproducir(Path(archivo))

        elif preparado.get("motor") == "windows":
            _con_windows(str(preparado.get("texto", "")))

        else:
            return False

    except Exception:  # noqa: BLE001 - sin voz se sigue trabajando
        return False

    return True


def duracion(archivo: Path) -> float:
    """Los segundos que dura un WAV, leídos de su cabecera."""
    try:
        with wave.open(str(archivo), "rb") as leido:
            velocidad = leido.getframerate()

            return leido.getnframes() / velocidad if velocidad else 0.0

    # EOFError y no solo wave.Error: un WAV truncado —una llamada cortada
    # a mitad— revienta al leer la cabecera, y eso no puede tumbar la
    # respuesta entera cuando lo único que se perdía era mover la boca.
    except (OSError, wave.Error, EOFError):
        return 0.0


def _estimar(texto: str) -> float:
    return max(1.0, len(texto.split()) / PALABRAS_POR_SEGUNDO)


def _escribir_wav(destino: Path, crudo: bytes) -> None:
    """Envuelve las muestras en un WAV con la cabecera correcta.

    OpenAI devuelve PCM de 24 kHz, 16 bits, mono.
    """
    with wave.open(str(destino), "wb") as archivo:
        archivo.setnchannels(1)
        archivo.setsampwidth(2)
        archivo.setframerate(HERCIOS_OPENAI)
        archivo.writeframes(crudo)


# --- Windows ----------------------------------------------------------------


def _windows_disponible() -> bool:
    return os.name == "nt" and bool(shutil.which("powershell"))


def _voz_windows() -> str | None:
    """La voz en español que tenga instalada, si tiene alguna."""
    if not _windows_disponible():
        return None

    salida = _powershell(
        "Add-Type -AssemblyName System.Speech; "
        "(New-Object System.Speech.Synthesis.SpeechSynthesizer)"
        ".GetInstalledVoices() | ForEach-Object { "
        "$_.VoiceInfo.Name + '|' + $_.VoiceInfo.Culture + "
        "'|' + $_.VoiceInfo.Gender }"
    )

    for linea in (salida or "").splitlines():
        partes = linea.strip().split("|")

        if len(partes) == 3 and partes[1].lower().startswith("es"):
            return f"{partes[0]} ({partes[1]}, {partes[2]})"

    return None


def _nota_windows() -> str:
    """Qué se puede esperar de las voces que hay, dicho sin adornos."""
    voz = _voz_windows()

    if voz is None:
        return "sin voces en español instaladas"

    if "Male" in voz:
        return "gratis y ya instalada"

    return (
        f"solo hay voz femenina ({voz}). Para una masculina, instala Raúl "
        "o Pablo en Configuración > Hora e idioma > Voz"
    )


def _con_windows(texto: str) -> None:
    escapado = texto.replace("'", "''")

    _powershell(
        "Add-Type -AssemblyName System.Speech; "
        "$v = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$es = $v.GetInstalledVoices() | Where-Object "
        "{ $_.VoiceInfo.Culture.Name -like 'es*' } | Select-Object -First 1; "
        "if ($es) { $v.SelectVoice($es.VoiceInfo.Name) }; "
        f"$v.Speak('{escapado}')"
    )


def _powershell(orden: str) -> str | None:
    try:
        resultado = subprocess.run(
            ["powershell", "-NoProfile", "-Command", orden],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=TIEMPO_LIMITE,
        )

    except (OSError, subprocess.SubprocessError):
        return None

    return resultado.stdout if resultado.returncode == 0 else None


def _reproducir(archivo: Path) -> None:
    """Suena el archivo. En Windows sin abrir ninguna ventana."""
    # `sys.platform` y no `os.name`: mypy entiende el primero como guarda de
    # plataforma, y en Linux `winsound` no existe.
    if sys.platform == "win32":
        import winsound

        winsound.PlaySound(str(archivo), winsound.SND_FILENAME)

        return

    for reproductor in ("aplay", "afplay", "paplay"):
        if shutil.which(reproductor):
            subprocess.run(
                [reproductor, str(archivo)],
                capture_output=True,
                check=False,
                timeout=TIEMPO_LIMITE,
            )

            return

    raise RuntimeError("no encontré con qué reproducir el audio")
