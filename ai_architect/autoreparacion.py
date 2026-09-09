"""
=========================================================
Autorreparación

Cuando falla su propio código, Architect avisa; con tu «adelante», se arregla.
=========================================================

La regla, dicha por Efraín y grabada aquí: **nunca se repara solo**. Cada
avería se apunta y se dice («falló algo en mi propio código; si dices
“adelante”, lo reviso»). Solo la palabra maestra **«adelante»** arranca la
reparación, y solo otra vez «adelante» reconstruye el instalador. No hay
temporizador, ni disparo automático, ni aprendizaje de este ciclo: siempre
pide tu orden y tu aprobación.

El ciclo, paso a paso:

1. ``registrar()`` apunta la avería (comando, frase, error, traza) en
   ``~/.ai_architect/averias.json``.
2. «adelante» → ``reparar()``: ``hacer`` trabaja sobre el **código fuente de
   Architect** (``ARCHITECT_FUENTE`` en el ``.env``, o la carpeta del paquete
   si corre desde el repositorio) con permiso de escritura, y después se corren
   las pruebas **aparte**, con pytest de verdad: no se cree lo que el agente
   diga, se comprueba.
3. Si las pruebas pasan, ofrece reconstruir el instalador; otro «adelante» →
   ``reconstruir()`` (``empaquetar.cmd``).

Instalado como programa (``.exe``) no puede tocarse a sí mismo: repara el
código fuente, que es de donde sale el próximo instalador.
"""

from __future__ import annotations

import json
import logging
import os
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

from ai_architect.agente.rutas_agente import get_config_dir

# Cómo suena «no sé hacerlo» en una respuesta. Cada vez que Architect contesta
# así, lo que se pidió queda apuntado como capacidad nueva.
INCAPACIDAD = re.compile(
    r"\bno (?:puedo|podr[ií]a|tengo (?:la )?capacidad|es posible|s[eé] c[oó]mo|"
    r"s[eé] hacer|estoy capacitad[oa]|logro|supe|entend[ií]|conozco|dispongo)\b|"
    r"no (?:me es|resulta) posible|no lo s[eé] hacer|fuera de mi alcance|no est[aá] en mis",
    re.IGNORECASE,
)

PALABRA_MAESTRA = (
    "adelante",
    "adelante architect",
    "architect adelante",
    "adelante arquitecto",
)

TIEMPO_PRUEBAS = 900
TIEMPO_EMPAQUETAR = 1200

# Lo último que está haciendo, para no arrancar dos reparaciones a la vez.
_en_curso = threading.Event()
_ultimo_informe = ""

logger = logging.getLogger(__name__)


def ruta() -> Path:
    return get_config_dir() / "averias.json"


def _cargar() -> list[dict[str, Any]]:
    try:
        return (
            list(json.loads(ruta().read_text(encoding="utf-8")))
            if ruta().is_file()
            else []
        )

    except ValueError:
        return []


def _guardar(lista: list[dict[str, Any]]) -> None:
    try:
        ruta().write_text(
            json.dumps(lista[-50:], ensure_ascii=False, indent=2), encoding="utf-8"
        )

    except OSError as _error:
        logger.debug("se ignora: %s", _error)


def registrar(comando: str, frase: str, error: str, traza: str = "") -> dict[str, Any]:
    """Apunta una avería del propio código y devuelve la ficha."""
    averia = {
        "id": secrets.token_hex(3),
        "cuando": time.time(),
        "comando": comando or "?",
        "frase": (frase or "")[:300],
        "error": (error or "")[:600],
        "traza": (traza or "")[-3000:],
        "estado": "pendiente",
    }
    lista = _cargar()
    lista.append(averia)
    _guardar(lista)

    return averia


def pendiente() -> dict[str, Any] | None:
    """La avería más reciente que espera un «adelante» (reparar o reconstruir)."""
    for averia in reversed(_cargar()):
        if averia.get("estado") in ("pendiente", "reparada"):
            return averia

    return None


def averias() -> list[dict[str, Any]]:
    return _cargar()


def _actualizar(id_: str, **cambios: Any) -> None:
    lista = _cargar()

    for averia in lista:
        if averia.get("id") == id_:
            averia.update(cambios)

    _guardar(lista)


def en_curso() -> bool:
    return _en_curso.is_set()


def ultimo_informe() -> str:
    return _ultimo_informe


def es_palabra_maestra(texto: str) -> bool:
    from ai_architect.core.texto import sin_adornos

    return sin_adornos(texto) in PALABRA_MAESTRA


# --- Dónde está su código -------------------------------------------------------


def fuente() -> Path | None:
    """La carpeta del código fuente de Architect, si está en esta máquina."""
    declarada = os.getenv("ARCHITECT_FUENTE", "")

    if declarada and (Path(declarada) / "pyproject.toml").is_file():
        return Path(declarada)

    if getattr(sys, "frozen", False):
        return None

    from ai_architect.core.env_file import raiz_del_paquete

    raiz = raiz_del_paquete()

    return raiz if (raiz / "pyproject.toml").is_file() else None


def _python_de(fuente_: Path) -> str:
    venv = (
        fuente_
        / ".venv"
        / ("Scripts" if os.name == "nt" else "bin")
        / ("python.exe" if os.name == "nt" else "python")
    )

    return str(venv) if venv.is_file() else sys.executable


# --- Reparar --------------------------------------------------------------------


def orden_de_reparacion(averia: dict[str, Any]) -> str:
    if averia.get("comando") == "mejora":
        return (
            "Este repositorio es TU PROPIO CÓDIGO (AI-architect). El usuario pide una "
            f"capacidad nueva: «{averia['frase']}». Impleméntala de la forma más pequeña y "
            "coherente con el proyecto: mira cómo están hechos los comandos en "
            "ai_architect/commands, los atajos de voz en commands/respuestas.py y la tabla "
            "del CLI en cli.py; añade pruebas nuevas en tests/. Si hace falta un paquete de "
            "Python, una skill (carpeta con skill.toml en ~/.ai_architect/skills) o un agente "
            "nuevo (ai_architect/agents), instálalo o créalo tú mismo: tienes la herramienta "
            "`instalar` y permiso para escribir. Corre `python -m pytest -q -x` "
            "y `python -m ruff check ai_architect` hasta que pasen. No empaquetes, no hagas "
            "commit y no automatices este ciclo: el usuario lo autoriza cada vez con su "
            "palabra maestra. Termina con un informe breve: qué añadiste (archivo por archivo) "
            "y cómo se usa."
        )

    return (
        "Este repositorio es TU PROPIO CÓDIGO (AI-architect). Falló el comando "
        f"«{averia['comando']}» al atender la orden «{averia['frase']}» con este error:\n"
        f"{averia['error']}\n\nTraza:\n{averia['traza'] or '(sin traza)'}\n\n"
        "Encuentra la causa y corrígela con el cambio más pequeño y seguro, sin cambiar "
        "APIs públicas. Corre `python -m pytest -q -x` con el intérprete del proyecto y "
        "`python -m ruff check ai_architect` hasta que pasen. No empaquetes, no hagas "
        "commit y no automatices este ciclo: el usuario lo autoriza cada vez con su "
        "palabra maestra. Termina con un informe breve: qué fallaba, qué cambiaste "
        "(archivo por archivo) y el resultado de las pruebas."
    )


# --- Con quién se repara ---------------------------------------------------------
#
# Efraín pidió que se conecte «directamente con Claude» para arreglarse y
# reescribir su código. Si está el CLI de Claude Code en esta máquina, la
# reparación se la encarga a él, en la carpeta del código fuente, con la misma
# orden; si no, la hace el propio agente `hacer`.

TIEMPO_CLAUDE = 1800


def reparador() -> str:
    """``"claude"`` si el CLI de Claude Code está y no se ha pedido otra cosa."""

    elegido = os.getenv("ARCHITECT_REPARADOR", "").strip().lower()

    if elegido in ("hacer", "agente"):
        return "hacer"

    return "claude" if shutil.which("claude") else "hacer"


def reparar_con_claude(fuente_: Path, orden: str) -> dict[str, Any]:
    """Claude Code, en modo no interactivo, sobre el código fuente."""

    ejecutable = shutil.which("claude")

    if not ejecutable:
        return {"ok": False, "informe": "No encuentro el CLI de Claude Code."}

    try:
        salida = subprocess.run(
            [
                ejecutable,
                "-p",
                orden,
                "--output-format",
                "text",
                # Sin terminal no hay a quién preguntar: se le deja editar y
                # correr las pruebas dentro de su propio repositorio.
                "--dangerously-skip-permissions",
            ],
            cwd=str(fuente_),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIEMPO_CLAUDE,
        )

    except (OSError, subprocess.SubprocessError) as e:
        return {"ok": False, "informe": f"Claude Code no pudo correr: {e}"}

    texto = (salida.stdout or "").strip() or (salida.stderr or "").strip()

    return {"ok": salida.returncode == 0, "informe": texto[-3000:]}


def correr_pruebas(fuente_: Path) -> dict[str, Any]:
    """pytest de verdad sobre el código fuente. Devuelve ok y la última línea."""
    try:
        salida = subprocess.run(
            [_python_de(fuente_), "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider"],
            cwd=str(fuente_),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIEMPO_PRUEBAS,
        )

    except (OSError, subprocess.SubprocessError) as e:
        return {"ok": False, "resumen": str(e)[:200]}

    lineas = [ln for ln in (salida.stdout or "").splitlines() if ln.strip()]
    resumen = lineas[-1] if lineas else (salida.stderr or "").strip()[-200:]

    return {"ok": salida.returncode == 0, "resumen": resumen[:300]}


def reparar(averia: dict[str, Any], motor: Any = None) -> dict[str, Any]:
    """La reparación entera: `hacer` con permiso sobre el código fuente + pruebas aparte."""
    global _ultimo_informe

    fuente_ = fuente()

    if fuente_ is None:
        return {
            "ok": False,
            "informe": (
                "No encuentro mi código fuente en esta máquina (ARCHITECT_FUENTE en "
                "~/.ai_architect/.env). Instalado como programa no puedo tocarme."
            ),
        }

    if _en_curso.is_set():
        return {"ok": False, "informe": "Ya hay una reparación en marcha."}

    _en_curso.set()
    _actualizar(averia["id"], estado="reparando")

    try:
        if reparador() == "claude" and motor is None:
            hecho = reparar_con_claude(fuente_, orden_de_reparacion(averia))
            informe = str(hecho.get("informe", ""))

        else:
            from ai_architect.commands import hacer

            resultado = hacer.run(
                str(fuente_), orden_de_reparacion(averia), si=True, motor=motor
            )
            informe = str(resultado.get("explanation") or resultado.get("error") or "")

        pruebas = correr_pruebas(fuente_)

    finally:
        _en_curso.clear()

    if pruebas["ok"]:
        _actualizar(
            averia["id"],
            estado="reparada",
            informe=informe[:2000],
            pruebas=pruebas["resumen"],
        )

        if averia.get("comando") == "mejora":
            cabeza = f"Mejora «{averia['frase'][:60]}» programada"
        else:
            cabeza = f"Reparación de «{averia['comando']}» lista"

        _ultimo_informe = (
            f"{cabeza} y las pruebas pasan ({pruebas['resumen']}). {informe[:600]}"
            "\n\nSi dices «adelante», me reinicio con el cambio."
        )

        # Lo aprendido queda en la memoria a largo plazo, con fecha.
        try:
            from ai_architect.agente import memoria

            memoria.recordar(
                (
                    f"Aprendió a: {averia['frase'][:120]}"
                    if averia.get("comando") == "mejora"
                    else f"Se reparó una avería en «{averia['comando']}»"
                )
                + f" ({time.strftime('%d/%m/%Y')})",
                fuente="autoreparacion",
            )

        except Exception as e:  # noqa: BLE001 - la memoria es un extra
            logger.debug("se ignora: %s", e)

        return {"ok": True, "informe": _ultimo_informe, "pruebas": pruebas}

    _actualizar(
        averia["id"],
        estado="pendiente",
        informe=informe[:2000],
        pruebas=pruebas["resumen"],
    )
    _ultimo_informe = (
        f"Intenté reparar «{averia['comando']}», pero las pruebas no pasan ({pruebas['resumen']}). "
        f"{informe[:600]}\n\nNo toco nada más. Si dices «adelante», lo intento otra vez."
    )

    return {"ok": False, "informe": _ultimo_informe, "pruebas": pruebas}


# --- Reconstruir -------------------------------------------------------------------


def reconstruir(averia: dict[str, Any] | None = None) -> dict[str, Any]:
    """`empaquetar.cmd` sobre el código fuente. Solo tras un «adelante»."""
    global _ultimo_informe

    fuente_ = fuente()

    if fuente_ is None:
        return {
            "ok": False,
            "informe": "No encuentro mi código fuente para reconstruirme.",
        }

    guion = fuente_ / "empaquetar.cmd"

    if not guion.is_file():
        return {"ok": False, "informe": f"No está {guion.name} en {fuente_}."}

    if _en_curso.is_set():
        return {"ok": False, "informe": "Ya hay un trabajo en marcha."}

    _en_curso.set()

    try:
        salida = subprocess.run(
            ["cmd", "/c", str(guion)],
            cwd=str(fuente_),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIEMPO_EMPAQUETAR,
        )

    except (OSError, subprocess.SubprocessError) as e:
        _en_curso.clear()

        return {"ok": False, "informe": f"No pude reconstruir: {e}"}

    finally:
        _en_curso.clear()

    instalador = fuente_ / "salida" / "ArquitectoSetup.exe"
    ok = salida.returncode == 0 and instalador.is_file()

    if ok and averia is not None:
        _actualizar(averia["id"], estado="reconstruida")

    _ultimo_informe = (
        f"Instalador reconstruido: {instalador} ({instalador.stat().st_size // 1_000_000} MB)."
        if ok
        else "La reconstrucción falló: "
        + (salida.stderr or salida.stdout).strip()[-300:]
    )

    return {
        "ok": ok,
        "informe": _ultimo_informe,
        "instalador": str(instalador) if ok else "",
    }


# --- La palabra maestra ---------------------------------------------------------


def adelante(avisar: Any = None, motor: Any = None, en_hilo: bool = True) -> str:
    """Qué hace un «adelante» ahora mismo, y lo arranca. Devuelve lo que se dice.

    ``avisar(texto)`` recibe el resultado cuando termina (voz proactiva, Telegram…).
    """
    if _en_curso.is_set():
        return "Ya estoy en ello; te aviso cuando termine."

    averia = pendiente()

    if averia is None:
        return "No tengo nada pendiente de tu «adelante»."

    if averia.get("estado") == "reparada":
        _actualizar(averia["id"], estado="aplicada")
        trabajo = reiniciar
        dicho = "Adelante: me reinicio con el código nuevo. Dame unos segundos."

    else:
        trabajo = lambda: reparar(averia, motor=motor)  # noqa: E731 - es un despacho
        dicho = (
            f"Adelante: programo la mejora «{averia['frase'][:70]}», corro mis pruebas "
            "y te aviso. No toco nada más sin tu orden."
            if averia.get("comando") == "mejora"
            else f"Adelante: reviso la avería de «{averia['comando']}», la corrijo y corro mis "
            "pruebas. No toco nada más sin tu orden. Te aviso cuando termine."
        )

    def _hacerlo() -> None:
        try:
            salida = trabajo()

        except Exception as e:  # noqa: BLE001 - se cuenta, no se esconde
            salida = {"ok": False, "informe": f"La reparación reventó: {e}"}

        if avisar is not None:
            try:
                avisar(str(salida.get("informe", "")))

            except Exception as _error:  # noqa: BLE001 - el aviso es un extra
                logger.debug("se ignora: %s", _error)

    if en_hilo:
        threading.Thread(target=_hacerlo, daemon=True, name="architect-reparar").start()

    else:
        _hacerlo()

    return dicho


def es_incapacidad(texto: str) -> bool:
    return bool(INCAPACIDAD.search(texto or ""))


def apuntar_incapacidad(frase: str, respuesta: str) -> tuple[dict[str, Any], str]:
    """Lo que no supo hacer queda como mejora pendiente, y se ofrece aprenderlo."""
    averia = registrar(
        "mejora",
        frase,
        "no supe hacerlo: " + " ".join((respuesta or "").split())[:300],
    )

    return averia, (
        "Eso todavía no lo sé hacer. Si dices «adelante», aprendo: programo la capacidad "
        "en mi código, instalo lo que haga falta, la pruebo y me reinicio con ella."
    )


def reiniciar() -> dict[str, Any]:
    """Se vuelve a lanzar a sí mismo con el código nuevo y cierra esta sesión.

    Solo tras un «adelante»: la reparación cambia archivos, pero el proceso
    que está corriendo sigue con los viejos hasta que arranca otra vez.
    """
    global _ultimo_informe

    if getattr(sys, "frozen", False):
        orden = [sys.executable, *sys.argv[1:]]
    else:
        orden = [sys.executable, "-m", "ai_architect.cli", *sys.argv[1:]]

    try:
        banderas = 0

        # `sys.platform` y no `os.name`: mypy solo entiende el primero como
        # guarda de plataforma, y en Linux esas banderas no existen.
        if sys.platform == "win32":
            banderas = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

        subprocess.Popen(orden, creationflags=banderas, close_fds=True)

    except (OSError, AttributeError) as e:
        _ultimo_informe = f"No pude reiniciarme: {e}. Cierra y vuelve a abrirme."

        return {"ok": False, "informe": _ultimo_informe}

    try:
        from ai_architect.commands import conversar

        conversar.cerrar_sesion(2.0)

    except (
        Exception
    ) as e:  # noqa: BLE001 - sin conversación abierta no hay nada que cerrar
        logger.debug("se ignora: %s", e)

    _ultimo_informe = "Me reinicio con el código nuevo. Dame unos segundos."

    return {"ok": True, "informe": _ultimo_informe}


def aviso_de_averia(averia: dict[str, Any]) -> str:
    """Lo que se le dice al usuario cuando acaba de fallar algo propio."""
    return (
        f"Falló algo en mi propio código (comando «{averia['comando']}»). "
        "Si dices «adelante», lo reviso, lo corrijo y corro mis pruebas; sin tu orden no lo toco."
    )
