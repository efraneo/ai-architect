"""Etiquetas de versión.

Venía de ``repository/`` con ``check=True`` en todo: borrar una etiqueta que
no existe lanzaba ``CalledProcessError``, y listar fuera de un repositorio
también. Y ``create`` no devolvía nada, así que si git fallaba -- por una
etiqueta repetida -- quien llamaba seguía creyendo que la había creado.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ai_architect.git.tag_manager import TagManager


def git(repo: Path, *argumentos: str) -> None:
    subprocess.run(
        ["git", *argumentos],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-b", "principal")
    git(tmp_path, "config", "user.email", "prueba@ejemplo.com")
    git(tmp_path, "config", "user.name", "Prueba")

    (tmp_path / "modulo.py").write_text("valor = 1\n", encoding="utf-8")

    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "primero")

    return tmp_path


# --- Fuera de un repositorio ------------------------------------------------


def test_una_carpeta_suelta_no_revienta(tmp_path: Path) -> None:
    gestor = TagManager(tmp_path)

    assert gestor.list() == []
    assert gestor.create("v1") is False
    assert gestor.delete("v1") is False
    assert gestor.latest() == ""


# --- Listar y crear ---------------------------------------------------------


def test_un_repositorio_sin_etiquetas(repo: Path) -> None:
    assert TagManager(repo).list() == []


def test_crear_y_listar(repo: Path) -> None:
    gestor = TagManager(repo)

    assert gestor.create("v1.0.0") is True
    assert gestor.list() == ["v1.0.0"]


def test_crear_con_mensaje(repo: Path) -> None:
    gestor = TagManager(repo)

    assert gestor.create("v1.0.0", "primera versión") is True
    assert gestor.exists("v1.0.0") is True


def test_repetir_una_etiqueta_falla(repo: Path) -> None:
    """La regresión: no devolvía nada, así que el fallo pasaba inadvertido."""
    gestor = TagManager(repo)
    gestor.create("v1.0.0")

    assert gestor.create("v1.0.0") is False


def test_las_etiquetas_salen_ordenadas(repo: Path) -> None:
    gestor = TagManager(repo)

    for etiqueta in ("v0.2.0", "v0.1.0", "v0.3.0"):
        gestor.create(etiqueta)

    assert gestor.list() == ["v0.1.0", "v0.2.0", "v0.3.0"]


# --- Borrar -----------------------------------------------------------------


def test_borrar_una_etiqueta(repo: Path) -> None:
    gestor = TagManager(repo)
    gestor.create("v1.0.0")

    assert gestor.delete("v1.0.0") is True
    assert gestor.list() == []


def test_borrar_una_que_no_existe_no_revienta(repo: Path) -> None:
    """La regresión: lanzaba CalledProcessError."""
    assert TagManager(repo).delete("inventada") is False


# --- La más reciente --------------------------------------------------------


def test_la_ultima_es_por_historia_no_por_alfabeto(repo: Path) -> None:
    gestor = TagManager(repo)
    gestor.create("v0.9.0")

    (repo / "otro.py").write_text("x = 1\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "segundo")

    gestor.create("v0.10.0")

    # Por orden alfabético "v0.9.0" va después; por historia, no.
    assert gestor.latest() == "v0.10.0"


def test_sin_etiquetas_no_hay_ultima(repo: Path) -> None:
    assert TagManager(repo).latest() == ""
