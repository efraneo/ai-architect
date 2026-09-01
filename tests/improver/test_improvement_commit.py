"""The improvement flow can commit on its own -- with three guards.

``git/`` was orphaned: four modules that nobody called. The architect
generated the patch and left it there, so the cycle never closed.

Committing **modifies the user's repository**, so this is opt-in and every
guard has its own test. Failing towards "do not commit" is the only safe
direction, and that is what these tests protect.

No test touches a real repository: ``GitManager`` is injected.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from ai_architect.improver.improvement_engine import (
    ImprovementEngine,
    auto_commit_activo,
)
from ai_architect.memory.memory_engine import MemoryEngine

DIFF = """--- a/modulo.py
+++ b/modulo.py
@@ -1 +1 @@
-valor = 1
+valor = 2
"""


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "modulo.py").write_text("valor = 1\n", encoding="utf-8")
    return tmp_path


def git_falso(*, es_repo: bool = True, aplica: bool = True, commitea: bool = True):
    git = mock.Mock()
    git.is_repository = mock.Mock(return_value=es_repo)
    git.apply_patch = mock.Mock(return_value=aplica)
    git.commit = mock.Mock(return_value=commitea)
    return git


def motor_con(tmp_path: Path, git=None, aprueba: bool = True) -> ImprovementEngine:
    motor = ImprovementEngine(
        memory=MemoryEngine(storage=tmp_path / "memoria.json"),
        git=git or git_falso(),
    )
    motor.provider.generate = mock.Mock(return_value=DIFF)  # type: ignore[method-assign]
    motor.decision.decide = mock.Mock(  # type: ignore[method-assign]
        return_value={
            "approved": aprueba,
            "confidence": 0.9,
            "decision": "ACCEPT" if aprueba else "REJECT",
        }
    )
    return motor


# --- El interruptor ---------------------------------------------------------


def test_por_defecto_el_auto_commit_esta_apagado() -> None:
    """Committing without being asked would be the worst default."""
    with mock.patch.dict(os.environ, {}, clear=True):
        assert auto_commit_activo() is False


@pytest.mark.parametrize("valor", ["true", "TRUE", " True "])
def test_se_enciende_con_true_en_cualquier_forma(valor: str) -> None:
    with mock.patch.dict(os.environ, {"AUTO_COMMIT": valor}):
        assert auto_commit_activo() is True


@pytest.mark.parametrize("valor", ["false", "no", "0", "", "si"])
def test_cualquier_otro_valor_lo_deja_apagado(valor: str) -> None:
    with mock.patch.dict(os.environ, {"AUTO_COMMIT": valor}):
        assert auto_commit_activo() is False


# --- Guarda 1: el interruptor -----------------------------------------------


def test_sin_auto_commit_no_toca_el_repositorio(repo: Path, tmp_path: Path) -> None:
    git = git_falso()
    motor = motor_con(tmp_path, git=git)

    with mock.patch.dict(os.environ, {"AUTO_COMMIT": "false"}):
        resultado = motor.improve(repo, instruction="algo")

    assert resultado["committed"] is False
    assert "AUTO_COMMIT" in resultado["commit_reason"]
    git.apply_patch.assert_not_called()
    git.commit.assert_not_called()


# --- Guarda 2: la aprobación ------------------------------------------------


def test_un_parche_no_aprobado_no_se_commitea(repo: Path, tmp_path: Path) -> None:
    """Even with the switch on: what the decision engine rejects does not land."""
    git = git_falso()
    motor = motor_con(tmp_path, git=git, aprueba=False)

    with mock.patch.dict(os.environ, {"AUTO_COMMIT": "true"}):
        resultado = motor.improve(repo, instruction="algo")

    assert resultado["committed"] is False
    assert "no fue aprobado" in resultado["commit_reason"]
    git.commit.assert_not_called()


# --- Guarda 3: que sea un repositorio git -----------------------------------


def test_si_no_es_un_repositorio_git_no_commitea(repo: Path, tmp_path: Path) -> None:
    git = git_falso(es_repo=False)
    motor = motor_con(tmp_path, git=git)

    with mock.patch.dict(os.environ, {"AUTO_COMMIT": "true"}):
        resultado = motor.improve(repo, instruction="algo")

    assert resultado["committed"] is False
    assert "repositorio git" in resultado["commit_reason"]
    git.apply_patch.assert_not_called()


# --- El camino feliz --------------------------------------------------------


def test_con_las_tres_condiciones_commitea(repo: Path, tmp_path: Path) -> None:
    git = git_falso()
    motor = motor_con(tmp_path, git=git)

    with mock.patch.dict(os.environ, {"AUTO_COMMIT": "true"}):
        resultado = motor.improve(repo, instruction="extraer el validador")

    assert resultado["committed"] is True
    git.apply_patch.assert_called_once()
    git.commit.assert_called_once()


def test_el_mensaje_del_commit_lleva_la_instruccion(repo: Path, tmp_path: Path) -> None:
    git = git_falso()
    motor = motor_con(tmp_path, git=git)

    with mock.patch.dict(os.environ, {"AUTO_COMMIT": "true"}):
        motor.improve(repo, instruction="extraer el validador")

    mensaje = git.commit.call_args.args[0]

    assert "AI Architect" in mensaje
    assert "extraer el validador" in mensaje


# --- Los fallos no rompen la mejora -----------------------------------------


def test_si_el_parche_no_aplica_la_mejora_sigue_en_pie(
    repo: Path, tmp_path: Path
) -> None:
    """The patch is already saved on disk: it can be applied by hand."""
    motor = motor_con(tmp_path, git=git_falso(aplica=False))

    with mock.patch.dict(os.environ, {"AUTO_COMMIT": "true"}):
        resultado = motor.improve(repo, instruction="algo")

    assert resultado["success"] is True
    assert resultado["committed"] is False
    assert "no se pudo aplicar" in resultado["commit_reason"]


def test_si_el_commit_falla_la_mejora_sigue_en_pie(repo: Path, tmp_path: Path) -> None:
    motor = motor_con(tmp_path, git=git_falso(commitea=False))

    with mock.patch.dict(os.environ, {"AUTO_COMMIT": "true"}):
        resultado = motor.improve(repo, instruction="algo")

    assert resultado["success"] is True
    assert resultado["committed"] is False


def test_una_excepcion_de_git_queda_recogida(repo: Path, tmp_path: Path) -> None:
    git = git_falso()
    git.apply_patch = mock.Mock(side_effect=RuntimeError("git no instalado"))
    motor = motor_con(tmp_path, git=git)

    with mock.patch.dict(os.environ, {"AUTO_COMMIT": "true"}):
        resultado = motor.improve(repo, instruction="algo")

    assert resultado["success"] is True
    assert resultado["committed"] is False
    assert "git no instalado" in resultado["commit_reason"]


# --- Queda registrado -------------------------------------------------------


def test_la_memoria_anota_si_se_commiteo(repo: Path, tmp_path: Path) -> None:
    motor = motor_con(tmp_path)

    with mock.patch.dict(os.environ, {"AUTO_COMMIT": "true"}):
        motor.improve(repo, instruction="algo")

    assert motor.memory.store.last(1)[0].metadata["committed"] is True
