"""The improvement flow records what it does in memory.

``memory/`` was built but nobody called it: the CLI never reached it, so the
architect could not learn from previous runs. This wires ``MemoryEngine``
into ``ImprovementEngine.improve()`` and pins down that it happens.

The provider is faked: no test hits an LLM.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from ai_architect.improver.improvement_engine import ImprovementEngine
from ai_architect.memory.memory_engine import MemoryEngine
from ai_architect.memory.models import ExperienceOutcome

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
    """An engine whose memory writes into the temporary directory."""
    memoria = MemoryEngine(storage=tmp_path / "memoria.json")
    motor = ImprovementEngine(memory=memoria, tests=runner_falso())
    motor.provider.generate = mock.Mock(return_value=DIFF)  # type: ignore[method-assign]
    return motor


def test_una_mejora_queda_registrada_en_la_memoria(
    motor: ImprovementEngine, repo: Path
) -> None:
    """The point of connecting it: the run stops being forgotten."""
    assert motor.memory.statistics()["experiences"] == 0

    motor.improve(repo, instruction="subir el valor")

    assert motor.memory.statistics()["experiences"] == 1


def test_el_registro_guarda_la_instruccion_y_el_repositorio(
    motor: ImprovementEngine, repo: Path
) -> None:
    motor.improve(repo, instruction="extraer el validador")

    experiencia = motor.memory.store.last(1)[0]

    assert experiencia.instruction == "extraer el validador"
    assert experiencia.repository == str(repo.resolve())


def test_el_registro_anota_el_proveedor_usado(
    motor: ImprovementEngine, repo: Path
) -> None:
    motor.improve(repo, instruction="algo")

    assert motor.memory.store.last(1)[0].provider == motor.provider.name


def test_el_archivo_apuntado_queda_en_el_registro(
    motor: ImprovementEngine, repo: Path
) -> None:
    motor.improve(repo, instruction="algo", file="modulo.py")

    assert motor.memory.store.last(1)[0].filename == "modulo.py"


def test_los_metadatos_llevan_el_parche_y_la_duracion(
    motor: ImprovementEngine, repo: Path
) -> None:
    resultado = motor.improve(repo, instruction="algo")

    metadatos = motor.memory.store.last(1)[0].metadata

    assert metadatos["patch_id"] == resultado["patch_id"]
    assert metadatos["duration"] == resultado["duration"]
    assert "files" in metadatos
    assert "tasks" in metadatos


def test_el_resultado_devuelve_el_identificador_de_la_experiencia(
    motor: ImprovementEngine, repo: Path
) -> None:
    resultado = motor.improve(repo, instruction="algo")

    assert resultado["experience_id"] == motor.memory.store.last(1)[0].id


def test_la_duracion_se_mide_y_es_positiva(
    motor: ImprovementEngine, repo: Path
) -> None:
    resultado = motor.improve(repo, instruction="algo")

    assert resultado["duration"] >= 0.0


def test_varias_mejoras_se_acumulan(motor: ImprovementEngine, repo: Path) -> None:
    """Memory has to grow: that is what makes learning possible."""
    for i in range(3):
        motor.improve(repo, instruction=f"mejora {i}")

    assert motor.memory.statistics()["experiences"] == 3


def test_lo_registrado_sobrevive_al_proceso(
    motor: ImprovementEngine, repo: Path, tmp_path: Path
) -> None:
    """It persists to disk: a new run must find the previous history."""
    motor.improve(repo, instruction="la primera")

    recargada = MemoryEngine(storage=tmp_path / "memoria.json")

    assert recargada.statistics()["experiences"] == 1


def test_un_repositorio_inexistente_no_registra_nada(
    motor: ImprovementEngine, tmp_path: Path
) -> None:
    """It fails before doing any work: there is no experience to record."""
    resultado = motor.improve(tmp_path / "no-existe", instruction="algo")

    assert resultado["success"] is False
    assert motor.memory.statistics()["experiences"] == 0


def test_si_la_memoria_falla_la_mejora_sigue_adelante(
    motor: ImprovementEngine, repo: Path
) -> None:
    """Recording is secondary: the patch is already generated and saved."""
    motor.memory.record = mock.Mock(  # type: ignore[method-assign]
        side_effect=RuntimeError("disco lleno")
    )

    resultado = motor.improve(repo, instruction="algo")

    assert resultado["success"] is True
    assert resultado["patch_id"]
    assert resultado["experience_id"] is None


def test_el_resultado_se_marca_como_exito_cuando_el_parche_es_valido(
    motor: ImprovementEngine, repo: Path
) -> None:
    motor.improve(repo, instruction="algo")

    assert motor.memory.store.last(1)[0].outcome == ExperienceOutcome.SUCCESS
