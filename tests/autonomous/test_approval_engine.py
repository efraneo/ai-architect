"""``ApprovalEngine`` se construía y no se llamaba nunca.

El mismo patrón que ya apareció en ``improver`` con el motor de decisión: el
objeto estaba ahí, en el constructor, sin que nadie lo invocara. Un motor
autónomo sin puerta de aprobación no es autónomo, es automático.

Y al conectarlo salió el desajuste: comparaba la confianza contra ``90``,
pero el ``DecisionEngine`` de este proyecto la devuelve en 0-1 (``0.73``).
**Nada se habría aprobado jamás.** Como nadie lo llamaba, no se notó.
"""

from __future__ import annotations

import pytest

from ai_architect.autonomous.approval_engine import ApprovalEngine


@pytest.fixture
def motor() -> ApprovalEngine:
    return ApprovalEngine()


def bueno(**cambios):
    base = {"tests_ok": True, "risk": "LOW", "confidence": 0.9}
    base.update(cambios)
    return base


# --- La escala de la confianza ----------------------------------------------


def test_la_confianza_va_en_cero_uno(motor: ApprovalEngine) -> None:
    """La regresión: 0.73 >= 90 es falso siempre."""
    assert motor.approve(bueno(confidence=0.9)) is True


def test_por_debajo_del_minimo_no_se_aprueba(motor: ApprovalEngine) -> None:
    assert motor.approve(bueno(confidence=0.5)) is False


def test_justo_en_el_minimo_se_aprueba(motor: ApprovalEngine) -> None:
    assert motor.approve(bueno(confidence=0.75)) is True


def test_el_minimo_se_puede_subir() -> None:
    exigente = ApprovalEngine(confianza_minima=0.95)

    assert exigente.approve(bueno(confidence=0.9)) is False


# --- Las pruebas mandan -----------------------------------------------------


def test_sin_pruebas_en_verde_no_se_aprueba(motor: ApprovalEngine) -> None:
    assert motor.approve(bueno(tests_ok=False)) is False


def test_si_no_se_dice_nada_de_las_pruebas_no_se_aprueba(
    motor: ApprovalEngine,
) -> None:
    """Lo que no se sabe, no se aprueba."""
    assert motor.approve({"confidence": 0.99}) is False


# --- El riesgo --------------------------------------------------------------


@pytest.mark.parametrize("riesgo", ["CRITICAL", "critical", "HIGH", "CRÍTICO"])
def test_el_riesgo_alto_veta(motor: ApprovalEngine, riesgo: str) -> None:
    assert motor.approve(bueno(risk=riesgo)) is False


def test_el_riesgo_bajo_no_estorba(motor: ApprovalEngine) -> None:
    assert motor.approve(bueno(risk="LOW")) is True


# --- Lo que no es un número -------------------------------------------------


def test_una_confianza_que_no_es_numero_no_aprueba(motor: ApprovalEngine) -> None:
    assert motor.approve(bueno(confidence="mucha")) is False


def test_un_booleano_no_cuenta_como_confianza(motor: ApprovalEngine) -> None:
    """``True`` es un ``int`` en Python, y 1 >= 0.75."""
    assert motor.approve(bueno(confidence=True)) is False


def test_una_ejecucion_vacia_no_se_aprueba(motor: ApprovalEngine) -> None:
    assert motor.approve({}) is False


# --- El motivo --------------------------------------------------------------


def test_dice_por_que_no(motor: ApprovalEngine) -> None:
    """Un ``False`` a secas no sirve para actuar."""
    assert motor.motivo(bueno(tests_ok=False)) == "las pruebas no pasaron"


def test_el_motivo_nombra_el_riesgo(motor: ApprovalEngine) -> None:
    assert "CRITICAL" in motor.motivo(bueno(risk="CRITICAL"))


def test_el_motivo_dice_cuanta_confianza_faltaba(motor: ApprovalEngine) -> None:
    motivo = motor.motivo(bueno(confidence=0.4))

    assert "0.40" in motivo
    assert "0.75" in motivo


def test_cuando_se_aprueba_tambien_lo_dice(motor: ApprovalEngine) -> None:
    assert motor.motivo(bueno()) == "aprobado"
