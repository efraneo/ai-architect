"""Tests for ``ExecutionResult``.

It is the object the whole execution subsystem returns, and it had no tests.
Its properties carry real logic: ``approved`` falls back through three
sources, ``decision_name`` derives a name when there is no report, and
``to_dict`` has to stay serializable so the result can be persisted.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from ai_architect.decision_engine.decision_report import DecisionReport, DecisionType
from ai_architect.execution.execution_result import ExecutionResult


def informe(
    aprobado: bool = True,
    confianza: float = 0.9,
    tipo: DecisionType = DecisionType.ACCEPT,
) -> DecisionReport:
    return DecisionReport(decision=tipo, approved=aprobado, confidence=confianza)


def crear(**kwargs: object) -> ExecutionResult:
    base: dict[str, object] = {
        "repository": "/repo",
        "filename": "modulo.py",
        "instruction": "mejora esto",
    }
    base.update(kwargs)
    return ExecutionResult(**base)  # type: ignore[arg-type]


# --- approved: tres fuentes, en orden --------------------------------------


def test_sin_decision_ni_metadatos_aprueba_si_validacion_y_exito() -> None:
    assert crear(success=True, validation_ok=True).approved is True


def test_sin_decision_no_aprueba_si_fallo_la_validacion() -> None:
    assert crear(success=True, validation_ok=False).approved is False


def test_sin_decision_no_aprueba_si_no_hubo_exito() -> None:
    assert crear(success=False, validation_ok=True).approved is False


def test_los_metadatos_mandan_sobre_validacion_y_exito() -> None:
    resultado = crear(
        success=False,
        validation_ok=False,
        metadata={"execution": {"approved": True}},
    )

    assert resultado.approved is True


def test_la_decision_manda_sobre_todo_lo_demas() -> None:
    """A DecisionReport is the most authoritative source."""
    resultado = crear(
        success=True,
        validation_ok=True,
        metadata={"execution": {"approved": True}},
        decision=informe(aprobado=False, tipo=DecisionType.MANUAL_REVIEW),
    )

    assert resultado.approved is False


# --- confidence y decision_name --------------------------------------------


def test_sin_decision_la_confianza_es_cero() -> None:
    assert crear().confidence == 0.0


def test_con_decision_la_confianza_sale_del_informe() -> None:
    assert crear(decision=informe(confianza=0.87)).confidence == 0.87


def test_sin_decision_el_nombre_se_deduce_de_la_aprobacion() -> None:
    assert crear(success=True, validation_ok=True).decision_name == "ACCEPT"
    assert crear(success=False).decision_name == "REJECT"


# --- Ciclo de vida ----------------------------------------------------------


def test_recien_creado_no_esta_completado() -> None:
    resultado = crear()

    assert resultado.completed is False
    assert resultado.finished_at is None


def test_finish_marca_el_final_y_calcula_la_duracion() -> None:
    resultado = crear()
    resultado.started_at = datetime.utcnow() - timedelta(seconds=2)

    resultado.finish()

    assert resultado.completed is True
    assert resultado.finished_at is not None
    assert resultado.duration >= 2.0
    assert resultado.execution_time == resultado.duration


# --- Metadatos --------------------------------------------------------------


def test_add_metadata_guarda_la_clave() -> None:
    resultado = crear()
    resultado.add_metadata("provider", "claude")

    assert resultado.metadata["provider"] == "claude"


# --- Serialización ----------------------------------------------------------


def test_to_dict_es_serializable_a_json() -> None:
    """The result gets persisted: a datetime inside would break it."""
    resultado = crear(success=True)
    resultado.finish()

    json.dumps(resultado.to_dict())


def test_to_dict_convierte_las_fechas_a_texto() -> None:
    resultado = crear()
    resultado.finish()

    datos = resultado.to_dict()

    assert isinstance(datos["started_at"], str)
    assert isinstance(datos["finished_at"], str)


def test_to_dict_deja_la_fecha_final_en_none_si_no_termino() -> None:
    assert crear().to_dict()["finished_at"] is None


def test_to_dict_serializa_la_decision_cuando_existe() -> None:
    resultado = crear(decision=informe())

    assert isinstance(resultado.to_dict()["decision"], dict)


def test_summary_trae_las_claves_del_informe_corto() -> None:
    esperadas = {
        "repository",
        "file",
        "success",
        "approved",
        "decision",
        "confidence",
        "validation",
        "tests",
        "provider",
        "duration",
    }

    assert esperadas == set(crear().summary())


# --- Verdad booleana --------------------------------------------------------


def test_el_resultado_es_falso_si_no_hubo_exito() -> None:
    """Lets you write ``if resultado:`` in the calling code."""
    assert bool(crear(success=True)) is True
    assert bool(crear(success=False)) is False
