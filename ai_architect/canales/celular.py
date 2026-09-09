"""El celular como algo que se manda: llamar, colgar, bloquear, poner música.

Architect no está en el teléfono; lo que hace es **mandarle una orden** por el
mismo bot de Telegram, con una forma fija que una automatización del teléfono
sabe leer (Tasker o Automate en Android; ver ``docs/CELULAR.md``):

    📱 LLAMAR|3001234567
    📱 MUSICA|Bad Bunny Tití me preguntó
    📱 BLOQUEAR|

El teléfono intercepta la notificación, separa por «|» y ejecuta. Lo que no
se puede: **desbloquear**. Ni Android ni iPhone dejan que un programa quite el
bloqueo —tampoco Siri sin tu cara o tu huella—, y está bien que sea así.

Los contactos viven en ``~/.ai_architect/contactos.json`` («recuerda que el
número de Juan es …» los va guardando); si no se conoce el número, se manda
el nombre y el teléfono busca en su agenda.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from ai_architect.agente.rutas_agente import get_config_dir
from ai_architect.canales import telegram
from ai_architect.core.texto import sin_adornos

MARCA = "\U0001f4f1"  # 📱

# Las órdenes que entiende el teléfono. Las que llevan «!» piden permiso.
ACCIONES = {
    "llamar": "llama a un contacto o número",
    "colgar": "cuelga la llamada en curso",
    "bloquear": "bloquea la pantalla",
    "musica": "pone una canción o un artista",
    "pausar": "pausa la música",
    "reanudar": "sigue la música",
    "siguiente": "siguiente canción",
    "anterior": "canción anterior",
    "volumen": "sube o baja el volumen (0-100)",
    "abrir": "abre una aplicación",
    "navegar": "abre una dirección web",
    "sonar": "hace sonar el teléfono para encontrarlo",
    "mensaje": "manda un SMS: número|texto",
}

CON_PERMISO = frozenset({"llamar", "mensaje"})


def ruta_contactos() -> Path:
    return get_config_dir() / "contactos.json"


def contactos() -> dict[str, str]:
    ruta = ruta_contactos()

    try:
        return (
            dict(json.loads(ruta.read_text(encoding="utf-8"))) if ruta.is_file() else {}
        )

    except ValueError:
        return {}


def guardar_contacto(nombre: str, numero: str) -> bool:
    limpio_nombre = sin_adornos(nombre)
    limpio_numero = re.sub(r"[^\d+]", "", numero)

    if not limpio_nombre or len(limpio_numero) < 6:
        return False

    agenda = contactos()
    agenda[limpio_nombre] = limpio_numero

    try:
        ruta_contactos().write_text(
            json.dumps(agenda, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    except OSError:
        return False

    return True


def numero_de(quien: str) -> str:
    """El número de un contacto conocido, o lo dicho tal cual (nombre o número)."""
    plano = sin_adornos(quien)

    if re.fullmatch(r"\+?\d[\d ]{5,}", quien.strip()):
        return re.sub(r"\s", "", quien.strip())

    agenda = contactos()

    if plano in agenda:
        return agenda[plano]

    for nombre, numero in agenda.items():
        if plano and (plano in nombre or nombre in plano):
            return numero

    return quien.strip()


def formar(accion: str, argumento: str = "") -> str:
    """El texto exacto que se manda al teléfono."""
    return f"{MARCA} {accion.upper()}|{argumento.strip()}"


def ordenar(accion: str, argumento: str = "") -> dict[str, Any]:
    """Manda la orden al teléfono por Telegram. Nunca lanza."""
    accion = accion.lower().strip()

    if accion not in ACCIONES:
        return {"ok": False, "error": f"no sé hacer «{accion}» en el celular"}

    if accion == "llamar":
        argumento = numero_de(argumento)

        if not argumento:
            return {"ok": False, "error": "¿a quién llamo?"}

    if not telegram.configurado():
        return {
            "ok": False,
            "error": "el celular va por Telegram y no está configurado (architect canales)",
        }

    salida = telegram.enviar(formar(accion, argumento))

    if not salida.get("ok"):
        return {"ok": False, "error": str(salida.get("description", "no se envió"))}

    return {
        "ok": True,
        "accion": accion,
        "argumento": argumento,
        "texto": formar(accion, argumento),
    }


# --- Entender la frase --------------------------------------------------------
#
# Se busca sobre una copia «plana» (sin tildes, sin signos, en minúsculas) que
# conserva la longitud, y el argumento se recorta del texto original: así
# «pon la canción Tití me preguntó» manda «Tití me preguntó», no «titi me pregunto».

CELULAR_AL_FINAL = r"(?:\s+(?:en|del|de)\s+(?:el|mi)\s+(?:celular|telefono|movil))?"

LLAMAR = re.compile(
    r"^(?:llama|llamar|llamale|llamalo|llamala|marca|marcale|marcar)(?:\s+(?:a|al|a la))?\s+"
    r"(?P<a>.+?)" + CELULAR_AL_FINAL + r"$"
)
MUSICA = re.compile(
    r"^(?:pon|pone|ponme|reproduce|reproducir|escuchar|quiero escuchar|toca)\s+"
    r"(?:la cancion|una cancion|cancion|musica|algo)?\s*(?:de\s+)?(?P<que>.+?)"
    + CELULAR_AL_FINAL
    + r"$"
)
VOLUMEN = re.compile(
    r"^(?:volumen|pon el volumen|sube el volumen|baja el volumen)(?:\s+(?:a|al))?\s*(?P<n>\d{1,3})"
    + CELULAR_AL_FINAL
    + r"$"
)
ABRIR = re.compile(
    r"^(?:abre|abrir|abreme|lanza)\s+(?:la app\s+|la aplicacion\s+)?(?P<app>.+?)"
    r"\s+(?:en|del)\s+(?:el|mi)\s+(?:celular|telefono|movil)$"
)
NAVEGAR = re.compile(
    r"^(?:navega a|ve a|entra a|abre la pagina)\s+(?P<url>\S+)"
    + CELULAR_AL_FINAL
    + r"$"
)

EN_EL_CELULAR = (
    "en el celular",
    "en el telefono",
    "en el movil",
    "en mi celular",
    "en mi telefono",
    "del celular",
    "el celular",
    "mi celular",
    "el telefono",
    "mi telefono",
)

COLGAR = (
    "cuelga",
    "cuelga la llamada",
    "corta la llamada",
    "termina la llamada",
    "colgar",
)
BLOQUEAR = (
    "bloquea el celular",
    "bloquea el telefono",
    "bloquea la pantalla",
    "bloquea mi celular",
    "bloquear celular",
    "bloquea",
)
PAUSAR = (
    "pausa la musica",
    "pausa",
    "para la musica",
    "deten la musica",
    "silencio musica",
)
REANUDAR = ("reanuda la musica", "sigue la musica", "continua la musica", "reanudar")
SIGUIENTE = (
    "siguiente cancion",
    "siguiente",
    "la siguiente",
    "cambia la cancion",
    "otra cancion",
    "salta la cancion",
)
ANTERIOR = ("cancion anterior", "la anterior", "anterior")
SONAR = (
    "donde esta mi celular",
    "haz sonar mi celular",
    "haz sonar el celular",
    "suena el celular",
    "encuentra mi celular",
)
DESBLOQUEAR = ("desbloquea", "desbloquear", "quita el bloqueo")


def _plano_con_longitud(texto: str) -> tuple[str, str]:
    """``(original, plano)`` con la misma longitud: tildes fuera, signos a espacio,
    minúsculas. Los índices de una coincidencia en ``plano`` valen en ``original``."""
    original = unicodedata.normalize("NFC", texto)
    letras = []

    for c in original:
        base = unicodedata.normalize("NFKD", c)[:1] or " "
        letras.append(base.lower() if base.isalnum() or base == "+" else " ")

    return original, "".join(letras)


def _recortar(original: str, plano: str, m: re.Match[str], grupo: str) -> str:
    inicio, fin = m.start(grupo), m.end(grupo)

    # Los espacios sobrantes del plano se recortan por los dos lados.
    while inicio < fin and plano[inicio] == " ":
        inicio += 1

    while fin > inicio and plano[fin - 1] == " ":
        fin -= 1

    return original[inicio:fin].strip()


def entender(frase: str) -> tuple[str, str] | None:
    """``(accion, argumento)`` si la frase es una orden para el celular; si no, ``None``."""
    original, plano = _plano_con_longitud(frase or "")
    limpia = " ".join(plano.split())

    if not limpia:
        return None

    if any(limpia.startswith(d) for d in DESBLOQUEAR):
        return ("desbloquear", "")

    sin_celular = limpia

    for coletilla in EN_EL_CELULAR:
        sin_celular = re.sub(
            rf"\s*\b{re.escape(coletilla)}\b\s*", " ", sin_celular
        ).strip()

    if limpia in COLGAR or sin_celular in COLGAR:
        return ("colgar", "")

    if (
        limpia in BLOQUEAR
        or sin_celular in BLOQUEAR
        or (
            limpia.startswith("bloquea")
            and any(p in limpia for p in ("celular", "telefono", "pantalla", "movil"))
        )
    ):
        return ("bloquear", "")

    if limpia in PAUSAR or sin_celular in PAUSAR:
        return ("pausar", "")

    if limpia in REANUDAR or sin_celular in REANUDAR:
        return ("reanudar", "")

    if limpia in SIGUIENTE or sin_celular in SIGUIENTE:
        return ("siguiente", "")

    if limpia in ANTERIOR or sin_celular in ANTERIOR:
        return ("anterior", "")

    if limpia in SONAR:
        return ("sonar", "")

    # Con captura: se busca en el plano (misma longitud) y se recorta del original.
    compacto = plano.strip()
    desplazamiento = len(plano) - len(plano.lstrip())
    original_c = original[desplazamiento : desplazamiento + len(compacto)]

    m = LLAMAR.match(compacto)

    if m:
        return ("llamar", _recortar(original_c, compacto, m, "a"))

    m = VOLUMEN.match(compacto)

    if m:
        return ("volumen", m["n"])

    m = NAVEGAR.match(compacto)

    if m:
        return ("navegar", _recortar(original_c, compacto, m, "url"))

    if any(p in limpia for p in ("cancion", "musica", "reproduce", "escuchar")):
        m = MUSICA.match(compacto)

        if m:
            return ("musica", _recortar(original_c, compacto, m, "que"))

    # «Abre X» solo es del celular si lo dice; en el PC «abre» es otra cosa.
    m = ABRIR.match(compacto)

    if m:
        return ("abrir", _recortar(original_c, compacto, m, "app"))

    return None
