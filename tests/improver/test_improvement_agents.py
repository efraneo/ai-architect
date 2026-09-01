"""The improvement flow asks the static agents before deciding.

``agents/`` was orphaned: thirty-four modules and an ``AgentManager`` that
nobody instantiated. The decision engine received only the analyzer's
findings, so a leaked secret or a missing licence never weighed on whether
a patch was approved.

Only the free half is wired in: ``inspect()``, not ``execute()``. Running
the five AI agents on every improvement would mean five extra provider
calls per run.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from ai_architect.improver.improvement_engine import ImprovementEngine
from ai_architect.memory.memory_engine import MemoryEngine

DIFF = """--- a/modulo.py
+++ b/modulo.py
@@ -1 +1 @@
-valor = 1
+valor = 2
"""


def runner_falso():
    """A TestRunner that does not spawn a real pytest inside this one."""
    runner = mock.Mock()
    runner.run = mock.Mock(
        return_value=mock.Mock(success=True, passed=10, failed=0, duration=0.1)
    )
    return runner


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "modulo.py").write_text("valor = 1\n", encoding="utf-8")
    return tmp_path


@pytest.fixture
def motor(tmp_path: Path) -> ImprovementEngine:
    motor = ImprovementEngine(
        memory=MemoryEngine(storage=tmp_path / "memoria.json"),
        tests=runner_falso(),
    )
    motor.provider.generate = mock.Mock(return_value=DIFF)  # type: ignore[method-assign]
    return motor


def test_el_gestor_de_agentes_esta_enganchado(motor: ImprovementEngine) -> None:
    """It used to be a package nobody built."""
    assert motor.agents is not None


def test_se_inspecciona_el_repositorio(motor: ImprovementEngine, repo: Path) -> None:
    espia = mock.Mock(return_value={})
    motor.agents.inspect = espia  # type: ignore[method-assign]

    motor.improve(repo, instruction="algo")

    espia.assert_called_once_with(str(repo.resolve()))


def test_no_se_llama_a_los_agentes_de_ia(motor: ImprovementEngine, repo: Path) -> None:
    """Five extra provider calls on every improvement is not acceptable."""
    espia = mock.Mock()
    motor.agents.execute = espia  # type: ignore[method-assign]

    motor.improve(repo, instruction="algo")

    espia.assert_not_called()


def test_la_inspeccion_viaja_en_el_resultado(
    motor: ImprovementEngine, repo: Path
) -> None:
    resultado = motor.improve(repo, instruction="algo")

    assert "security" in resultado["agents"]
    assert "dependencies" in resultado["agents"]


def test_los_hallazgos_llegan_al_motor_de_decision(
    motor: ImprovementEngine, repo: Path
) -> None:
    """The point of connecting them: a leaked secret weighs on the decision."""
    (repo / "config.py").write_text('password = "hunter2"\n', encoding="utf-8")

    espia = mock.Mock(return_value={"approved": True, "confidence": 0.8})
    motor.decision.decide = espia  # type: ignore[method-assign]

    motor.improve(repo, instruction="algo")

    hallazgos = espia.call_args.kwargs["findings"]

    assert any("Password Assignment" in str(h) for h in hallazgos)


def test_los_del_analizador_siguen_llegando(
    motor: ImprovementEngine, repo: Path
) -> None:
    """The agents add to them; they do not replace them."""
    motor.recommendations = mock.Mock(return_value=["del analizador"])  # type: ignore[method-assign]
    espia = mock.Mock(return_value={"approved": True, "confidence": 0.8})
    motor.decision.decide = espia  # type: ignore[method-assign]

    motor.improve(repo, instruction="algo")

    assert "del analizador" in espia.call_args.kwargs["findings"]


def test_si_la_inspeccion_falla_la_mejora_sigue(
    motor: ImprovementEngine, repo: Path
) -> None:
    """Inspecting is secondary: the patch does not depend on it."""
    motor.agents.inspect = mock.Mock(  # type: ignore[method-assign]
        side_effect=RuntimeError("se rompió")
    )

    resultado = motor.improve(repo, instruction="algo")

    assert resultado["success"] is True
    assert resultado["agents"] == {"error": "se rompió"}


def test_una_inspeccion_rota_no_inventa_hallazgos(
    motor: ImprovementEngine, repo: Path
) -> None:
    motor.agents.inspect = mock.Mock(side_effect=RuntimeError("x"))  # type: ignore[method-assign]
    espia = mock.Mock(return_value={"approved": True, "confidence": 0.8})
    motor.decision.decide = espia  # type: ignore[method-assign]

    motor.recommendations = mock.Mock(return_value=[])  # type: ignore[method-assign]

    motor.improve(repo, instruction="algo")

    assert espia.call_args.kwargs["findings"] == []


def test_se_puede_inyectar_otro_gestor(tmp_path: Path, repo: Path) -> None:
    """So a test does not have to walk a real tree."""
    gestor = mock.Mock()
    gestor.inspect = mock.Mock(return_value={"security": {"status": "OK"}})
    gestor.findings_de = mock.Mock(return_value=[])

    motor = ImprovementEngine(
        memory=MemoryEngine(storage=tmp_path / "memoria.json"),
        tests=runner_falso(),
        agents=gestor,
    )
    motor.provider.generate = mock.Mock(return_value=DIFF)  # type: ignore[method-assign]

    motor.improve(repo, instruction="algo")

    gestor.inspect.assert_called_once()
