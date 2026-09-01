"""Lo que pasa cuando la ejecución real sale mal.

Probando qué devuelve un modelo cuando no colabora, y qué pasa con el
proveedor caído, salieron dos cosas:

    sin cuota    REVIENTA: RuntimeError: insufficient_quota
    sin red      REVIENTA: ConnectionError: no route to host
    clave mala   REVIENTA: PermissionError: invalid api key

Los tres fallos más comunes del mundo real escapaban como excepción cruda,
saltándose todo lo que venía después — incluido dejar constancia en memoria.
El arquitecto no se enteraba de que sus ejecuciones estaban fallando.

Y un parche con cabeceras pero sin una sola línea movida se reportaba como
``success=True`` con un archivo: el ciclo autónomo creería que hizo algo.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from ai_architect.improver.improvement_engine import ImprovementEngine
from ai_architect.memory.memory_engine import MemoryEngine

CAMBIA = """--- a/modulo.py
+++ b/modulo.py
@@ -1 +1 @@
-valor = 1
+valor = 2
"""

SIN_CAMBIOS = "--- a/modulo.py\n+++ b/modulo.py\n"


def runner_falso():
    runner = mock.Mock()
    runner.run = mock.Mock(
        return_value=mock.Mock(success=True, passed=1, failed=0, duration=0.1)
    )
    return runner


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "modulo.py").write_text("valor = 1\n", encoding="utf-8")
    return tmp_path


@pytest.fixture
def motor(tmp_path: Path) -> ImprovementEngine:
    return ImprovementEngine(
        memory=MemoryEngine(storage=tmp_path / "memoria.json"),
        tests=runner_falso(),
    )


# --- El proveedor falla -----------------------------------------------------


@pytest.mark.parametrize(
    "fallo",
    [
        RuntimeError("insufficient_quota"),
        ConnectionError("no route to host"),
        PermissionError("invalid api key"),
        TimeoutError("timed out"),
    ],
)
def test_un_proveedor_caido_no_revienta(
    motor: ImprovementEngine, repo: Path, fallo: Exception
) -> None:
    """La regresión: la excepción se escapaba de `improve()`."""
    motor.provider.generate = mock.Mock(side_effect=fallo)  # type: ignore[method-assign]

    resultado = motor.improve(repo, instruction="algo")

    assert resultado["success"] is False


def test_el_error_dice_qué_pasó(motor: ImprovementEngine, repo: Path) -> None:
    motor.provider.generate = mock.Mock(  # type: ignore[method-assign]
        side_effect=RuntimeError("insufficient_quota")
    )

    resultado = motor.improve(repo, instruction="algo")

    assert "el proveedor falló" in resultado["error"]
    assert "insufficient_quota" in resultado["error"]


def test_el_intento_fallido_queda_registrado(
    motor: ImprovementEngine, repo: Path
) -> None:
    """Si el proveedor lleva cinco ejecuciones fallando, eso es justo lo que
    el arquitecto tiene que saber la próxima vez."""
    motor.provider.generate = mock.Mock(side_effect=RuntimeError("x"))  # type: ignore[method-assign]

    motor.improve(repo, instruction="algo")

    assert motor.memory.statistics()["experiences"] == 1


def test_el_registro_dice_que_fue_un_fracaso(
    motor: ImprovementEngine, repo: Path
) -> None:
    from ai_architect.memory.models import ExperienceOutcome

    motor.provider.generate = mock.Mock(side_effect=RuntimeError("x"))  # type: ignore[method-assign]

    motor.improve(repo, instruction="algo")

    experiencia = motor.memory.store.last(1)[0]

    assert experiencia.outcome == ExperienceOutcome.FAILURE
    assert "x" in experiencia.metadata["error"]


def test_no_se_toca_nada_si_el_proveedor_falla(
    motor: ImprovementEngine, repo: Path
) -> None:
    motor.provider.generate = mock.Mock(side_effect=RuntimeError("x"))  # type: ignore[method-assign]

    resultado = motor.improve(repo, instruction="algo", apply=True)

    assert resultado["working_tree"] == "untouched"
    assert (repo / "modulo.py").read_text(encoding="utf-8") == "valor = 1\n"


def test_si_ni_la_memoria_funciona_el_fallo_sigue_saliendo(
    motor: ImprovementEngine, repo: Path
) -> None:
    """Lo que importa es devolver el fallo, no anotarlo."""
    motor.provider.generate = mock.Mock(side_effect=RuntimeError("x"))  # type: ignore[method-assign]
    motor.memory.record = mock.Mock(side_effect=OSError("disco lleno"))  # type: ignore[method-assign]

    resultado = motor.improve(repo, instruction="algo")

    assert resultado["success"] is False
    assert resultado["experience_id"] is None


# --- Un parche que no cambia nada -------------------------------------------


def test_un_parche_sin_cambios_no_es_un_exito(
    motor: ImprovementEngine, repo: Path
) -> None:
    """La regresión: `success=True` con un archivo, sin mover una línea."""
    motor.provider.generate = mock.Mock(return_value=SIN_CAMBIOS)  # type: ignore[method-assign]

    resultado = motor.improve(repo, instruction="algo")

    assert resultado["success"] is False
    assert "no cambia ni una línea" in resultado["error"]


def test_un_parche_con_cambios_si_lo_es(motor: ImprovementEngine, repo: Path) -> None:
    motor.provider.generate = mock.Mock(return_value=CAMBIA)  # type: ignore[method-assign]

    assert motor.improve(repo, instruction="algo")["success"] is True


# --- Lo que devuelve un modelo que no colabora ------------------------------


@pytest.mark.parametrize(
    "respuesta",
    [
        "Claro, aquí tienes la mejora que pides:\n\nDeberías extraer el validador.",
        "No puedo ayudarte con eso.",
        "",
        "   \n\n  ",
        '{"patch": "algo"}',
    ],
)
def test_una_respuesta_que_no_es_un_diff(
    motor: ImprovementEngine, repo: Path, respuesta: str
) -> None:
    """Prosa, una negativa, JSON o nada: ninguna toca el repositorio."""
    motor.provider.generate = mock.Mock(return_value=respuesta)  # type: ignore[method-assign]

    resultado = motor.improve(repo, instruction="algo", apply=True)

    assert resultado["success"] is False
    assert resultado["working_tree"] == "untouched"
    assert (repo / "modulo.py").read_text(encoding="utf-8") == "valor = 1\n"


# --- El formato que devuelven los modelos nuevos ----------------------------
#
# Probado contra gpt-5.5 en una ejecución real: con el prompt pidiendo
# "unified diff format" a secas, devolvió su propio formato de edición.


OTRO_FORMATO = """*** Begin Patch
*** Update File: modulo.py
@@
 valor = 1
+valor = 2
*** End Patch"""


def test_el_formato_apply_patch_se_reconoce(
    motor: ImprovementEngine, repo: Path
) -> None:
    """Antes se rechazaba con "Git rejected the patch", que hace pensar en un
    parche corrupto en vez de en un malentendido de formato."""
    motor.provider.generate = mock.Mock(return_value=OTRO_FORMATO)  # type: ignore[method-assign]

    resultado = motor.improve(repo, instruction="algo")

    assert resultado["success"] is False
    assert "*** Begin Patch" in resultado["error"]
    assert "diff unificado" in resultado["error"]


def test_no_toca_nada_con_ese_formato(motor: ImprovementEngine, repo: Path) -> None:
    motor.provider.generate = mock.Mock(return_value=OTRO_FORMATO)  # type: ignore[method-assign]

    resultado = motor.improve(repo, instruction="algo", apply=True)

    assert resultado["working_tree"] == "untouched"
    assert (repo / "modulo.py").read_text(encoding="utf-8") == "valor = 1\n"
