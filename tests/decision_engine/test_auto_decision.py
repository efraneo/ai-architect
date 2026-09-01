"""``AutoDecision``: la tubería entera, de contexto a veredicto.

Está **conectada** —es lo que hay detrás de ``DecisionEngine.decide()``, que
llama ``ImprovementEngine.improve()`` en cada ejecución— y estaba al 71 %.

Encadena cinco motores: calidad, riesgo, confianza, puntuación y política.
Lo que se fija aquí es que la cadena llega entera hasta el final, y que un
contexto pobre no se convierte en un "sí" por descuido.
"""

from __future__ import annotations

import pytest

from ai_architect.core.context import AIContext
from ai_architect.decision_engine.auto_decision import AutoDecision
from ai_architect.decision_engine.decision_report import DecisionType


@pytest.fixture
def motor() -> AutoDecision:
    return AutoDecision()


def contexto(
    *,
    pruebas_ok: bool = True,
    hallazgos: list[str] | None = None,
    metricas: dict | None = None,
) -> AIContext:
    ctx = AIContext(repository="/proyecto")
    ctx.tests["success"] = pruebas_ok
    ctx.validation["findings"] = list(hallazgos or [])
    ctx.metrics.update(metricas or {})
    return ctx


# --- La cadena llega hasta el final -----------------------------------------


def test_devuelve_un_veredicto(motor: AutoDecision) -> None:
    informe = motor.evaluate(contexto())

    assert isinstance(informe.decision, DecisionType)


def test_el_veredicto_trae_confianza_y_motivo(motor: AutoDecision) -> None:
    informe = motor.evaluate(contexto())

    assert 0.0 <= informe.confidence <= 1.0
    assert informe.reason


def test_el_veredicto_trae_las_metricas_de_la_cadena(motor: AutoDecision) -> None:
    """Si un motor intermedio no aportara, esto vendría vacío."""
    informe = motor.evaluate(contexto())

    assert "score" in informe.metrics
    assert "grade" in informe.metrics
    assert "risk" in informe.metrics


# --- Las pruebas mandan -----------------------------------------------------


def test_sin_pruebas_en_verde_no_se_aprueba(motor: AutoDecision) -> None:
    informe = motor.evaluate(contexto(pruebas_ok=False))

    assert informe.approved is False
    assert informe.decision == DecisionType.REJECT


def test_un_contexto_sin_decir_nada_de_las_pruebas_no_aprueba(
    motor: AutoDecision,
) -> None:
    """Lo que no se sabe, no se aprueba."""
    ctx = AIContext(repository="/proyecto")

    assert motor.evaluate(ctx).approved is False


# --- Los hallazgos pesan ----------------------------------------------------


def test_muchos_hallazgos_no_dan_lo_mismo_que_ninguno(motor: AutoDecision) -> None:
    limpio = motor.evaluate(contexto())
    sucio = motor.evaluate(contexto(hallazgos=[f"hallazgo {i}" for i in range(40)]))

    assert sucio.metrics["score"] <= limpio.metrics["score"]


# --- Las preguntas al informe -----------------------------------------------


def test_las_cuatro_preguntas_son_excluyentes(motor: AutoDecision) -> None:
    informe = motor.evaluate(contexto())

    respuestas = [
        motor.should_commit(informe),
        motor.should_retry(informe),
        motor.requires_review(informe),
        motor.rejected(informe),
    ]

    assert sum(respuestas) == 1


def test_un_rechazo_no_se_commitea(motor: AutoDecision) -> None:
    informe = motor.evaluate(contexto(pruebas_ok=False))

    assert motor.should_commit(informe) is False
    assert motor.rejected(informe) is True


# --- Lo que se puede leer del informe ---------------------------------------


def test_el_resumen_cabe_en_una_linea(motor: AutoDecision) -> None:
    resumen = motor.summary(motor.evaluate(contexto()))

    assert "Grade=" in resumen
    assert "Score=" in resumen
    assert "Confidence=" in resumen


def test_el_diagnostico_es_serializable(motor: AutoDecision) -> None:
    """El resultado se persiste y se imprime como JSON."""
    import json

    datos = motor.diagnostics(motor.evaluate(contexto()))

    assert isinstance(datos, dict)
    assert json.dumps(datos, default=str)


def test_el_diagnostico_dice_que_se_decidio(motor: AutoDecision) -> None:
    datos = motor.diagnostics(motor.evaluate(contexto(pruebas_ok=False)))

    assert datos["approved"] is False
