"""El estado del repositorio, leído bien.

Venía de ``repository/``, la capa de git paralela que solo era alcanzable
desde ``agent.py`` -- que no importaba nadie. Traía dos fallos:

- ``check=True``: fuera de un repositorio **lanzaba una excepción** en vez
  de decir que no había nada que mirar.
- Clasificaba con ``"A" in code`` / ``"M" in code`` / ``"D" in code`` en una
  cadena de ``elif``. El código de porcelain son **dos columnas** -- índice y
  árbol de trabajo -- así que un ``AM`` contaba solo como creado, un ``MM``
  solo como modificado, y los renombrados y conflictos no contaban nada.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ai_architect.git.git_models import GitStatus
from ai_architect.git.status_manager import StatusManager


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
    """La regresión: iba con ``check=True`` y lanzaba CalledProcessError."""
    estado = StatusManager(tmp_path).status()

    assert isinstance(estado, GitStatus)
    assert estado.clean is True
    assert estado.branch == ""


# --- Un árbol limpio --------------------------------------------------------


def test_recien_commiteado_esta_limpio(repo: Path) -> None:
    estado = StatusManager(repo).status()

    assert estado.clean is True
    assert estado.total == 0
    assert estado.branch == "principal"


def test_is_clean_va_por_lo_mismo(repo: Path) -> None:
    assert StatusManager(repo).is_clean() is True


# --- Cada estado en su sitio ------------------------------------------------


def test_un_archivo_modificado(repo: Path) -> None:
    (repo / "modulo.py").write_text("valor = 2\n", encoding="utf-8")

    estado = StatusManager(repo).status()

    assert estado.modified == ["modulo.py"]
    assert estado.clean is False


def test_un_archivo_sin_seguir(repo: Path) -> None:
    (repo / "nuevo.py").write_text("x = 1\n", encoding="utf-8")

    assert StatusManager(repo).status().untracked == ["nuevo.py"]


def test_un_archivo_anadido(repo: Path) -> None:
    (repo / "nuevo.py").write_text("x = 1\n", encoding="utf-8")
    git(repo, "add", "nuevo.py")

    assert StatusManager(repo).status().created == ["nuevo.py"]


def test_un_archivo_borrado(repo: Path) -> None:
    (repo / "modulo.py").unlink()

    assert StatusManager(repo).status().deleted == ["modulo.py"]


def test_anadido_y_luego_modificado_cuenta_por_los_dos(repo: Path) -> None:
    """La regresión: ``AM`` contaba solo como creado.

    Las dos primeras columnas son índice y árbol de trabajo, y un archivo
    puede estar en las dos: esto no es una cadena de ``elif``."""
    (repo / "nuevo.py").write_text("x = 1\n", encoding="utf-8")
    git(repo, "add", "nuevo.py")
    (repo / "nuevo.py").write_text("x = 2\n", encoding="utf-8")

    estado = StatusManager(repo).status()

    assert estado.created == ["nuevo.py"]
    assert estado.modified == ["nuevo.py"]


def test_un_renombrado_se_ve(repo: Path) -> None:
    """La regresión: ``R`` no entraba en ninguna rama del ``elif``."""
    git(repo, "mv", "modulo.py", "renombrado.py")

    estado = StatusManager(repo).status()

    assert estado.renamed == ["renombrado.py"]
    assert estado.clean is False


def test_un_conflicto_se_ve(repo: Path) -> None:
    """La regresión: ``UU`` tampoco entraba en ninguna rama."""
    git(repo, "checkout", "-b", "otra")
    (repo / "modulo.py").write_text("valor = 2\n", encoding="utf-8")
    git(repo, "commit", "-am", "en la otra")

    git(repo, "checkout", "principal")
    (repo / "modulo.py").write_text("valor = 3\n", encoding="utf-8")
    git(repo, "commit", "-am", "en principal")

    subprocess.run(
        ["git", "merge", "otra"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    estado = StatusManager(repo).status()

    assert estado.conflicted == ["modulo.py"]
    assert estado.clean is False


# --- El modelo --------------------------------------------------------------


def test_clean_se_deduce_no_se_guarda() -> None:
    """Antes era un campo fijado al construir: tocar las listas después lo
    dejaba mintiendo."""
    estado = GitStatus()

    assert estado.clean is True

    estado.modified.append("algo.py")

    assert estado.clean is False


def test_total_suma_todo() -> None:
    estado = GitStatus(
        modified=["a"],
        created=["b"],
        deleted=["c"],
        renamed=["d"],
        untracked=["e"],
        conflicted=["f"],
    )

    assert estado.total == 6


def test_se_puede_serializar(repo: Path) -> None:
    """El informe de los agentes va a JSON."""
    datos = StatusManager(repo).status().as_dict()

    assert datos["branch"] == "principal"
    assert datos["clean"] is True
    assert datos["total"] == 0
