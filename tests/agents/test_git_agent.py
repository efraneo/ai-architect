"""El agente de git, que ahora lee el estado como todo el mundo.

Tenía su propia lectura de ``git status``: contaba solo las líneas que
empiezan por ``" M"`` o ``"M "`` —perdiéndose los ``MM`` y los ``AM``—, no
veía renombrados ni conflictos, y llamaba a git **dos veces** para el mismo
estado (``_modified()`` y ``_untracked()`` ejecutaban ``_status()`` cada uno).

Ahora usa ``git/status_manager.py``, el mismo que usa ``GitManager``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest import mock

import pytest

from ai_architect.agents.git_agent import GitAgent


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


def test_fuera_de_un_repositorio_lo_dice(tmp_path: Path) -> None:
    informe = GitAgent().review(str(tmp_path))

    assert informe["git"] is False
    assert informe["status"] == "NOT_A_GIT_REPOSITORY"


def test_reporta_la_rama_y_el_ultimo_commit(repo: Path) -> None:
    informe = GitAgent().review(str(repo))

    assert informe["branch"] == "principal"
    assert "primero" in informe["last_commit"]


def test_un_repositorio_limpio(repo: Path) -> None:
    informe = GitAgent().review(str(repo))

    assert informe["clean"] is True
    assert informe["pending"] == 0


def test_cuenta_lo_modificado_y_lo_no_seguido(repo: Path) -> None:
    (repo / "modulo.py").write_text("valor = 2\n", encoding="utf-8")
    (repo / "nuevo.py").write_text("x = 1\n", encoding="utf-8")

    informe = GitAgent().review(str(repo))

    assert informe["modified"] == 1
    assert informe["untracked"] == 1
    assert informe["pending"] == 2


def test_ve_los_anadidos_y_modificados(repo: Path) -> None:
    """La regresión: ``AM`` no lo contaba como modificado."""
    (repo / "nuevo.py").write_text("x = 1\n", encoding="utf-8")
    git(repo, "add", "nuevo.py")
    (repo / "nuevo.py").write_text("x = 2\n", encoding="utf-8")

    informe = GitAgent().review(str(repo))

    assert informe["created"] == 1
    assert informe["modified"] == 1


def test_ve_los_renombrados(repo: Path) -> None:
    git(repo, "mv", "modulo.py", "otro.py")

    assert GitAgent().review(str(repo))["renamed"] == 1


def test_un_conflicto_es_un_hallazgo(repo: Path) -> None:
    """No es una estadística: hay que resolverlo antes de parchear encima."""
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

    informe = GitAgent().review(str(repo))

    assert informe["conflicted"] == 1
    assert informe["findings"][0]["type"] == "conflicto"


def test_sin_conflictos_no_hay_hallazgos(repo: Path) -> None:
    assert "findings" not in GitAgent().review(str(repo))


def test_reporta_la_ultima_etiqueta(repo: Path) -> None:
    git(repo, "tag", "v1.0.0")

    assert GitAgent().review(str(repo))["latest_tag"] == "v1.0.0"


def test_sin_rama_remota_no_hay_adelanto_ni_retraso(repo: Path) -> None:
    """Es lo normal en una rama recién creada: cero y cero, no un error."""
    informe = GitAgent().review(str(repo))

    assert informe["ahead"] == 0
    assert informe["behind"] == 0


def test_el_estado_se_lee_una_sola_vez(repo: Path) -> None:
    """La regresión: ``_modified()`` y ``_untracked()`` llamaban cada uno a
    ``_status()``, lanzando git dos veces para lo mismo."""
    with mock.patch(
        "ai_architect.git.status_manager.StatusManager.status",
        wraps=lambda: None,
    ) as leer:
        leer.return_value = mock.Mock(
            branch="principal",
            clean=True,
            modified=[],
            created=[],
            deleted=[],
            renamed=[],
            untracked=[],
            conflicted=[],
            total=0,
        )

        GitAgent().review(str(repo))

    assert leer.call_count == 1
