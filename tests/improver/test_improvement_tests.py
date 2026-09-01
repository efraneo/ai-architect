"""The improvement flow runs the target project's suite before deciding.

``test_runner/`` was orphaned, and the flow passed structural validity to the
decision engine dressed up as a test result:

    tests_ok=bool(structurally_valid)

So the engine believed the tests had passed when nothing had been run. That
is the weakest link in the cycle, and this closes it.

``TestRunner`` is injected: no test spawns a real pytest inside this one.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest

from ai_architect.improver.improvement_engine import (
    ImprovementEngine,
    run_tests_activo,
)
from ai_architect.memory.memory_engine import MemoryEngine

DIFF = """--- a/modulo.py
+++ b/modulo.py
@@ -1 +1 @@
-valor = 1
+valor = 2
"""


def runner_falso(exito: bool = True, pasadas: int = 10, fallidas: int = 0):
    runner = mock.Mock()
    runner.run = mock.Mock(
        return_value=mock.Mock(
            success=exito,
            passed=pasadas,
            failed=fallidas,
            duration=0.1,
        )
    )
    return runner


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "modulo.py").write_text("valor = 1\n", encoding="utf-8")
    return tmp_path


def motor_con(tmp_path: Path, runner=None) -> ImprovementEngine:
    motor = ImprovementEngine(
        memory=MemoryEngine(storage=tmp_path / "memoria.json"),
        tests=runner or runner_falso(),
    )
    motor.provider.generate = mock.Mock(return_value=DIFF)  # type: ignore[method-assign]
    return motor


# --- El interruptor ---------------------------------------------------------


def test_las_pruebas_se_ejecutan_por_defecto() -> None:
    """Unlike auto-commit, running tests is safe and adds information."""
    with mock.patch.dict(os.environ, {}, clear=True):
        assert run_tests_activo() is True


def test_se_pueden_apagar() -> None:  # para suites muy lentas
    with mock.patch.dict(os.environ, {"RUN_TESTS": "false"}):
        assert run_tests_activo() is False


# --- Se ejecutan de verdad --------------------------------------------------


def test_la_suite_del_proyecto_se_ejecuta(repo: Path, tmp_path: Path) -> None:
    runner = runner_falso()
    motor = motor_con(tmp_path, runner)

    with mock.patch.dict(os.environ, {"RUN_TESTS": "true"}):
        motor.improve(repo, instruction="algo")

    runner.run.assert_called_once_with(repo.resolve())


def test_el_resultado_trae_lo_que_paso_con_las_pruebas(
    repo: Path, tmp_path: Path
) -> None:
    motor = motor_con(tmp_path, runner_falso(exito=True, pasadas=42))

    with mock.patch.dict(os.environ, {"RUN_TESTS": "true"}):
        resultado = motor.improve(repo, instruction="algo")

    assert resultado["tests"]["executed"] is True
    assert resultado["tests"]["success"] is True
    assert resultado["tests"]["passed"] == 42


def test_apagadas_no_se_ejecutan_ni_se_dan_por_buenas(
    repo: Path, tmp_path: Path
) -> None:
    """Not running them cannot count as passing."""
    runner = runner_falso()
    motor = motor_con(tmp_path, runner)

    with mock.patch.dict(os.environ, {"RUN_TESTS": "false"}):
        resultado = motor.improve(repo, instruction="algo")

    runner.run.assert_not_called()
    assert resultado["tests"]["executed"] is False
    assert resultado["tests"]["success"] is False
    assert "RUN_TESTS" in resultado["tests"]["reason"]


# --- Lo que llega al motor de decisión --------------------------------------


def test_la_decision_recibe_el_resultado_real_de_las_pruebas(
    repo: Path, tmp_path: Path
) -> None:
    """The regression: it used to receive structural validity instead."""
    motor = motor_con(tmp_path, runner_falso(exito=False, fallidas=3))
    espia = mock.Mock(return_value={"approved": False, "confidence": 0.1})
    motor.decision.decide = espia  # type: ignore[method-assign]

    with mock.patch.dict(os.environ, {"RUN_TESTS": "true"}):
        motor.improve(repo, instruction="algo")

    assert espia.call_args.kwargs["tests_ok"] is False


def test_con_la_suite_en_verde_la_decision_lo_sabe(repo: Path, tmp_path: Path) -> None:
    motor = motor_con(tmp_path, runner_falso(exito=True))
    espia = mock.Mock(return_value={"approved": True, "confidence": 0.9})
    motor.decision.decide = espia  # type: ignore[method-assign]

    with mock.patch.dict(os.environ, {"RUN_TESTS": "true"}):
        motor.improve(repo, instruction="algo")

    assert espia.call_args.kwargs["tests_ok"] is True


def test_la_validez_estructural_sigue_llegando_pero_como_lo_que_es(
    repo: Path, tmp_path: Path
) -> None:
    """It is still useful information -- just not a test result."""
    motor = motor_con(tmp_path)
    espia = mock.Mock(return_value={"approved": True, "confidence": 0.9})
    motor.decision.decide = espia  # type: ignore[method-assign]

    with mock.patch.dict(os.environ, {"RUN_TESTS": "true"}):
        motor.improve(repo, instruction="algo")

    assert "structurally_valid" in espia.call_args.kwargs["task"]


# --- Los fallos no rompen la mejora -----------------------------------------


def test_si_la_suite_no_se_puede_ejecutar_la_mejora_sigue(
    repo: Path, tmp_path: Path
) -> None:
    """Someone else's suite can do anything, including refusing to start."""
    runner = mock.Mock()
    runner.run = mock.Mock(side_effect=RuntimeError("pytest no instalado"))
    motor = motor_con(tmp_path, runner)

    with mock.patch.dict(os.environ, {"RUN_TESTS": "true"}):
        resultado = motor.improve(repo, instruction="algo")

    assert resultado["success"] is True
    assert resultado["tests"]["executed"] is False
    assert "pytest no instalado" in resultado["tests"]["reason"]


def test_un_fallo_al_ejecutar_no_cuenta_como_exito(repo: Path, tmp_path: Path) -> None:
    runner = mock.Mock()
    runner.run = mock.Mock(side_effect=RuntimeError("lo que sea"))
    motor = motor_con(tmp_path, runner)
    espia = mock.Mock(return_value={"approved": False, "confidence": 0.0})
    motor.decision.decide = espia  # type: ignore[method-assign]

    with mock.patch.dict(os.environ, {"RUN_TESTS": "true"}):
        motor.improve(repo, instruction="algo")

    assert espia.call_args.kwargs["tests_ok"] is False


# --- Modificar y volver a ejecutar ------------------------------------------


def test_sin_apply_las_pruebas_siguen_siendo_las_de_antes(
    repo: Path, tmp_path: Path
) -> None:
    """El comportamiento de siempre: no se toca el árbol de trabajo."""
    motor = motor_con(tmp_path, runner_falso(exito=True))

    with mock.patch.dict(os.environ, {"RUN_TESTS": "true"}):
        resultado = motor.improve(repo, instruction="algo")

    assert resultado["verification"] is None
    assert (repo / "modulo.py").read_text(encoding="utf-8") == "valor = 1\n"


def test_con_apply_se_verifica(repo: Path, tmp_path: Path) -> None:
    motor = motor_con(tmp_path, runner_falso(exito=True))
    espia = mock.Mock(
        return_value={
            "applied": True,
            "reverted": False,
            "reason": "ok",
            "tests_before": {"success": True},
            "tests": {"executed": True, "success": True, "failed": 0},
        }
    )

    with mock.patch(
        "ai_architect.improver.improvement_engine.verificar",
        espia,
    ):
        with mock.patch.dict(os.environ, {"RUN_TESTS": "true"}):
            resultado = motor.improve(repo, instruction="algo", apply=True)

    espia.assert_called_once()
    assert resultado["verification"]["applied"] is True


def test_la_decision_recibe_las_pruebas_de_despues(repo: Path, tmp_path: Path) -> None:
    """El fallo que esto arregla: `tests_ok` decía que el repositorio estaba
    en verde ANTES del cambio, no que el cambio fuera bueno."""
    motor = motor_con(tmp_path, runner_falso(exito=True))
    decision = mock.Mock(return_value={"approved": False, "confidence": 0.1})
    motor.decision.decide = decision  # type: ignore[method-assign]

    with mock.patch(
        "ai_architect.improver.improvement_engine.verificar",
        return_value={
            "applied": True,
            "reverted": True,
            "reason": "rompe las pruebas",
            "tests_before": {"executed": True, "success": True},
            "tests": {"executed": True, "success": False, "failed": 3},
        },
    ):
        with mock.patch.dict(os.environ, {"RUN_TESTS": "true"}):
            motor.improve(repo, instruction="algo", apply=True)

    assert decision.call_args.kwargs["tests_ok"] is False
