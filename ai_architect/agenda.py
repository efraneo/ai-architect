"""La agenda: recordatorios por voz y el contexto del día.

El agente de contexto y agenda de un asistente personal: sabe qué hora es,
en qué parte del día estás, qué te queda pendiente y te lo recuerda solo
cuando toca (el latido de ``proactivo`` mira los vencidos cada minuto).

    tú   Recuérdame llamar a Juan a las tres.
    él   Apuntado: llamar a Juan, hoy a las 15:00.
    ...  (a las 15:00, sin que le pregunten)
    él   Efraín, te recuerdo: llamar a Juan.

Se guarda en ``agenda.json`` en la carpeta de Architect, en hora local.
Las tareas repetidas («revisa el proyecto cada noche») siguen en
``commands/tareas``: aquello son órdenes que se da a sí mismo; esto son
avisos para ti.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from ai_architect.core.texto import sin_adornos

ARCHIVO = "agenda.json"

PIDE = re.compile(
    r"^(?:recuerdame|recuerda me|avisame|avisa me|recuerda|ponme un recordatorio|"
    r"pon un recordatorio|agenda|agendame|anota en la agenda|apunta en la agenda)\b"
    r"\s*(?:que|de|para)?\s*(?P<que>.+)$"
)

QUE_TENGO = (
    "que tengo hoy",
    "que tengo pendiente",
    "que tengo para hoy",
    "que tengo manana",
    "que tengo para manana",
    "que hay en la agenda",
    "que hay en mi agenda",
    "mi agenda",
    "mis recordatorios",
    "que recordatorios tengo",
    "que me toca hoy",
    "que me toca",
)

CANCELAR = (
    "cancela los recordatorios",
    "borra los recordatorios",
    "olvida los recordatorios",
    "cancela la agenda",
    "limpia la agenda",
    "borra la agenda",
)

NUMEROS = {
    "un": 1,
    "una": 1,
    "uno": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
    "once": 11,
    "doce": 12,
    "quince": 15,
    "veinte": 20,
    "treinta": 30,
    "cuarenta": 40,
    "cuarenta y cinco": 45,
    "cincuenta": 50,
    "media": 30,
}

EN = re.compile(
    r"\b(?:en|dentro de)\s+(?P<n>\d+|" + "|".join(NUMEROS) + r")\s*"
    r"(?P<u>minutos?|min|horas?|h|dias?|segundos?)\b"
)

A_LAS = re.compile(
    r"\b(?:a las?|a la)\s+(?P<h>\d{1,2}|" + "|".join(NUMEROS) + r")"
    r"(?:\s*[:.]\s*(?P<m>\d{2})|\s+y\s+(?P<frac>media|cuarto)|\s+y\s+(?P<mm>\d{1,2}))?"
    r"(?:\s+(?:de la|de|por la)\s+(?P<parte>manana|tarde|noche|madrugada))?"
)

DIA = re.compile(r"\b(?P<dia>manana|pasado manana|hoy|esta tarde|esta noche)\b")


def ruta() -> Path:
    from ai_architect.agente.rutas_agente import get_config_dir

    return Path(get_config_dir()) / ARCHIVO


def _cargar() -> list[dict[str, Any]]:
    try:
        datos = json.loads(ruta().read_text(encoding="utf-8"))

    except (OSError, ValueError):
        return []

    return [d for d in datos if isinstance(d, dict)] if isinstance(datos, list) else []


def _guardar(lista: list[dict[str, Any]]) -> None:
    try:
        ruta().parent.mkdir(parents=True, exist_ok=True)
        ruta().write_text(
            json.dumps(lista, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    except OSError:
        pass


# --- entender la frase ------------------------------------------------------------


def _numero(texto: str) -> int:
    texto = texto.strip()

    return int(texto) if texto.isdigit() else NUMEROS.get(texto, 0)


def cuando(frase: str, ahora: datetime | None = None) -> tuple[datetime | None, str]:
    """El momento que dice la frase y la frase sin esa parte."""
    ahora = ahora or datetime.now()
    limpia = sin_adornos(frase)
    resto = limpia

    m = EN.search(limpia)

    if m:
        n = _numero(m.group("n"))
        unidad = m.group("u")
        salto = (
            timedelta(seconds=n)
            if unidad.startswith("seg")
            else (
                timedelta(minutes=n)
                if unidad.startswith("min")
                else (
                    timedelta(days=n)
                    if unidad.startswith("dia")
                    else timedelta(hours=n)
                )
            )
        )
        resto = (limpia[: m.start()] + " " + limpia[m.end() :]).strip()

        return ahora + salto, con_mayusculas(_sin_muletas(resto), frase)

    dia = ahora.date()
    parte_del_dia = ""
    d = DIA.search(limpia)

    if d:
        palabra = d.group("dia")

        if palabra == "manana":
            dia = dia + timedelta(days=1)

        elif palabra == "pasado manana":
            dia = dia + timedelta(days=2)

        elif palabra in ("esta tarde", "esta noche"):
            parte_del_dia = palabra.split()[1]

        resto = (limpia[: d.start()] + " " + limpia[d.end() :]).strip()

    h = A_LAS.search(resto)

    if h is None:
        if parte_del_dia:
            hora = 15 if parte_del_dia == "tarde" else 20
            momento = datetime.combine(dia, datetime.min.time()).replace(hour=hora)

            return momento, con_mayusculas(_sin_muletas(resto), frase)

        if d and not parte_del_dia:
            momento = datetime.combine(dia, datetime.min.time()).replace(hour=9)

            return momento, con_mayusculas(_sin_muletas(resto), frase)

        return None, con_mayusculas(_sin_muletas(resto), frase)

    hora = _numero(h.group("h"))
    minutos = int(h.group("m") or h.group("mm") or 0)

    if h.group("frac") == "media":
        minutos = 30

    elif h.group("frac") == "cuarto":
        minutos = 15

    parte = h.group("parte") or parte_del_dia

    if parte in ("tarde", "noche") and hora < 12:
        hora += 12

    elif not parte and hora < 12 and not d:
        # «a las tres» dicho a las cinco de la tarde es a las tres de la
        # mañana solo si nadie piensa; se asume la próxima vez que sean las tres.
        candidata = ahora.replace(hour=hora, minute=minutos, second=0, microsecond=0)

        if candidata <= ahora and hora + 12 < 24:
            hora += 12

    if hora > 23:
        hora = 23

    momento = datetime.combine(dia, datetime.min.time()).replace(
        hour=hora, minute=minutos
    )

    if momento <= ahora and not d:
        momento += timedelta(days=1)

    resto = (resto[: h.start()] + " " + resto[h.end() :]).strip()

    return momento, con_mayusculas(_sin_muletas(resto), frase)


def con_mayusculas(texto: str, original: str) -> str:
    """El texto limpio, con las palabras tal como se dijeron («Juan», no «juan»)."""
    por_clave: dict[str, str] = {}

    for palabra in original.split():
        clave = sin_adornos(palabra)

        if clave:
            por_clave.setdefault(clave, palabra.strip(" ,.;:¿?¡!"))

    return " ".join(por_clave.get(w, w) for w in texto.split())


def _sin_muletas(texto: str) -> str:
    texto = re.sub(r"\s+", " ", texto).strip(" ,.;:")
    texto = re.sub(r"^(?:que|de|para|que tengo que|tengo que|debo)\s+", "", texto)

    return texto.strip(" ,.;:")


# --- la agenda --------------------------------------------------------------------------


def recordar(texto: str, momento: datetime) -> dict[str, Any]:
    lista = _cargar()
    aviso = {
        "id": uuid.uuid4().hex[:8],
        "texto": texto,
        "cuando": momento.replace(second=0, microsecond=0).isoformat(),
        "estado": "pendiente",
        "creado": datetime.now().isoformat(timespec="seconds"),
    }
    lista.append(aviso)
    _guardar(lista)

    return aviso


def pendientes(dia: date | None = None) -> list[dict[str, Any]]:
    salida = [a for a in _cargar() if a.get("estado") == "pendiente"]

    if dia is not None:
        salida = [
            a for a in salida if str(a.get("cuando", "")).startswith(dia.isoformat())
        ]

    return sorted(salida, key=lambda a: str(a.get("cuando", "")))


def vencidos(ahora: datetime | None = None) -> list[dict[str, Any]]:
    """Los avisos cuya hora llegó. Se marcan como avisados: se dicen una vez."""
    ahora = ahora or datetime.now()
    lista = _cargar()
    tocan = []

    for a in lista:
        if a.get("estado") != "pendiente":
            continue

        try:
            momento = datetime.fromisoformat(str(a.get("cuando")))

        except ValueError:
            a["estado"] = "roto"

            continue

        if momento <= ahora:
            a["estado"] = "avisado"
            a["avisado"] = ahora.isoformat(timespec="seconds")
            tocan.append(a)

    if tocan:
        _guardar(lista)

    return tocan


def cancelar_todos() -> int:
    lista = _cargar()
    n = 0

    for a in lista:
        if a.get("estado") == "pendiente":
            a["estado"] = "cancelado"
            n += 1

    _guardar(lista)

    return n


# --- decirlo ----------------------------------------------------------------------------


def _hora_dicha(momento: datetime, ahora: datetime) -> str:
    hora = momento.strftime("%H:%M")

    if momento.date() == ahora.date():
        return f"hoy a las {hora}"

    if momento.date() == ahora.date() + timedelta(days=1):
        return f"mañana a las {hora}"

    return f"el {momento.day} de {MESES[momento.month - 1]} a las {hora}"


MESES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def que_tengo(dia: date | None = None, ahora: datetime | None = None) -> str:
    ahora = ahora or datetime.now()
    lista = pendientes(dia)

    if not lista:
        return (
            "No tienes nada en la agenda"
            + (" para hoy" if dia == ahora.date() else " para mañana" if dia else "")
            + "."
        )

    partes = []

    for a in lista[:8]:
        try:
            momento = datetime.fromisoformat(str(a["cuando"]))
            partes.append(f"{a['texto']} ({_hora_dicha(momento, ahora)})")

        except (KeyError, ValueError):
            continue

    return f"Tienes {len(lista)} recordatorio(s): " + "; ".join(partes) + "."


def momento_del_dia(ahora: datetime | None = None) -> str:
    hora = (ahora or datetime.now()).hour

    if hora < 6:
        return "madrugada"

    if hora < 12:
        return "mañana"

    if hora < 19:
        return "tarde"

    return "noche"


def contexto(ahora: datetime | None = None) -> str:
    """Una línea para el guion del modelo: hora, parte del día y lo pendiente."""
    ahora = ahora or datetime.now()
    hoy = pendientes(ahora.date())
    texto = f"Son las {ahora:%H:%M} ({momento_del_dia(ahora)})."

    if hoy:
        texto += " Pendiente hoy: " + "; ".join(
            f"{a['texto']} a las {str(a['cuando'])[11:16]}" for a in hoy[:5]
        )

    return texto


def por_voz(frase: str, ahora: datetime | None = None) -> dict[str, Any] | None:
    """«Recuérdame…», «qué tengo hoy», «cancela los recordatorios». ``None`` si no iba de eso."""
    ahora = ahora or datetime.now()
    limpia = sin_adornos(frase)

    if not limpia:
        return None

    if limpia in CANCELAR or any(limpia.startswith(c) for c in CANCELAR):
        n = cancelar_todos()

        return {
            "respuesta": (
                f"Listo, cancelé {n} recordatorio(s)."
                if n
                else "No había recordatorios."
            )
        }

    if limpia in QUE_TENGO or any(limpia.startswith(q) for q in QUE_TENGO):
        dia: date | None = (
            ahora.date() + timedelta(days=1) if "manana" in limpia else ahora.date()
        )

        if "pendiente" in limpia or limpia in (
            "mi agenda",
            "mis recordatorios",
            "que me toca",
        ):
            dia = None

        return {"respuesta": que_tengo(dia, ahora), "agenda": pendientes(dia)}

    m = PIDE.match(limpia)

    if m is None:
        return None

    # «Recuerda que…» es memoria de hechos, no agenda.
    if limpia.startswith(("recuerda que", "recuerdame que")) and not any(
        p.search(limpia) for p in (EN, A_LAS, DIA)
    ):
        return None

    momento, texto = cuando(m.group("que"), ahora)
    texto = con_mayusculas(texto, frase)

    if momento is None:
        return {
            "respuesta": "¿A qué hora te lo recuerdo? Dime «en veinte minutos» o «a las tres».",
            "pedir_hora": texto,
        }

    if not texto:
        return {"respuesta": "¿Qué te recuerdo? Dime qué y cuándo."}

    aviso = recordar(texto, momento)

    return {
        "respuesta": f"Apuntado: {texto}, {_hora_dicha(momento, ahora)}.",
        "agenda": [aviso],
    }
