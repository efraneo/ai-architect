"""
=========================================================
Tareas

Que trabaje solo, cuando se le diga.
=========================================================

``scheduler/`` llevaba meses escrito y sin conectar: tiene el modelo de una
tarea, sabe cuáles tocan y sabe calcular la siguiente. Le faltaban las dos
mitades que la hacen servir para algo — **no guardaba nada**, así que las
tareas morían con el proceso, y **nadie ejecutaba los callbacks**, que
además eran cadenas sin significado.

Esto le pone las dos, y con una idea que lo simplifica todo: **una tarea
programada es una orden que se da a sí mismo**. El `callback` deja de ser
un nombre suelto y pasa a ser la frase que se le diría en voz alta. Así
todo lo que ya sabe hacer —elegir comando, resolver la carpeta, pedir
permiso antes de escribir— vale igual a las tres de la mañana.

    tú   Revisa autosgsst cada noche.
    él   Programado: revisar autosgsst, cada noche a las diez.
    ...
    tú   Descansemos.
    él   Listo, las dejo en pausa. Tienes dos tareas dormidas.

**En hora local, no UTC.** El original usaba ``utcnow()``. Nadie dice "cada
noche" pensando en UTC: quien lo dice quiere que ocurra cuando en su casa
es de noche. Además ``utcnow()`` está en desuso desde Python 3.12.

**Dos formas de que se ejecuten.** Con la conversación abierta, un hilo las
mira cada minuto y te cuenta el resultado en voz alta. Con el programa
cerrado hace falta que alguien lo despierte, y de eso sabe Windows:
``architect tareas --correr`` es lo que se registra en el Programador de
tareas.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any

from ai_architect.core import perfil
from ai_architect.core.env_file import CARPETA_USUARIO
from ai_architect.core.texto import contiene, sin_adornos
from ai_architect.scheduler.models import JobStatus, ScheduledJob

ARCHIVO = CARPETA_USUARIO / "tareas.json"

DIA = 24 * 3600

# Cuándo es "de noche", "de mañana" y "de tarde" para alguien que lo dice
# hablando. No hay que acertar el minuto: hay que caer en el tramo.
HORAS = {
    "noche": 22,
    "madrugada": 3,
    "manana": 8,
    "mediodia": 13,
    "tarde": 17,
}

CADA = (
    "cada noche",
    "cada manana",
    "cada tarde",
    "cada dia",
    "todas las noches",
    "todos los dias",
    "cada hora",
    "cada madrugada",
    "cada mediodia",
)

DESCANSAR = (
    "descansemos",
    "descansa",
    "para las tareas",
    "pausa las tareas",
    "deja de trabajar",
    "duermete",
    "a dormir",
)

REANUDAR = (
    "reanuda",
    "sigue con las tareas",
    "vuelve al trabajo",
    "despierta",
    "reactiva las tareas",
)

LISTAR = (
    "que tienes programado",
    "que tareas tienes",
    "tus tareas",
    "las tareas",
    "que hay programado",
)

CANCELAR = (
    "cancela las tareas",
    "borra las tareas",
    "quita las tareas",
    "olvida las tareas",
)


# --- Lo que se dice hablando ------------------------------------------------


def por_voz(frase: str, project: str = ".") -> dict[str, Any] | None:
    """Interpreta una orden sobre tareas. ``None`` si no iba de eso.

    Se resuelve aquí y no con el modelo: son cuatro verbos y una hora, y
    mandarlo fuera son dos segundos de espera para programar algo que ya
    está dicho.
    """
    limpia = sin_adornos(frase)

    if not limpia:
        return None

    if contiene(limpia, *DESCANSAR):
        return _dormir()

    if contiene(limpia, *REANUDAR):
        return _despertar()

    if contiene(limpia, *CANCELAR):
        return _olvidar_todas()

    if contiene(limpia, *LISTAR):
        return {"success": True, "explanation": contar()}

    if contiene(limpia, *CADA):
        return programar(frase, project)

    return None


def programar(frase: str, project: str = ".") -> dict[str, Any]:
    """Guarda una tarea a partir de la frase, tal como se dijo."""
    cada, cuando = _cada_cuanto(frase)

    orden = _la_orden(frase)

    if not orden:
        return {
            "success": False,
            "explanation": "No entendí qué quieres que haga cada vez. Dímelo entero.",
        }

    tarea = ScheduledJob(
        id=datetime.now().strftime("%Y%m%d%H%M%S%f")[:18],
        name=orden,
        interval_seconds=cada,
        # El callback es la frase: una tarea programada es una orden que se
        # da a si mismo, y asi vale todo lo que ya sabe hacer.
        callback=json.dumps({"frase": orden, "project": project}),
        next_run=cuando,
    )

    guardar(cargar() + [tarea])

    return {
        "success": True,
        "task": tarea.id,
        "explanation": (
            f"Programado: {orden}, {_cuando_se_dice(cada, cuando)}. "
            "Dime «descansemos» cuando quieras que pare."
        ),
    }


def contar() -> str:
    """Lo que hay programado, dicho para oírlo."""
    tareas = cargar()

    if not tareas:
        return "No tengo nada programado."

    despiertas = [t for t in tareas if t.enabled]

    if not despiertas:
        return f"Tengo {_cuantas(len(tareas))} en pausa. Dime «reanuda» para seguir."

    trozos = [
        f"{t.name}, {_cuando_se_dice(t.interval_seconds, t.next_run)}"
        for t in despiertas[:4]
    ]

    return f"Tengo {_cuantas(len(despiertas))}: " + "; ".join(trozos) + "."


def _dormir() -> dict[str, Any]:
    tareas = cargar()

    for tarea in tareas:
        tarea.enabled = False

    guardar(tareas)

    if not tareas:
        return {"success": True, "explanation": "No tenía nada en marcha, pero vale."}

    return {
        "success": True,
        "explanation": (
            f"Listo, las dejo en pausa. {_cuantas(len(tareas)).capitalize()} dormidas. "
            "Dime «reanuda» cuando quieras."
        ),
    }


def _despertar() -> dict[str, Any]:
    tareas = cargar()

    ahora = datetime.now()

    for tarea in tareas:
        tarea.enabled = True

        # Si estuvo dormida más de un ciclo, no se ejecuta cinco veces
        # seguidas al despertar: se apunta a la próxima y ya.
        if tarea.next_run and tarea.next_run < ahora:
            tarea.next_run = _siguiente(tarea.interval_seconds, ahora)

    guardar(tareas)

    if not tareas:
        return {"success": True, "explanation": "No tengo tareas que reanudar."}

    return {
        "success": True,
        "explanation": f"Vuelvo al trabajo. {_cuantas(len(tareas)).capitalize()} activas.",
    }


def _olvidar_todas() -> dict[str, Any]:
    cuantas = len(cargar())

    guardar([])

    return {
        "success": True,
        "explanation": (
            f"Borradas {_cuantas(cuantas)}." if cuantas else "No había ninguna."
        ),
    }


# --- Ejecutarlas ------------------------------------------------------------


def pendientes(ahora: datetime | None = None) -> list[ScheduledJob]:
    """Las que ya tocan. Solo las despiertas."""
    momento = ahora or datetime.now()

    return [
        t
        for t in cargar()
        if t.enabled and t.next_run is not None and t.next_run <= momento
    ]


def correr(ahora: datetime | None = None) -> list[dict[str, Any]]:
    """Ejecuta las que tocan y reprograma la siguiente vuelta.

    Se reprograma **antes** de ejecutar. Si la tarea falla o tarda media
    hora, la próxima ya está puesta; con el orden al revés, un fallo deja
    la tarea colgada y no vuelve a correr nunca.
    """
    momento = ahora or datetime.now()

    hechas: list[dict[str, Any]] = []

    for tarea in pendientes(momento):
        _reprogramar(tarea.id, momento)

        hechas.append(_ejecutar_una(tarea))

    return hechas


def _ejecutar_una(tarea: ScheduledJob) -> dict[str, Any]:
    from ai_architect.commands import pide

    try:
        encargo = json.loads(tarea.callback)

    except (ValueError, TypeError):
        encargo = {"frase": tarea.name, "project": "."}

    try:
        salida = pide.run(
            str(encargo.get("project") or "."),
            frase=str(encargo.get("frase") or tarea.name),
        )

    except Exception as e:  # noqa: BLE001 - una tarea rota no tumba las demás
        _marcar(tarea.id, JobStatus.FAILED)

        return {"task": tarea.id, "name": tarea.name, "error": str(e)}

    _marcar(tarea.id, JobStatus.SUCCESS if salida.get("success") else JobStatus.FAILED)

    return {
        "task": tarea.id,
        "name": tarea.name,
        "success": bool(salida.get("success")),
        "explanation": str(salida.get("explanation") or salida.get("error") or ""),
    }


def run(
    correr_ahora: bool = False,
    project: str = ".",
    registrar: bool = False,
    desregistrar: bool = False,
) -> dict[str, Any]:
    """El comando: lista, ejecuta, o se registra en Windows."""
    from ai_architect.core import windows

    if registrar:
        return windows.registrar(project)

    if desregistrar:
        return windows.quitar()

    if not correr_ahora:
        # Si Windows no lo despierta, las tareas solo corren con la
        # conversacion abierta — y eso no es lo que se pidio al decir
        # "cada noche". Callarlo seria dejar creer que funciona.
        despierta = (
            ""
            if windows.esta_registrada()
            else (
                " Ojo: solo se ejecutan con la conversación abierta. "
                "Para que corran con el programa cerrado: "
                "architect tareas --registrar"
            )
        )

        return {
            "success": True,
            "tasks": [asdict(t) for t in cargar()],
            "windows": windows.esta_registrada(),
            "explanation": f"{perfil.encabezar()} {contar()}{despierta}",
        }

    hechas = correr()

    if not hechas:
        return {"success": True, "ran": 0, "explanation": "No tocaba ninguna."}

    return {
        "success": True,
        "ran": len(hechas),
        "results": hechas,
        "explanation": "\n\n".join(
            f"{h['name']}: {h.get('explanation') or h.get('error', '')}" for h in hechas
        ),
    }


# --- El libro ---------------------------------------------------------------


def cargar() -> list[ScheduledJob]:
    if not ARCHIVO.is_file():
        return []

    try:
        crudo = json.loads(ARCHIVO.read_text(encoding="utf-8"))

    except (OSError, ValueError):
        # Un libro ilegible no puede impedir hablar. Se pierden las tareas,
        # no la conversación — y se dice cuando se pregunte por ellas.
        return []

    tareas = []

    for fila in crudo if isinstance(crudo, list) else []:
        try:
            tareas.append(
                ScheduledJob(
                    id=str(fila["id"]),
                    name=str(fila["name"]),
                    interval_seconds=int(fila["interval_seconds"]),
                    callback=str(fila.get("callback") or ""),
                    enabled=bool(fila.get("enabled", True)),
                    last_run=_fecha(fila.get("last_run")),
                    next_run=_fecha(fila.get("next_run")),
                    status=JobStatus(fila.get("status") or JobStatus.PENDING),
                )
            )

        except (KeyError, TypeError, ValueError):
            # Una fila corrupta se salta; las demás siguen valiendo.
            continue

    return tareas


def guardar(tareas: list[ScheduledJob]) -> bool:
    try:
        ARCHIVO.parent.mkdir(parents=True, exist_ok=True)

        ARCHIVO.write_text(
            json.dumps(
                [
                    {
                        **asdict(t),
                        "last_run": t.last_run.isoformat() if t.last_run else None,
                        "next_run": t.next_run.isoformat() if t.next_run else None,
                        "status": str(t.status),
                    }
                    for t in tareas
                ],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    except OSError:
        return False

    return True


def _reprogramar(cual: str, desde: datetime) -> None:
    tareas = cargar()

    for tarea in tareas:
        if tarea.id == cual:
            tarea.last_run = desde
            tarea.next_run = _siguiente(tarea.interval_seconds, desde)

    guardar(tareas)


def _marcar(cual: str, estado: JobStatus) -> None:
    tareas = cargar()

    for tarea in tareas:
        if tarea.id == cual:
            tarea.status = estado

    guardar(tareas)


# --- Cuándo -----------------------------------------------------------------


def _cada_cuanto(frase: str) -> tuple[int, datetime]:
    """Cada cuánto, y cuándo toca la primera vez.

    En hora local: nadie dice "cada noche" pensando en UTC.
    """
    limpia = sin_adornos(frase)

    if "cada hora" in limpia:
        ahora = datetime.now()

        return (
            3600,
            (ahora + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0),
        )

    hora = _hora_dicha(limpia)

    for palabra, cual in HORAS.items():
        if palabra in limpia:
            hora = hora if hora is not None else cual

            break

    return (DIA, _proxima_vez(hora if hora is not None else HORAS["noche"]))


def _hora_dicha(limpia: str) -> int | None:
    """La hora concreta, si la dijo: "cada día a las 7"."""
    hallado = re.search(r"a las (\d{1,2})", limpia)

    if hallado is None:
        return None

    hora = int(hallado.group(1))

    if not 0 <= hora <= 23:
        return None

    # "a las 7" dicho de noche es a las 19, no a las 7 de la mañana. Se
    # respeta lo que dijo: si quería las siete de la mañana, lo dirá.
    if hora < 7 and "manana" not in limpia and "madrugada" not in limpia:
        hora += 12

    return hora


def _proxima_vez(hora: int) -> datetime:
    ahora = datetime.now()

    proxima = ahora.replace(hour=hora, minute=0, second=0, microsecond=0)

    return proxima if proxima > ahora else proxima + timedelta(days=1)


def _siguiente(cada: int, desde: datetime) -> datetime:
    return desde + timedelta(seconds=max(cada, 60))


def _la_orden(frase: str) -> str:
    """La frase sin la parte del "cada noche": queda lo que hay que hacer."""
    limpia = frase.strip()

    for marca in (
        "cada noche",
        "cada madrugada",
        "cada mañana",
        "cada manana",
        "cada tarde",
        "cada mediodía",
        "cada mediodia",
        "cada día",
        "cada dia",
        "cada hora",
        "todas las noches",
        "todos los días",
        "todos los dias",
    ):
        limpia = re.sub(marca, "", limpia, flags=re.IGNORECASE)

    # La hora y su franja van juntas al decirlas —"a las 7 de la mañana"— y
    # hay que quitarlas juntas: quitando solo la hora queda "revisa las
    # dependencias de la mañana", que es otra orden.
    limpia = re.sub(
        r"\ba las \d{1,2}\s*(de la (mañana|manana|tarde|noche|madrugada))?",
        "",
        limpia,
        flags=re.IGNORECASE,
    )

    return re.sub(r"\s+", " ", limpia).strip(" ,.;:")


def _cuando_se_dice(cada: int, cuando: datetime | None) -> str:
    """Cuándo toca, dicho como se dice y no como se imprime.

    "cada día a las 22" leído en voz alta suena a marcador de partido.
    """
    if cada <= 3600:
        return "cada hora"

    if cuando is None:
        return "cada día"

    hora = cuando.hour % 12 or 12

    franja = (
        "de la mañana"
        if cuando.hour < 12
        else "de la tarde" if cuando.hour < 20 else "de la noche"
    )

    return f"cada día a las {hora} {franja}"


def _cuantas(n: int) -> str:
    return "una tarea" if n == 1 else f"{n} tareas"


def _fecha(valor: Any) -> datetime | None:
    if not valor:
        return None

    try:
        return datetime.fromisoformat(str(valor))

    except ValueError:
        return None
