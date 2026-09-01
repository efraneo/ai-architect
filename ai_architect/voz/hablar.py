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
import tempfile
from pathlib import Path
from typing import Any

TIEMPO_LIMITE = 60

# Dónde se buscan las voces de Piper, si están.
CARPETA_VOCES = Path.home() / ".ai_architect" / "voces"

# Voces masculinas de español latino que Piper publica. La primera que
# aparezca es la que se usa.
VOCES_PIPER = (
    "es_MX-ald-medium.onnx",
    "es_AR-daniel-high.onnx",
    "es_MX-claude-high.onnx",
)

# Las voces de OpenAI que suenan masculinas. No están etiquetadas por acento:
# suenan neutras, no latinas, y conviene decirlo.
VOZ_OPENAI = "onyx"


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
            "nota": "de pago por uso; suena neutro, no latino",
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


def _piper_disponible() -> Path | None:
    """La voz de Piper que se va a usar, si hay alguna."""
    if not shutil.which("piper"):
        return None

    for nombre in VOCES_PIPER:
        voz = CARPETA_VOCES / nombre

        if voz.is_file():
            return voz

    return None


def _con_piper(texto: str) -> None:
    voz = _piper_disponible()

    if voz is None:
        raise RuntimeError("Piper no está disponible")

    salida = Path(tempfile.gettempdir()) / "arquitecto.wav"

    subprocess.run(
        ["piper", "--model", str(voz), "--output_file", str(salida)],
        input=texto,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
        timeout=TIEMPO_LIMITE,
    )

    _reproducir(salida)


# --- OpenAI -----------------------------------------------------------------


def _con_openai(texto: str) -> None:
    from openai import OpenAI

    salida = Path(tempfile.gettempdir()) / "arquitecto.wav"

    respuesta = OpenAI().audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=VOZ_OPENAI,
        input=texto,
        response_format="wav",
    )

    salida.write_bytes(respuesta.read())

    _reproducir(salida)


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
    if os.name == "nt":
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
