from __future__ import annotations

from ai_architect.autonomous.approval_engine import ApprovalEngine
from ai_architect.autonomous.autonomous_engine import AutonomousEngine


def test_autonomous_engine_executes_tasks() -> None:
    engine = AutonomousEngine()

    tasks = [
        {
            "priority": 10,
            "risk": 1,
            "callback": lambda: "first",
        },
        {
            "priority": 5,
            "risk": 1,
            "callback": lambda: "second",
        },
    ]

    result = engine.execute(tasks)

    assert "results" in result
    assert "monitor" in result

    results = result["results"]

    assert isinstance(results, list)
    assert len(results) == 2

    assert results[0]["success"] is True
    assert results[0]["result"] == "first"

    assert results[1]["success"] is True
    assert results[1]["result"] == "second"


def test_autonomous_engine_processes_failed_task() -> None:
    engine = AutonomousEngine()

    def failing_callback() -> None:
        raise RuntimeError("autonomous failure")

    tasks = [
        {
            "priority": 10,
            "risk": 1,
            "callback": failing_callback,
        },
    ]

    result = engine.execute(tasks)

    results = result["results"]

    assert isinstance(results, list)
    assert len(results) == 1

    assert results[0]["success"] is False
    assert "traceback" in results[0]
    assert "autonomous failure" in results[0]["traceback"]


def test_autonomous_engine_handles_empty_task_list() -> None:
    engine = AutonomousEngine()

    result = engine.execute([])

    assert result["results"] == []

    monitor = result["monitor"]

    assert isinstance(monitor, dict)
    assert monitor["executions"] == 0
    assert monitor["events"] == []


# --- La puerta de aprobación ------------------------------------------------
#
# ``ApprovalEngine`` se construía en ``__init__`` y no se llamaba nunca: el
# mismo patrón que el motor de decisión en ``improver``. Un motor autónomo
# sin puerta de aprobación no es autónomo, es automático.


def tarea_que_devuelve(salida, **extra):
    base = {"priority": 1, "risk": 0, "callback": lambda: salida}
    base.update(extra)
    return base


def mejora(confianza: float = 0.9, pruebas_ok: bool = True) -> dict:
    """La forma de lo que devuelve ``ImprovementEngine.improve()``."""
    return {
        "success": True,
        "patch_id": "abc",
        "decision": {"approved": True, "confidence": confianza},
        "tests": {"success": pruebas_ok},
    }


def test_el_motor_de_aprobacion_esta_enganchado() -> None:
    """Antes se construía y nadie lo llamaba."""
    engine = AutonomousEngine()

    resultado = engine.execute([tarea_que_devuelve(mejora())])

    assert resultado["results"][0]["approved"] is True


def test_sin_pruebas_en_verde_no_se_aprueba() -> None:
    engine = AutonomousEngine()

    resultado = engine.execute([tarea_que_devuelve(mejora(pruebas_ok=False))])

    assert resultado["results"][0]["approved"] is False
    assert resultado["results"][0]["approval_reason"] == "las pruebas no pasaron"


def test_con_poca_confianza_no_se_aprueba() -> None:
    engine = AutonomousEngine()

    resultado = engine.execute([tarea_que_devuelve(mejora(confianza=0.2))])

    assert resultado["results"][0]["approved"] is False


def test_una_tarea_que_falla_no_se_aprueba() -> None:
    def revienta():
        raise RuntimeError("algo")

    engine = AutonomousEngine()

    resultado = engine.execute([{"priority": 1, "risk": 0, "callback": revienta}])

    assert resultado["results"][0]["approved"] is False
    assert resultado["results"][0]["approval_reason"] == "la tarea falló"


def test_lo_que_no_se_puede_juzgar_no_se_aprueba() -> None:
    """Lo que no se sabe, no se aprueba."""
    engine = AutonomousEngine()

    resultado = engine.execute([tarea_que_devuelve("una cadena suelta")])

    assert resultado["results"][0]["approved"] is False
    assert "nada que juzgar" in resultado["results"][0]["approval_reason"]


def test_la_tarea_se_ejecuta_aunque_no_se_apruebe() -> None:
    """No es un permiso previo: es el veredicto sobre lo que salió."""
    engine = AutonomousEngine()

    resultado = engine.execute([tarea_que_devuelve(mejora(pruebas_ok=False))])

    assert resultado["results"][0]["success"] is True
    assert resultado["results"][0]["result"]["patch_id"] == "abc"


def test_el_informe_cuenta_cuantas_se_aprobaron() -> None:
    engine = AutonomousEngine()

    resultado = engine.execute(
        [
            tarea_que_devuelve(mejora(), priority=3),
            tarea_que_devuelve(mejora(pruebas_ok=False), priority=2),
            tarea_que_devuelve(mejora(), priority=1),
        ]
    )

    assert resultado["approved"] == 2


def test_el_riesgo_de_la_tarea_llega_a_la_aprobacion() -> None:
    engine = AutonomousEngine()

    resultado = engine.execute([tarea_que_devuelve(mejora(), risk_level="CRITICAL")])

    assert resultado["results"][0]["approved"] is False
    assert "CRITICAL" in resultado["results"][0]["approval_reason"]


def test_se_puede_inyectar_otro_motor_de_aprobacion() -> None:
    engine = AutonomousEngine(approval=ApprovalEngine(confianza_minima=0.99))

    resultado = engine.execute([tarea_que_devuelve(mejora(confianza=0.9))])

    assert resultado["results"][0]["approved"] is False


# --- Lo que ya no construye -------------------------------------------------


def test_ya_no_trae_gestores_de_git_sin_usar() -> None:
    """Construía un BranchManager, un MergeManager y un RollbackManager que
    no llamaba nunca, y que ejecutaban git **sin ``cwd``**: sobre el
    directorio del proceso, no sobre el repositorio analizado. El rollback
    era un ``git reset --hard HEAD~1`` suelto."""
    engine = AutonomousEngine()

    assert not hasattr(engine, "branch")
    assert not hasattr(engine, "merge")
    assert not hasattr(engine, "rollback")


def test_una_tarea_que_revienta_dice_cual_era() -> None:
    """El resultado del worker no lleva rastro de la tarea: sin esto, un
    fallo no dice qué instrucción lo produjo."""

    def revienta():
        raise RuntimeError("algo")

    engine = AutonomousEngine()

    resultado = engine.execute(
        [{"name": "extraer el validador", "priority": 1, "callback": revienta}]
    )

    assert resultado["results"][0]["task"] == "extraer el validador"
