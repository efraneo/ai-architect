"""
=========================================================
Instalar

Que Architect se procure lo que le falta: paquetes de Python y skills.
=========================================================

- ``paquete("rich")`` instala con el ``pip`` del mismo intérprete que está
  corriendo y **lo apunta en ``requirements.txt``** del proyecto, para que la
  próxima máquina lo tenga sin que nadie se acuerde.
- ``skill("https://github.com/usuario/repo")`` baja una skill (una carpeta con
  ``skill.toml`` o ``SKILL.md``) a ``~/.ai_architect/skills/<nombre>``; vale
  un repositorio entero, una subcarpeta (``.../tree/main/skills/x``) o un
  archivo suelto en crudo.

Todo lo instalado queda apuntado en ``~/.ai_architect/instalado.json``.

Dentro del ``.exe`` empaquetado no hay ``pip``: los paquetes se instalan solo
en el entorno de desarrollo; las skills sí, en cualquiera.
"""

from __future__ import annotations

import io
import json
import logging
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

import requests

from ai_architect.agente.rutas_agente import get_config_dir, get_skills_dir

TIEMPO_LIMITE = 600

# Un nombre de paquete de PyPI, con extras y especificador de versión como mucho.
PAQUETE_VALIDO = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*(\[[A-Za-z0-9_,.-]+\])?([<>=!~]=?[A-Za-z0-9.*+!-]+(,[<>=!~]=?[A-Za-z0-9.*+!-]+)*)?$"
)

logger = logging.getLogger(__name__)


def ruta_registro() -> Path:
    return get_config_dir() / "instalado.json"


def _apuntar(que: str, nombre: str, detalle: str = "") -> None:
    ruta = ruta_registro()

    try:
        lista = json.loads(ruta.read_text(encoding="utf-8")) if ruta.is_file() else []

    except ValueError:
        lista = []

    lista.append(
        {"que": que, "nombre": nombre, "detalle": detalle, "cuando": time.time()}
    )

    try:
        ruta.write_text(
            json.dumps(lista, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    except OSError as _error:
        logger.debug("se ignora: %s", _error)


def instalado() -> list[dict[str, Any]]:
    ruta = ruta_registro()

    try:
        return (
            list(json.loads(ruta.read_text(encoding="utf-8"))) if ruta.is_file() else []
        )

    except ValueError:
        return []


# --- Paquetes ------------------------------------------------------------------


def empaquetado() -> bool:
    return bool(getattr(sys, "frozen", False))


def paquete(
    nombre: str, requisitos: Path | str | None = "requirements.txt"
) -> dict[str, Any]:
    """``pip install nombre`` en este intérprete y anotación en requirements."""
    limpio = (nombre or "").strip()

    if not PAQUETE_VALIDO.match(limpio):
        return {"ok": False, "error": f"eso no parece un paquete de PyPI: {nombre!r}"}

    if empaquetado():
        return {
            "ok": False,
            "error": (
                "dentro del instalador no hay pip: los paquetes se instalan en el entorno "
                "de desarrollo (pip install " + limpio + ")"
            ),
        }

    try:
        salida = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                limpio,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIEMPO_LIMITE,
        )

    except (OSError, subprocess.SubprocessError) as e:
        return {"ok": False, "error": str(e)}

    if salida.returncode != 0:
        return {"ok": False, "error": (salida.stderr or salida.stdout).strip()[-600:]}

    apuntado = _en_requisitos(limpio, requisitos) if requisitos else False

    _apuntar("paquete", limpio, "requirements.txt" if apuntado else "")

    return {"ok": True, "paquete": limpio, "requirements": apuntado}


def _en_requisitos(paquete_: str, ruta: Path | str) -> bool:
    """Añade el paquete a requirements.txt si no estaba. Devuelve si lo añadió."""
    archivo = Path(ruta)
    base = re.split(r"[\[<>=!~]", paquete_, maxsplit=1)[0].lower().replace("_", "-")

    try:
        actual = archivo.read_text(encoding="utf-8") if archivo.is_file() else ""

    except OSError:
        return False

    for linea in actual.splitlines():
        limpia = linea.strip()

        if not limpia or limpia.startswith("#"):
            continue

        if (
            re.split(r"[\[<>=!~ ]", limpia, maxsplit=1)[0].lower().replace("_", "-")
            == base
        ):
            return False

    try:
        with archivo.open("a", encoding="utf-8") as f:
            if actual and not actual.endswith("\n"):
                f.write("\n")

            f.write(f"{paquete_}\n")

    except OSError:
        return False

    return True


# --- Skills ------------------------------------------------------------------------

GITHUB = re.compile(
    r"^https?://github\.com/(?P<usuario>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?"
    r"(?:/tree/(?P<rama>[^/]+)(?P<ruta>/.*)?)?/?$"
)


def skill(origen: str, destino_base: Path | None = None) -> dict[str, Any]:
    """Baja una skill de GitHub (repositorio, subcarpeta) o de un archivo en crudo."""
    origen = (origen or "").strip()
    base = destino_base or get_skills_dir()

    if not origen.startswith(("http://", "https://")):
        return {"ok": False, "error": "dame la URL de GitHub o del archivo"}

    coincide = GITHUB.match(origen)

    try:
        if coincide:
            return _skill_de_github(coincide, base)

        return _skill_de_archivo(origen, base)

    except (requests.RequestException, OSError, zipfile.BadZipFile, ValueError) as e:
        return {"ok": False, "error": str(e)}


def _skill_de_archivo(url: str, base: Path) -> dict[str, Any]:
    nombre_archivo = url.rsplit("/", 1)[-1]

    if nombre_archivo not in ("skill.toml", "SKILL.md"):
        return {"ok": False, "error": "el archivo debe llamarse skill.toml o SKILL.md"}

    respuesta = requests.get(url, timeout=60)
    respuesta.raise_for_status()

    nombre = _nombre_de_skill(respuesta.text) or url.rstrip("/").split("/")[-2]
    carpeta = base / _seguro(nombre)
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / nombre_archivo).write_text(respuesta.text, encoding="utf-8")

    _apuntar("skill", nombre, url)

    return {"ok": True, "skill": nombre, "carpeta": str(carpeta), "archivos": 1}


def _skill_de_github(coincide: re.Match[str], base: Path) -> dict[str, Any]:
    usuario, repo = coincide["usuario"], coincide["repo"]
    rama = coincide["rama"] or "main"
    ruta = (coincide["ruta"] or "").strip("/")

    url = f"https://codeload.github.com/{usuario}/{repo}/zip/refs/heads/{rama}"
    respuesta = requests.get(url, timeout=120)

    if respuesta.status_code == 404 and not coincide["rama"]:
        rama = "master"
        respuesta = requests.get(
            f"https://codeload.github.com/{usuario}/{repo}/zip/refs/heads/{rama}",
            timeout=120,
        )

    respuesta.raise_for_status()

    paquete_zip = zipfile.ZipFile(io.BytesIO(respuesta.content))
    raiz = paquete_zip.namelist()[0].split("/")[0]
    prefijo = f"{raiz}/{ruta}".rstrip("/") + "/"

    miembros = [m for m in paquete_zip.namelist() if m.startswith(prefijo)]
    manifiestos = [
        m for m in miembros if m.rsplit("/", 1)[-1] in ("skill.toml", "SKILL.md")
    ]

    if not manifiestos:
        return {"ok": False, "error": "ahí no hay ningún skill.toml ni SKILL.md"}

    # La skill es la carpeta del manifiesto más superficial.
    manifiesto = min(manifiestos, key=lambda m: m.count("/"))
    carpeta_zip = manifiesto.rsplit("/", 1)[0] + "/"
    nombre = _nombre_de_skill(
        paquete_zip.read(manifiesto).decode("utf-8", "replace")
    ) or (carpeta_zip.rstrip("/").split("/")[-1] if ruta else repo)
    destino = base / _seguro(nombre)
    destino.mkdir(parents=True, exist_ok=True)
    escritos = 0

    for miembro in miembros:
        if not miembro.startswith(carpeta_zip) or miembro.endswith("/"):
            continue

        relativo = Path(miembro[len(carpeta_zip) :])

        if ".." in relativo.parts:
            continue

        salida = destino / relativo
        salida.parent.mkdir(parents=True, exist_ok=True)
        salida.write_bytes(paquete_zip.read(miembro))
        escritos += 1

    _apuntar("skill", nombre, f"github.com/{usuario}/{repo}@{rama}/{ruta}".rstrip("/"))

    return {"ok": True, "skill": nombre, "carpeta": str(destino), "archivos": escritos}


def _nombre_de_skill(texto: str) -> str:
    coincide = re.search(r'^\s*name\s*[:=]\s*"?([A-Za-z0-9_.-]+)"?', texto, re.M)

    return coincide.group(1) if coincide else ""


def _seguro(nombre: str) -> str:
    limpio = re.sub(r"[^A-Za-z0-9_.-]+", "-", nombre).strip("-.")

    return limpio or "skill"
