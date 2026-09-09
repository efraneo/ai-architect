"""El hogar: luces, enchufes, persianas y sensores por Home Assistant.

El agente de hogar e IoT. No habla con cada marca: habla con Home Assistant,
que ya habla con todas, por su API REST (``HOGAR_URL`` y ``HOGAR_TOKEN`` en
el ``.env`` de Architect). Sin eso, Architect pide los datos y los guarda.

    tú   Enciende la luz de la sala.
    él   Listo: luz de la sala encendida.
    tú   ¿Cómo está la puerta del garaje?
    él   La puerta del garaje está cerrada.
"""

from __future__ import annotations

import difflib
import json
import re
import urllib.request
from typing import Any

from ai_architect.core.texto import sin_adornos

TIEMPO = 8

ENCENDER = ("enciende", "prende", "activa", "abre", "sube")
APAGAR = ("apaga", "desactiva", "cierra", "baja")
ESTADO = re.compile(
    r"^(?:como esta|como estan|cual es el estado de|estado de|esta encendid[ao]|esta apagad[ao]|esta abiert[ao]|esta cerrad[ao])\s+(?P<que>.+?)\??$"
)
ACCION = re.compile(
    r"^(?P<verbo>"
    + "|".join(ENCENDER + APAGAR)
    + r")\s+(?:la |el |las |los )?(?P<que>.+?)\.?$"
)

ARTICULOS = ("la ", "el ", "las ", "los ", "de la ", "del ", "de ", "mi ", "mis ")

ACCIONES_POR_DOMINIO = {
    "cover": ("open_cover", "close_cover"),
    "lock": ("unlock", "lock"),
    "media_player": ("media_play", "media_stop"),
}

SENSIBLES = ("lock",)


def _valor(clave: str) -> str:
    from ai_architect import canales

    return canales.valor(clave)


def configurado() -> bool:
    return bool(_valor("HOGAR_URL") and _valor("HOGAR_TOKEN"))


def que_falta() -> list[str]:
    return [k for k in ("HOGAR_URL", "HOGAR_TOKEN") if not _valor(k)]


# --- la API ----------------------------------------------------------------------------


def _pedir(ruta: str, cuerpo: dict[str, Any] | None = None) -> Any:
    url = _valor("HOGAR_URL").rstrip("/") + "/api/" + ruta.lstrip("/")
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
    peticion = urllib.request.Request(
        url,
        data=datos,
        method="POST" if cuerpo is not None else "GET",
        headers={
            "Authorization": f"Bearer {_valor('HOGAR_TOKEN')}",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(
        peticion, timeout=TIEMPO
    ) as r:  # noqa: S310 - URL del usuario
        texto = r.read().decode("utf-8", errors="replace")

    return json.loads(texto) if texto.strip() else None


def dispositivos() -> list[dict[str, Any]]:
    """Todo lo que Home Assistant conoce, con nombre, id y estado."""
    estados = _pedir("states")
    salida = []

    for e in estados if isinstance(estados, list) else []:
        if not isinstance(e, dict):
            continue

        id_ = str(e.get("entity_id", ""))
        dominio = id_.split(".", 1)[0]

        if dominio not in (
            "light",
            "switch",
            "cover",
            "lock",
            "fan",
            "climate",
            "media_player",
            "binary_sensor",
            "sensor",
        ):
            continue

        atributos = e.get("attributes") or {}
        salida.append(
            {
                "id": id_,
                "dominio": dominio,
                "nombre": str(atributos.get("friendly_name") or id_.split(".", 1)[-1]),
                "estado": str(e.get("state", "")),
                "unidad": str(atributos.get("unit_of_measurement", "")),
            }
        )

    return salida


def buscar(
    nombre: str, lista: list[dict[str, Any]] | None = None
) -> dict[str, Any] | None:
    """El dispositivo que más se parece a lo dicho («luz de la sala»)."""
    lista = dispositivos() if lista is None else lista
    limpio = sin_adornos(nombre)

    for a in ARTICULOS:
        if limpio.startswith(a):
            limpio = limpio[len(a) :]

    if not lista or not limpio:
        return None

    nombres = {sin_adornos(d["nombre"]): d for d in lista}
    ids = {d["id"].split(".", 1)[-1].replace("_", " "): d for d in lista}
    todos = {**ids, **nombres}

    if limpio in todos:
        return todos[limpio]

    contiene = [n for n in todos if limpio in n or n in limpio]

    if contiene:
        return todos[sorted(contiene, key=len)[0]]

    parecidos = difflib.get_close_matches(limpio, list(todos), n=1, cutoff=0.6)

    return todos[parecidos[0]] if parecidos else None


def accion(nombre: str, encender: bool) -> dict[str, Any]:
    if not configurado():
        return {"ok": False, "falta": que_falta()}

    try:
        d = buscar(nombre)

    except Exception as e:  # noqa: BLE001 - sin Home Assistant se dice
        return {"ok": False, "error": f"no llego a Home Assistant: {e}"}

    if d is None:
        return {"ok": False, "error": f"no encuentro «{nombre}» en la casa"}

    dominio = d["dominio"]
    servicio = ACCIONES_POR_DOMINIO.get(dominio, ("turn_on", "turn_off"))[
        0 if encender else 1
    ]

    try:
        _pedir(f"services/{dominio}/{servicio}", {"entity_id": d["id"]})

    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"Home Assistant no aceptó la orden: {e}"}

    return {"ok": True, "dispositivo": d["nombre"], "accion": servicio}


def estado(nombre: str) -> dict[str, Any]:
    if not configurado():
        return {"ok": False, "falta": que_falta()}

    try:
        d = buscar(nombre)

    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"no llego a Home Assistant: {e}"}

    if d is None:
        return {"ok": False, "error": f"no encuentro «{nombre}» en la casa"}

    return {"ok": True, **d}


# --- decirlo --------------------------------------------------------------------------------

ESTADOS = {
    "on": "encendido",
    "off": "apagado",
    "open": "abierto",
    "closed": "cerrado",
    "locked": "bloqueado",
    "unlocked": "desbloqueado",
    "unavailable": "sin conexión",
    "playing": "reproduciendo",
    "idle": "en espera",
}


def _en_palabras(d: dict[str, Any]) -> str:
    valor = ESTADOS.get(d.get("estado", ""), d.get("estado", ""))

    if d.get("unidad"):
        valor = f"{d['estado']} {d['unidad']}"

    return f"{d['nombre']} está {valor}."


def por_voz(frase: str) -> dict[str, Any] | None:
    """«Enciende la luz de la sala», «apaga el ventilador», «cómo está la puerta»."""
    limpia = sin_adornos(frase)

    if not limpia:
        return None

    if limpia in (
        "estado de la casa",
        "como esta la casa",
        "que hay en la casa",
        "dispositivos de la casa",
    ):
        if not configurado():
            return _pedir_configuracion()

        try:
            lista = dispositivos()

        except Exception as e:  # noqa: BLE001
            return {"respuesta": f"No llego a Home Assistant: {e}"}

        encendidos = [d["nombre"] for d in lista if d["estado"] == "on"]

        return {
            "respuesta": f"Conozco {len(lista)} dispositivo(s). Encendidos: "
            + (", ".join(encendidos[:8]) or "ninguno")
            + ".",
            "panel": {
                "tipo": "texto",
                "titulo": "La casa",
                "cuerpo": "\n".join(
                    f"{d['nombre']}: {d['estado']}" for d in lista[:40]
                ),
            },
        }

    m = ESTADO.match(limpia)

    if m:
        que = m.group("que")

        if not _suena_a_casa(que) and not (configurado() and _lo_conoce(que)):
            return None

        salida = estado(que)

        if salida.get("falta"):
            return _pedir_configuracion()

        return {
            "respuesta": (
                _en_palabras(salida) if salida.get("ok") else str(salida.get("error"))
            )
        }

    m = ACCION.match(limpia)

    if m is None:
        return None

    que = m.group("que")

    # «Abre Word» o «cierra Architect» no son de la casa: solo entra lo que
    # suene a dispositivo, o lo que Home Assistant conozca si está configurado.
    if not _suena_a_casa(que) and not (configurado() and _lo_conoce(que)):
        return None

    encender = m.group("verbo") in ENCENDER
    salida = accion(que, encender)

    if salida.get("falta"):
        return _pedir_configuracion()

    if not salida.get("ok"):
        return {"respuesta": str(salida.get("error"))}

    return {
        "respuesta": f"Listo: {salida['dispositivo']} "
        + ("encendido." if encender else "apagado.")
    }


COSAS_DE_CASA = (
    "luz",
    "luces",
    "lampara",
    "bombillo",
    "foco",
    "ventilador",
    "aire",
    "calefaccion",
    "persiana",
    "cortina",
    "enchufe",
    "toma",
    "televisor",
    "tele",
    "puerta",
    "porton",
    "garaje",
    "cerradura",
    "alarma",
    "camara de",
    "riego",
    "calentador",
    "cafetera",
    "nevera",
)


def _suena_a_casa(que: str) -> bool:
    return any(c in que for c in COSAS_DE_CASA)


def _lo_conoce(que: str) -> bool:
    try:
        return buscar(que) is not None

    except Exception:  # noqa: BLE001
        return False


def _pedir_configuracion() -> dict[str, Any]:
    from ai_architect.canales import asistente

    return asistente.empezar("hogar")
