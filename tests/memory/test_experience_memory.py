"""Tests for ``ExperienceMemory``.

The whole ``memory/`` package sat at 0 % coverage. It is the subsystem that
lets the architect learn from previous runs, so a silent failure there does
not crash anything: it just makes the system stop learning, which is much
harder to notice.

Everything runs against ``tmp_path``; no real repository is touched.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_architect.memory.experience_memory import ExperienceMemory


@pytest.fixture
def memoria(tmp_path: Path) -> ExperienceMemory:
    return ExperienceMemory(str(tmp_path))


def anadir(
    memoria: ExperienceMemory,
    *,
    task: str = "refactorizar",
    success: bool = True,
    quality: float = 95.0,
    notes: str = "",
    confidence: float = 0.9,
) -> None:
    memoria.create(
        project="proyecto",
        task=task,
        decision="ACCEPT",
        success=success,
        confidence=confidence,
        duration=1.0,
        quality=quality,
        notes=notes,
    )


# --- Arranque en frío -------------------------------------------------------


def test_un_repositorio_sin_historial_arranca_vacio(memoria: ExperienceMemory) -> None:
    assert memoria.all() == []


def test_el_archivo_no_se_crea_hasta_que_hay_algo(
    memoria: ExperienceMemory,
) -> None:
    assert not memoria.file.exists()


def test_un_archivo_corrupto_no_tumba_el_arranque(tmp_path: Path) -> None:
    """A truncated JSON must not stop the architect: it starts with no history."""
    (tmp_path / ExperienceMemory.FILE_NAME).write_text("{roto", encoding="utf-8")

    assert ExperienceMemory(str(tmp_path)).all() == []


# --- Persistencia -----------------------------------------------------------


def test_lo_guardado_sobrevive_a_una_nueva_instancia(
    memoria: ExperienceMemory, tmp_path: Path
) -> None:
    """The point of the subsystem: learning must outlive the process."""
    anadir(memoria, task="extraer validaciones")

    recargada = ExperienceMemory(str(tmp_path))

    assert len(recargada.all()) == 1
    assert recargada.all()[0].task == "extraer validaciones"


def test_el_archivo_guardado_es_json_valido(
    memoria: ExperienceMemory, tmp_path: Path
) -> None:
    anadir(memoria)

    datos = json.loads((tmp_path / ExperienceMemory.FILE_NAME).read_text("utf-8"))

    assert isinstance(datos, list)
    assert len(datos) == 1


def test_create_devuelve_la_experiencia_y_la_registra(
    memoria: ExperienceMemory,
) -> None:
    experiencia = memoria.create(
        project="p",
        task="t",
        decision="ACCEPT",
        success=True,
        confidence=0.5,
        duration=2.0,
    )

    assert experiencia.task == "t"
    assert memoria.all() == [experiencia]


# --- Filtros ----------------------------------------------------------------


def test_separa_las_exitosas_de_las_fallidas(memoria: ExperienceMemory) -> None:
    anadir(memoria, task="una que va", success=True)
    anadir(memoria, task="una que falla", success=False)

    assert [e.task for e in memoria.successful()] == ["una que va"]
    assert [e.task for e in memoria.failed()] == ["una que falla"]


def test_search_encuentra_por_la_tarea(memoria: ExperienceMemory) -> None:
    anadir(memoria, task="extraer el validador")
    anadir(memoria, task="renombrar variables")

    assert len(memoria.search("validador")) == 1


def test_search_tambien_mira_las_notas(memoria: ExperienceMemory) -> None:
    anadir(memoria, task="algo", notes="rompio el pipeline")

    assert len(memoria.search("pipeline")) == 1


def test_search_no_distingue_mayusculas(memoria: ExperienceMemory) -> None:
    anadir(memoria, task="Extraer el Validador")

    assert len(memoria.search("VALIDADOR")) == 1


def test_search_sin_coincidencias_devuelve_lista_vacia(
    memoria: ExperienceMemory,
) -> None:
    anadir(memoria, task="algo")

    assert memoria.search("inexistente") == []


# --- best y last ------------------------------------------------------------


def test_best_solo_trae_exitosas_sobre_el_minimo(memoria: ExperienceMemory) -> None:
    anadir(memoria, task="excelente", quality=98.0, success=True)
    anadir(memoria, task="mediocre", quality=50.0, success=True)
    anadir(memoria, task="fallida", quality=99.0, success=False)

    assert [e.task for e in memoria.best()] == ["excelente"]


def test_best_ordena_de_mayor_a_menor_calidad(memoria: ExperienceMemory) -> None:
    anadir(memoria, task="buena", quality=92.0)
    anadir(memoria, task="mejor", quality=99.0)

    assert [e.task for e in memoria.best()] == ["mejor", "buena"]


def test_best_admite_bajar_el_minimo(memoria: ExperienceMemory) -> None:
    anadir(memoria, task="regular", quality=60.0)

    assert memoria.best() == []
    assert len(memoria.best(minimum_quality=50.0)) == 1


def test_last_devuelve_las_mas_recientes(memoria: ExperienceMemory) -> None:
    for i in range(5):
        anadir(memoria, task=f"tarea-{i}")

    assert [e.task for e in memoria.last(limit=2)] == ["tarea-3", "tarea-4"]


def test_last_con_menos_registros_que_el_limite(memoria: ExperienceMemory) -> None:
    anadir(memoria, task="unica")

    assert len(memoria.last(limit=10)) == 1


# --- Estadísticas y limpieza ------------------------------------------------


def test_statistics_sobre_una_memoria_vacia_no_revienta(
    memoria: ExperienceMemory,
) -> None:
    assert isinstance(memoria.statistics(), dict)


def test_statistics_cuenta_lo_registrado(memoria: ExperienceMemory) -> None:
    anadir(memoria, success=True)
    anadir(memoria, success=False)

    estadisticas = memoria.statistics()

    assert estadisticas["experiences"] == 2
    assert estadisticas["successful"] == 1
    assert estadisticas["failed"] == 1
    assert estadisticas["success_rate"] == 50.0


def test_clear_vacia_la_memoria(memoria: ExperienceMemory, tmp_path: Path) -> None:
    anadir(memoria)
    memoria.clear()

    assert memoria.all() == []
    assert ExperienceMemory(str(tmp_path)).all() == []


def test_summary_devuelve_un_diccionario(memoria: ExperienceMemory) -> None:
    anadir(memoria)

    assert isinstance(memoria.summary(), dict)
