"""
=========================================================
Agent Scope

What the agents look at -- and what they must not.
=========================================================

Every agent walked the tree with a bare ``rglob``, so on this very
repository the Security Agent reported fifteen leaked secrets: all of them
inside ``.venv`` -- ``httpx/_urls.py``, ``pydantic/types.py``, and even
binaries like ``ruff.exe``, where the regex matched raw bytes.

An agent that reports someone else's dependencies is not a help; it is
noise, and noise reaches the decision engine as findings.

The ignore list is the project's own (``filesystem/constants.py``): one
list, not one per agent.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from ai_architect.filesystem.ignore_manager import IgnoreManager

# Read as text by an agent, these are bytes: a regex matches anything there.
BINARY_EXTENSIONS = {
    ".pyc",
    ".pyd",
    ".pyo",
    ".so",
    ".dll",
    ".dylib",
    ".exe",
    ".bin",
    ".zip",
    ".gz",
    ".tar",
    ".whl",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".pdf",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".woff",
    ".woff2",
    ".ttf",
}


def gestor_de(raiz: Path) -> IgnoreManager:
    """El gestor de exclusiones del proyecto, con su ``.gitignore``.

    **Se cachea siempre, no solo dentro de un bloque compartido.**
    ``esta_ignorado()`` se llama una vez por archivo: sin caché, cada llamada
    abría el ``.gitignore``. La suite pasó de 2 segundos a 16 minutos antes
    de que esto estuviera aquí.

    Se invalida por la fecha del ``.gitignore``, así que editarlo se nota sin
    reiniciar nada.
    """
    clave = str(raiz)

    gitignore = raiz / ".gitignore"

    try:
        marca = gitignore.stat().st_mtime_ns
    except OSError:
        marca = 0

    guardado = _gestores.get(clave)

    if guardado is not None and guardado[0] == marca:
        return guardado[1]

    gestor = IgnoreManager.for_project(raiz)

    _gestores[clave] = (marca, gestor)

    return gestor


def esta_ignorado(archivo: Path, raiz: Path) -> bool:
    """¿Está el archivo dentro de algo que no es del proyecto?

    Se mira la ruta relativa entera, no solo la carpeta padre: ``.venv``
    está cuatro niveles por encima de ``site-packages/httpx/_urls.py``.

    Además de la lista fija, se respeta el ``.gitignore`` del proyecto: cada
    repositorio ignora sus propias carpetas de salida, y recorrerlas es el
    mismo error que recorrer el ``.venv``.
    """
    try:
        relativo = archivo.relative_to(raiz)
    except ValueError:
        relativo = archivo

    return gestor_de(raiz).should_ignore(relativo)


def es_binario(archivo: Path) -> bool:
    """Reading this as text produces noise, not code."""
    return archivo.suffix.lower() in BINARY_EXTENSIONS


# --- Un solo recorrido para todos -------------------------------------------
#
# Cada agente recorría el árbol por su cuenta: once agentes, seis recorridos
# completos. Un recorrido de este repositorio cuesta 0,75 s, y cuatro de los
# agentes no hacen casi nada más que recorrer.
#
# Paralelizarlo con hilos se probó y salió **peor** (32 % más lento): el
# trabajo no está repartido entre los agentes, está repetido por cada uno.

Clave = tuple[str, str, bool]

_cache: dict[Clave, list[Path]] | None = None

# El gestor de exclusiones de cada raíz, con la fecha del ``.gitignore``
# que leyó. Va aparte del caché de recorridos: no guarda lo mismo y no
# caduca igual -- este sobrevive entre ejecuciones, aquel muere con el
# bloque.
_gestores: dict[str, tuple[int, IgnoreManager]] = {}


@contextmanager
def recorrido_compartido() -> Iterator[None]:
    """Dentro de este bloque el árbol se recorre una vez por patrón.

    El caché vive solo mientras dura el bloque: entre una inspección y la
    siguiente los archivos pueden haber cambiado, y devolver una lista vieja
    sería peor que recorrer de nuevo.

    Se puede anidar sin romper nada: solo el bloque exterior crea y destruye
    el caché.
    """
    global _cache

    if _cache is not None:  # ya hay uno activo más arriba
        yield
        return

    _cache = {}

    try:
        yield

    finally:
        _cache = None


def _recorrer(raiz: Path, patron: str, solo_archivos: bool) -> list[Path]:
    """El recorrido de verdad, con caché si hay un bloque compartido activo."""
    clave: Clave = (str(raiz), patron, solo_archivos)

    if _cache is not None and clave in _cache:
        return _cache[clave]

    encontrados = [
        entrada
        for entrada in raiz.rglob(patron)
        if not esta_ignorado(entrada, raiz)
        and (not solo_archivos or (entrada.is_file() and not es_binario(entrada)))
    ]

    if _cache is not None:
        _cache[clave] = encontrados

    return encontrados


def archivos(raiz: Path, patron: str = "*") -> Iterator[Path]:
    """The project's files: no dependencies, no caches, no binaries."""
    yield from _recorrer(raiz, patron, solo_archivos=True)


def archivos_py(raiz: Path) -> list[Path]:
    """The project's own Python files."""
    return _recorrer(raiz, "*.py", solo_archivos=True)


def todo(raiz: Path) -> list[Path]:
    """Todo lo que hay bajo la raíz, carpetas y binarios incluidos.

    Las métricas cuentan carpetas y el tamaño de los archivos: para ellas un
    ``.png`` sí forma parte del proyecto. Lo único que se descarta es lo que
    no es tuyo: ``.venv``, ``node_modules``, las cachés.
    """
    return _recorrer(raiz, "*", solo_archivos=False)
