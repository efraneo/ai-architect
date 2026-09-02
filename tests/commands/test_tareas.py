"""Que trabaje solo, cuando se le diga.

`scheduler/` llevaba meses escrito y sin conectar. Lo que se fija aquí es
lo que le faltaba para servir de algo: que las tareas **sobrevivan al
proceso** y que **alguien las ejecute**.

Y lo que no puede pasar: que una tarea dormida despierte disparando cinco
ejecuciones seguidas, o que un fallo deje una tarea sin volver a correr
nunca.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

import pytest

from ai_architect.commands import tareas


@pytest.fixture(autouse=True)
def libro_propio(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(tareas, "ARCHIVO", tmp_path / "tareas.json")

    yield


# --- Programar hablando ------------------------------------------------------


def test_cada_noche_se_programa_a_las_diez() -> None:
    salida = tareas.por_voz("revisa autosgsst cada noche", ".")

    assert salida is not None
    guardadas = tareas.cargar()

    assert len(guardadas) == 1
    assert guardadas[0].next_run.hour == tareas.HORAS["noche"]


def test_la_orden_se_guarda_sin_la_parte_del_cuando() -> None:
    """La tarea es "revisa autosgsst", no "revisa autosgsst cada noche"."""
    tareas.por_voz("revisa autosgsst cada noche", ".")

    assert tareas.cargar()[0].name == "revisa autosgsst"


def test_la_hora_y_su_franja_se_quitan_juntas() -> None:
    """Quitando solo la hora queda "las dependencias de la mañana"."""
    tareas.por_voz("revisa las dependencias cada día a las 7 de la mañana", ".")

    assert tareas.cargar()[0].name == "revisa las dependencias"


def test_se_respeta_la_hora_dicha() -> None:
    tareas.por_voz("revisa esto cada día a las 7 de la mañana", ".")

    assert tareas.cargar()[0].next_run.hour == 7


def test_la_proxima_vez_nunca_es_en_el_pasado() -> None:
    tareas.por_voz("revisa esto cada noche", ".")

    assert tareas.cargar()[0].next_run > datetime.now()


def test_una_tarea_es_una_orden_que_se_da_a_si_mismo() -> None:
    """El callback es la frase: así vale todo lo que ya sabe hacer."""
    import json

    tareas.por_voz("revisa autosgsst cada noche", "C:/proyectos/x")

    encargo = json.loads(tareas.cargar()[0].callback)

    assert encargo["frase"] == "revisa autosgsst"
    assert encargo["project"] == "C:/proyectos/x"


# --- Pausar y reanudar -------------------------------------------------------


def test_descansemos_las_duerme_a_todas() -> None:
    tareas.por_voz("revisa esto cada noche", ".")
    tareas.por_voz("revisa lo otro cada día", ".")

    tareas.por_voz("descansemos", ".")

    assert all(not t.enabled for t in tareas.cargar())


def test_una_tarea_dormida_no_se_ejecuta() -> None:
    tareas.por_voz("revisa esto cada noche", ".")
    tareas.por_voz("descansemos", ".")

    manana = datetime.now() + timedelta(days=2)

    assert tareas.pendientes(manana) == []


def test_al_despertar_no_dispara_todo_lo_atrasado() -> None:
    """Dormida tres días, al reanudar se ejecutaría tres veces seguidas."""
    tareas.por_voz("revisa esto cada noche", ".")
    tareas.por_voz("descansemos", ".")

    guardadas = tareas.cargar()
    guardadas[0].next_run = datetime.now() - timedelta(days=3)
    tareas.guardar(guardadas)

    tareas.por_voz("reanuda", ".")

    assert tareas.pendientes() == []
    assert tareas.cargar()[0].enabled is True


def test_se_puede_preguntar_que_hay() -> None:
    tareas.por_voz("revisa autosgsst cada noche", ".")

    dicho = tareas.por_voz("qué tienes programado", ".")["explanation"]

    assert "revisa autosgsst" in dicho


def test_sin_nada_lo_dice() -> None:
    assert "No tengo nada" in tareas.contar()


def test_se_pueden_borrar() -> None:
    tareas.por_voz("revisa esto cada noche", ".")

    tareas.por_voz("cancela las tareas", ".")

    assert tareas.cargar() == []


def test_lo_que_no_va_de_tareas_no_se_ataja() -> None:
    assert tareas.por_voz("revisa el proyecto", ".") is None
    assert tareas.por_voz("qué hora es", ".") is None


# --- Ejecutarlas -------------------------------------------------------------


def test_sobreviven_al_proceso() -> None:
    """Era la mitad que le faltaba: morían con el intérprete."""
    tareas.por_voz("revisa esto cada noche", ".")

    assert len(tareas.cargar()) == 1, "se releen del disco, no de memoria"


def test_se_ejecuta_la_que_toca() -> None:
    tareas.por_voz("revisa esto cada noche", ".")

    guardadas = tareas.cargar()
    guardadas[0].next_run = datetime.now() - timedelta(minutes=1)
    tareas.guardar(guardadas)

    with mock.patch(
        "ai_architect.commands.pide.run",
        return_value={"success": True, "explanation": "Todo bien."},
    ) as ejecutar:
        hechas = tareas.correr()

    ejecutar.assert_called_once()
    assert hechas[0]["explanation"] == "Todo bien."


def test_se_reprograma_antes_de_ejecutar() -> None:
    """Si se reprogramara después, un fallo la dejaría sin volver a correr."""
    tareas.por_voz("revisa esto cada noche", ".")

    guardadas = tareas.cargar()
    guardadas[0].next_run = datetime.now() - timedelta(minutes=1)
    tareas.guardar(guardadas)

    with mock.patch(
        "ai_architect.commands.pide.run", side_effect=RuntimeError("se rompió")
    ):
        tareas.correr()

    assert tareas.cargar()[0].next_run > datetime.now()


def test_una_tarea_rota_no_tumba_las_demas() -> None:
    tareas.por_voz("revisa esto cada noche", ".")

    guardadas = tareas.cargar()
    guardadas[0].next_run = datetime.now() - timedelta(minutes=1)
    tareas.guardar(guardadas)

    with mock.patch("ai_architect.commands.pide.run", side_effect=RuntimeError("boom")):
        hechas = tareas.correr()

    assert "boom" in hechas[0]["error"]


def test_lo_que_no_toca_no_se_ejecuta() -> None:
    tareas.por_voz("revisa esto cada noche", ".")

    with mock.patch("ai_architect.commands.pide.run") as ejecutar:
        tareas.correr()

    ejecutar.assert_not_called()


# --- El libro ----------------------------------------------------------------


def test_un_libro_ilegible_no_impide_hablar(tmp_path: Path, monkeypatch) -> None:
    roto = tmp_path / "tareas.json"
    roto.write_text("{esto no es json")

    monkeypatch.setattr(tareas, "ARCHIVO", roto)

    assert tareas.cargar() == []


def test_una_fila_corrupta_no_se_lleva_las_buenas(tmp_path: Path, monkeypatch) -> None:
    import json

    libro = tmp_path / "tareas.json"

    monkeypatch.setattr(tareas, "ARCHIVO", libro)

    tareas.por_voz("revisa esto cada noche", ".")

    crudo = json.loads(libro.read_text(encoding="utf-8"))
    crudo.append({"esto": "no tiene forma de tarea"})
    libro.write_text(json.dumps(crudo), encoding="utf-8")

    assert len(tareas.cargar()) == 1


def test_se_dice_la_hora_como_se_dice() -> None:
    """ "cada día a las 22" leído en voz alta suena a marcador."""
    dicho = tareas._cuando_se_dice(tareas.DIA, datetime(2026, 9, 2, 22, 0))

    assert "10 de la noche" in dicho
