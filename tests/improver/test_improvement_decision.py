"""The improvement flow asks the decision engine whether to approve.

``decision_engine/`` was fully orphaned: ten modules that nobody called. The
improvement flow had a hardcoded ``patch.approved = False`` with the comment
"Structural validation is not approval" -- a declared gap where the engine
was meant to go.

Now the decision comes from the engine, and these tests pin down that
``approved`` really depends on it and not on a constant.
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


def runner_falso(exito: bool = True):
    """A TestRunner that does not spawn a real pytest inside this one."""
    runner = mock.Mock()
    runner.run = mock.Mock(
        return_value=mock.Mock(
            success=exito,
            passed=10 if exito else 7,
            failed=0 if exito else 3,
            duration=0.1,
        )
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


def test_el_motor_de_decision_esta_enganchado(motor: ImprovementEngine) -> None:
    """It used to be built and never called."""
    assert motor.decision is not None


def test_la_decision_viaja_en_el_resultado(
    motor: ImprovementEngine, repo: Path
) -> None:
    resultado = motor.improve(repo, instruction="algo")

    assert isinstance(resultado["decision"], dict)
    assert "approved" in resultado["decision"]
    assert "confidence" in resultado["decision"]


def test_se_consulta_al_motor_con_el_contexto_de_la_mejora(
    motor: ImprovementEngine, repo: Path
) -> None:
    """It must receive the metrics and findings, not be called empty."""
    espia = mock.Mock(return_value={"approved": True, "confidence": 0.8})
    motor.decision.decide = espia  # type: ignore[method-assign]

    motor.improve(repo, instruction="extraer el validador")

    argumentos = espia.call_args.kwargs

    assert argumentos["repository"] == str(repo.resolve())
    assert argumentos["task"]["instruction"] == "extraer el validador"
    assert "metrics" in argumentos
    assert "findings" in argumentos


def test_si_el_motor_aprueba_el_parche_queda_aprobado(
    motor: ImprovementEngine, repo: Path
) -> None:
    """The regression: ``approved`` used to be a hardcoded False."""
    motor.decision.decide = mock.Mock(  # type: ignore[method-assign]
        return_value={"approved": True, "confidence": 0.9, "decision": "ACCEPT"}
    )

    resultado = motor.improve(repo, instruction="algo")

    assert resultado["approved"] is True


def test_si_el_motor_rechaza_el_parche_no_queda_aprobado(
    motor: ImprovementEngine, repo: Path
) -> None:
    motor.decision.decide = mock.Mock(  # type: ignore[method-assign]
        return_value={"approved": False, "confidence": 0.1, "decision": "REJECT"}
    )

    resultado = motor.improve(repo, instruction="algo")

    assert resultado["approved"] is False


def test_una_decision_sin_el_campo_no_aprueba(
    motor: ImprovementEngine, repo: Path
) -> None:
    """Approving by default would be the dangerous direction to fail in."""
    motor.decision.decide = mock.Mock(return_value={})  # type: ignore[method-assign]

    assert motor.improve(repo, instruction="algo")["approved"] is False


def test_la_confianza_de_la_decision_llega_a_la_memoria(
    motor: ImprovementEngine, repo: Path
) -> None:
    motor.decision.decide = mock.Mock(  # type: ignore[method-assign]
        return_value={"approved": True, "confidence": 0.73, "decision": "ACCEPT"}
    )

    motor.improve(repo, instruction="algo")

    assert motor.memory.store.last(1)[0].confidence == 0.73


def test_la_memoria_registra_la_decision_tomada(
    motor: ImprovementEngine, repo: Path
) -> None:
    """So a later run can look at what was decided and how it went."""
    motor.decision.decide = mock.Mock(  # type: ignore[method-assign]
        return_value={"approved": True, "confidence": 0.9, "decision": "ACCEPT"}
    )

    motor.improve(repo, instruction="algo")

    metadatos = motor.memory.store.last(1)[0].metadata

    assert metadatos["decision"] == "ACCEPT"
    assert metadatos["approved"] is True
