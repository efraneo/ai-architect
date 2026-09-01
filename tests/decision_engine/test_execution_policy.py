"""``ExecutionPolicy``: la regla que decide si un cambio pasa solo.

Está **conectada** —`DecisionEngine` la usa a través de `AutoDecision`— y es
la que en última instancia deja o no que el arquitecto commitee sin que
nadie mire. Estaba al 69 %.

Lo que se fija aquí es el orden de las reglas, que es lo que importa: las
pruebas mandan sobre todo lo demás, y el riesgo crítico manda sobre la
puntuación. Fallar hacia el "no" es la única dirección segura.
"""

from __future__ import annotations

import pytest

from ai_architect.core.enums import RiskLevel
from ai_architect.decision_engine.confidence_engine import ConfidenceReport
from ai_architect.decision_engine.decision_report import DecisionType
from ai_architect.decision_engine.execution_policy import ExecutionPolicy
from ai_architect.decision_engine.models import RiskAssessment
from ai_architect.decision_engine.scoring_engine import ScoreReport


def puntuacion(valor: float, grado: str = "A") -> ScoreReport:
    return ScoreReport(
        score=valor,
        approved=valor >= 70,
        quality=valor,
        confidence=0.9,
        risk=0.1,
        grade=grado,
        reasons=[],
    )


def confianza(valor: float) -> ConfidenceReport:
    from ai_architect.core.enums import Confidence

    nivel = Confidence.HIGH if valor >= 0.8 else Confidence.LOW

    return ConfidenceReport(value=valor, level=nivel)


def riesgo(nivel: RiskLevel) -> RiskAssessment:
    return RiskAssessment(score=0.5, level=nivel)


@pytest.fixture
def politica() -> ExecutionPolicy:
    return ExecutionPolicy()


def decidir(
    politica: ExecutionPolicy,
    *,
    score: float = 95.0,
    conf: float = 0.95,
    nivel: RiskLevel = RiskLevel.LOW,
    pruebas: bool = True,
) -> DecisionType:
    return politica.evaluate(
        puntuacion(score),
        confianza(conf),
        riesgo(nivel),
        pruebas,
    ).decision


# --- Las pruebas mandan sobre todo lo demás ---------------------------------


def test_sin_pruebas_en_verde_se_rechaza(politica: ExecutionPolicy) -> None:
    """Aunque todo lo demás sea inmejorable."""
    assert decidir(politica, score=100.0, conf=1.0, pruebas=False) == (
        DecisionType.REJECT
    )


def test_el_motivo_dice_que_fueron_las_pruebas(politica: ExecutionPolicy) -> None:
    informe = politica.evaluate(
        puntuacion(100.0), confianza(1.0), riesgo(RiskLevel.LOW), False
    )

    assert informe.reason == "Unit tests failed."


# --- El riesgo crítico manda sobre la puntuación ----------------------------


def test_el_riesgo_critico_se_rechaza(politica: ExecutionPolicy) -> None:
    assert decidir(politica, nivel=RiskLevel.CRITICAL) == DecisionType.REJECT


def test_el_riesgo_alto_con_todo_a_favor_va_a_revision(
    politica: ExecutionPolicy,
) -> None:
    """Ni con 95 puntos y 0,95 de confianza pasa solo: lo mira una persona."""
    assert decidir(politica, score=95.0, conf=0.95, nivel=RiskLevel.HIGH) == (
        DecisionType.MANUAL_REVIEW
    )


def test_el_riesgo_alto_con_poca_confianza_se_reintenta(
    politica: ExecutionPolicy,
) -> None:
    assert decidir(politica, score=95.0, conf=0.5, nivel=RiskLevel.HIGH) == (
        DecisionType.RETRY
    )


def test_el_riesgo_alto_con_poca_puntuacion_se_reintenta(
    politica: ExecutionPolicy,
) -> None:
    assert decidir(politica, score=80.0, conf=0.95, nivel=RiskLevel.HIGH) == (
        DecisionType.RETRY
    )


# --- La puntuación ----------------------------------------------------------


def test_muy_buena_puntuacion_y_confianza_se_acepta(
    politica: ExecutionPolicy,
) -> None:
    assert decidir(politica, score=90.0, conf=0.70) == DecisionType.ACCEPT


def test_muy_buena_puntuacion_pero_poca_confianza_va_a_revision(
    politica: ExecutionPolicy,
) -> None:
    """90 puntos no bastan si el motor no se fía de lo que hizo."""
    assert decidir(politica, score=95.0, conf=0.5) == DecisionType.MANUAL_REVIEW


def test_puntuacion_intermedia_va_a_revision(politica: ExecutionPolicy) -> None:
    assert decidir(politica, score=70.0) == DecisionType.MANUAL_REVIEW


def test_puntuacion_baja_se_reintenta(politica: ExecutionPolicy) -> None:
    assert decidir(politica, score=55.0) == DecisionType.RETRY


def test_puntuacion_muy_baja_se_rechaza(politica: ExecutionPolicy) -> None:
    assert decidir(politica, score=54.9) == DecisionType.REJECT


# --- El informe -------------------------------------------------------------


def test_solo_aceptar_marca_aprobado(politica: ExecutionPolicy) -> None:
    aceptado = politica.evaluate(
        puntuacion(95.0), confianza(0.95), riesgo(RiskLevel.LOW), True
    )
    revision = politica.evaluate(
        puntuacion(70.0), confianza(0.95), riesgo(RiskLevel.LOW), True
    )

    assert aceptado.approved is True
    assert revision.approved is False


def test_el_informe_lleva_las_metricas(politica: ExecutionPolicy) -> None:
    informe = politica.evaluate(
        puntuacion(95.0, grado="A"), confianza(0.9), riesgo(RiskLevel.LOW), True
    )

    assert informe.metrics["score"] == 95.0
    assert informe.metrics["grade"] == "A"
    assert informe.metrics["risk"] == RiskLevel.LOW.value


# --- Las preguntas que se le hacen al informe -------------------------------


def test_should_commit_solo_con_aceptado(politica: ExecutionPolicy) -> None:
    aceptado = politica.evaluate(
        puntuacion(95.0), confianza(0.95), riesgo(RiskLevel.LOW), True
    )

    assert politica.should_commit(aceptado) is True
    assert politica.should_retry(aceptado) is False
    assert politica.requires_review(aceptado) is False
    assert politica.rejected(aceptado) is False


def test_un_rechazo_no_se_commitea(politica: ExecutionPolicy) -> None:
    rechazado = politica.evaluate(
        puntuacion(100.0), confianza(1.0), riesgo(RiskLevel.LOW), False
    )

    assert politica.should_commit(rechazado) is False
    assert politica.rejected(rechazado) is True


def test_el_resumen_cabe_en_una_linea(politica: ExecutionPolicy) -> None:
    informe = politica.evaluate(
        puntuacion(95.0, grado="A"), confianza(0.9), riesgo(RiskLevel.LOW), True
    )

    resumen = politica.summary(informe)

    assert "ACCEPT" in resumen
    assert "Grade=A" in resumen
    assert "95.00" in resumen
