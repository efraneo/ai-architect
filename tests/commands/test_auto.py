"""``architect auto``: varias mejoras en una sola pasada.

Es lo que pone a trabajar a ``autonomous/``, que llevaba nueve módulos
huérfanos. Cada instrucción es una tarea: se ordenan por prioridad, se
ejecutan y cada resultado pasa por la puerta de aprobación.

Ninguna prueba llama a un proveedor: el ``ImprovementEngine`` se inyecta.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from ai_architect.cli import build_parser
from ai_architect.commands import auto


@pytest.fixture
def proyecto(tmp_path: Path) -> Path:
    (tmp_path / "modulo.py").write_text("valor = 1\n", encoding="utf-8")
    return tmp_path


def mejorador_falso(confianza: float = 0.9, pruebas_ok: bool = True):
    """Devuelve lo que devuelve ``improve()``, sin llamar a nadie."""
    motor = mock.Mock()

    def improve(_repositorio, instruction: str = "", **_):
        return {
            "success": True,
            "instruction": instruction,
            "patch_id": f"parche-{instruction}",
            "decision": {"approved": True, "confidence": confianza},
            "tests": {"success": pruebas_ok},
            "committed": False,
        }

    motor.improve = mock.Mock(side_effect=improve)
    return motor


# --- El comando existe ------------------------------------------------------


def test_el_parser_acepta_auto() -> None:
    args = build_parser().parse_args(["auto", ".", "--instructions", "una", "otra"])

    assert args.command == "auto"
    assert args.instructions == ["una", "otra"]


# --- Lo que hace ------------------------------------------------------------


def test_ejecuta_todas_las_instrucciones(proyecto: Path) -> None:
    motor = mejorador_falso()

    resultado = auto.run(str(proyecto), ["una", "otra", "tercera"], engine=motor)

    assert resultado["success"] is True
    assert resultado["total_tasks"] == 3
    assert resultado["executed"] == 3
    assert motor.improve.call_count == 3


def test_cada_tarea_lleva_su_propia_instruccion(proyecto: Path) -> None:
    """El fallo clásico: capturar la variable del bucle y correr tres veces
    la última instrucción."""
    motor = mejorador_falso()

    resultado = auto.run(str(proyecto), ["una", "otra", "tercera"], engine=motor)

    assert [t["instruction"] for t in resultado["tasks"]] == [
        "una",
        "otra",
        "tercera",
    ]


def test_la_primera_instruccion_va_primero(proyecto: Path) -> None:
    """El planificador ordena por prioridad de mayor a menor."""
    motor = mejorador_falso()

    auto.run(str(proyecto), ["la importante", "la otra"], engine=motor)

    pedidas = [c.kwargs["instruction"] for c in motor.improve.call_args_list]

    assert pedidas == ["la importante", "la otra"]


# --- La puerta de aprobación ------------------------------------------------


def test_con_pruebas_en_verde_y_confianza_se_aprueba(proyecto: Path) -> None:
    resultado = auto.run(str(proyecto), ["una"], engine=mejorador_falso())

    assert resultado["approved"] == 1
    assert resultado["tasks"][0]["approved"] is True


def test_con_las_pruebas_en_rojo_no_se_aprueba(proyecto: Path) -> None:
    motor = mejorador_falso(pruebas_ok=False)

    resultado = auto.run(str(proyecto), ["una"], engine=motor)

    assert resultado["approved"] == 0
    assert resultado["tasks"][0]["reason"] == "las pruebas no pasaron"


def test_con_poca_confianza_no_se_aprueba(proyecto: Path) -> None:
    motor = mejorador_falso(confianza=0.3)

    resultado = auto.run(str(proyecto), ["una"], engine=motor)

    assert resultado["tasks"][0]["approved"] is False
    assert "0.30" in resultado["tasks"][0]["reason"]


def test_la_mejora_se_ejecuta_aunque_no_se_apruebe(proyecto: Path) -> None:
    """La aprobación es un veredicto sobre el resultado, no un permiso previo:
    el parche ya está generado y guardado."""
    motor = mejorador_falso(pruebas_ok=False)

    resultado = auto.run(str(proyecto), ["una"], engine=motor)

    assert resultado["executed"] == 1
    assert resultado["tasks"][0]["success"] is True
    assert resultado["tasks"][0]["patch_id"] == "parche-una"


# --- Los fallos -------------------------------------------------------------


def test_una_mejora_que_revienta_no_para_las_demas(proyecto: Path) -> None:
    motor = mejorador_falso()
    motor.improve = mock.Mock(
        side_effect=[RuntimeError("sin cuota"), {"success": True, "tests": {}}]
    )

    resultado = auto.run(str(proyecto), ["una", "otra"], engine=motor)

    assert resultado["executed"] == 2
    assert resultado["tasks"][0]["success"] is False
    assert resultado["tasks"][0]["reason"] == "la tarea falló"


def test_un_repositorio_inexistente_falla_con_claridad(tmp_path: Path) -> None:
    resultado = auto.run(str(tmp_path / "no-existe"), ["una"])

    assert resultado["success"] is False
    assert resultado["error"] == "Repository not found."


def test_sin_instrucciones_no_hay_nada_que_hacer(proyecto: Path) -> None:
    resultado = auto.run(str(proyecto), [])

    assert resultado["success"] is False
    assert resultado["error"] == "No instructions given."


def test_no_se_construye_el_mejorador_si_el_repo_no_existe(tmp_path: Path) -> None:
    """Construirlo lee las claves del proveedor: no hace falta para fallar."""
    with mock.patch("ai_architect.commands.auto.ImprovementEngine") as construir:
        auto.run(str(tmp_path / "no-existe"), ["una"])

    construir.assert_not_called()
