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
from pathlib import Path

from ai_architect.filesystem.constants import DEFAULT_IGNORED_DIRECTORIES

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


def esta_ignorado(archivo: Path, raiz: Path) -> bool:
    """Is the file inside an ignored directory (``.venv``, ``node_modules``...)?

    The whole relative path is checked, not just the parent: ``.venv`` sits
    many levels above ``site-packages/httpx/_urls.py``.
    """
    try:
        relativo = archivo.relative_to(raiz)
    except ValueError:
        relativo = archivo

    return any(parte in DEFAULT_IGNORED_DIRECTORIES for parte in relativo.parts)


def es_binario(archivo: Path) -> bool:
    """Reading this as text produces noise, not code."""
    return archivo.suffix.lower() in BINARY_EXTENSIONS


def archivos(raiz: Path, patron: str = "*") -> Iterator[Path]:
    """The project's files: no dependencies, no caches, no binaries."""
    for archivo in raiz.rglob(patron):
        if not archivo.is_file():
            continue

        if esta_ignorado(archivo, raiz) or es_binario(archivo):
            continue

        yield archivo


def archivos_py(raiz: Path) -> list[Path]:
    """The project's own Python files."""
    return list(archivos(raiz, "*.py"))
