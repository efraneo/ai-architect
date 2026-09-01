"""Las ramas, apuntando al repositorio correcto.

``BranchManager`` venía de ``autonomous/``, donde llamaba a git **sin
``cwd``**: operaba sobre el directorio en el que estuviera el proceso, no
sobre el repositorio analizado. Revisar un proyecto ajeno habría creado la
rama en el repositorio equivocado -- en el de AI-architect, por ejemplo.

Junto a él venían un ``MergeManager`` y un ``RollbackManager`` con el mismo
fallo, y el segundo lanzaba un ``git reset --hard HEAD~1`` suelto. Se
podaron: ``git/commit_manager.py`` ya hace *rollback* y *discard* pasando
``cwd=self.repository``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ai_architect.git.branch_manager import BranchManager


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
    """Un repositorio de verdad, con un commit para tener rama."""
    git(tmp_path, "init", "-b", "principal")
    git(tmp_path, "config", "user.email", "prueba@ejemplo.com")
    git(tmp_path, "config", "user.name", "Prueba")

    (tmp_path / "modulo.py").write_text("valor = 1\n", encoding="utf-8")

    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "primero")

    return tmp_path


# --- Apunta a donde se le dice ----------------------------------------------


def test_trabaja_sobre_el_repositorio_indicado(repo: Path, tmp_path: Path) -> None:
    """La regresión: sin ``cwd`` operaba sobre el directorio del proceso."""
    assert BranchManager(repo).current() == "principal"


def test_una_carpeta_que_no_es_un_repositorio_no_hace_nada(tmp_path: Path) -> None:
    """Sin esta guarda, git subiría por el árbol hasta encontrar otro
    repositorio y trabajaría sobre él."""
    suelta = tmp_path / "suelta"
    suelta.mkdir()

    gestor = BranchManager(suelta)

    assert gestor.current() == ""
    assert gestor.create("nueva") is False


# --- Crear y cambiar --------------------------------------------------------


def test_crea_la_rama_y_se_cambia_a_ella(repo: Path) -> None:
    gestor = BranchManager(repo)

    assert gestor.create("trabajo") is True
    assert gestor.current() == "trabajo"


def test_dice_que_no_si_la_rama_ya_existe(repo: Path) -> None:
    """Antes iba con ``check=False`` y no devolvía nada: el trabajo seguía
    creyendo que estaba en la rama nueva."""
    gestor = BranchManager(repo)
    gestor.create("trabajo")
    gestor.checkout("principal")

    assert gestor.create("trabajo") is False


def test_sabe_si_una_rama_existe(repo: Path) -> None:
    gestor = BranchManager(repo)

    assert gestor.exists("principal") is True
    assert gestor.exists("inventada") is False


def test_se_cambia_a_una_rama_existente(repo: Path) -> None:
    gestor = BranchManager(repo)
    gestor.create("trabajo")

    assert gestor.checkout("principal") is True
    assert gestor.current() == "principal"


def test_cambiarse_a_una_rama_que_no_existe_falla(repo: Path) -> None:
    assert BranchManager(repo).checkout("inventada") is False


# --- Fusionar ---------------------------------------------------------------


def test_fusiona_una_rama(repo: Path) -> None:
    gestor = BranchManager(repo)
    gestor.create("trabajo")

    (repo / "nuevo.py").write_text("otro = 2\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "segundo")

    gestor.checkout("principal")

    assert gestor.merge("trabajo") is True
    assert (repo / "nuevo.py").exists()


def test_un_conflicto_se_reporta_como_fallo(repo: Path) -> None:
    """Quien llame tiene que enterarse, no seguir como si nada."""
    gestor = BranchManager(repo)
    gestor.create("trabajo")

    (repo / "modulo.py").write_text("valor = 2\n", encoding="utf-8")
    git(repo, "commit", "-am", "en la rama")

    gestor.checkout("principal")
    (repo / "modulo.py").write_text("valor = 3\n", encoding="utf-8")
    git(repo, "commit", "-am", "en principal")

    assert gestor.merge("trabajo") is False


def test_fusionar_una_rama_inexistente_falla(repo: Path) -> None:
    assert BranchManager(repo).merge("inventada") is False
