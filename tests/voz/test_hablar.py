"""La voz: qué hay, qué falta, y no mentir sobre ello.

Al mirar este equipo, Windows solo tenía voces **femeninas** en español:
Sabina (es-MX), Helena (es-ES) y Zira (en-US). Decir "listo, ya tienes voz
masculina latina" habría sido mentir en lo primero que se nota.

Por eso esto detecta lo que hay y lo dice, incluido lo que falta para
conseguir la voz que se quería.
"""

from __future__ import annotations

from unittest import mock

import pytest

from ai_architect.voz import hablar as voz

# --- Qué se dice en alto ----------------------------------------------------


def test_no_lee_los_comandos() -> None:
    """Una ruta o un comando leídos en alto suenan a ruido."""
    limpio = voz._para_decir("Buenas tardes.\narchitect improve . --apply\nTodo bien.")

    assert "architect" not in limpio
    assert "Buenas tardes" in limpio
    assert "Todo bien" in limpio


def test_quita_el_formato() -> None:
    assert "`" not in voz._para_decir("El `pide` funciona")
    assert "*" not in voz._para_decir("Va **muy** bien")


def test_junta_las_lineas() -> None:
    assert voz._para_decir("uno\n\ndos") == "uno dos"


def test_un_texto_vacio_no_se_dice() -> None:
    assert voz.hablar("   ")["hablado"] is False


# --- Elegir motor -----------------------------------------------------------


def _todos(piper: bool, openai: bool, windows: bool) -> dict:
    return {
        "piper": {"disponible": piper},
        "openai": {"disponible": openai},
        "windows": {"disponible": windows},
    }


def test_prefiere_piper_por_gratis_y_masculino() -> None:
    """El orden no es caprichoso: primero el que da la voz que se pidió y no
    cuesta dinero."""
    with mock.patch.object(voz, "motores", return_value=_todos(True, True, True)):
        assert voz.elegir() == "piper"


def test_sin_piper_usa_openai() -> None:
    with mock.patch.object(voz, "motores", return_value=_todos(False, True, True)):
        assert voz.elegir() == "openai"


def test_windows_es_el_ultimo() -> None:
    """Es el que suena distinto a lo que se quería."""
    with mock.patch.object(voz, "motores", return_value=_todos(False, False, True)):
        assert voz.elegir() == "windows"


def test_se_puede_pedir_uno_concreto() -> None:
    with mock.patch.object(voz, "motores", return_value=_todos(True, True, True)):
        assert voz.elegir("windows") == "windows"


def test_si_el_pedido_no_esta_se_usa_otro() -> None:
    with mock.patch.object(voz, "motores", return_value=_todos(False, True, False)):
        assert voz.elegir("piper") == "openai"


def test_sin_ninguna_no_se_elige_nada() -> None:
    with mock.patch.object(voz, "motores", return_value=_todos(False, False, False)):
        assert voz.elegir() == ""


# --- Sin voz se sigue trabajando --------------------------------------------


def test_sin_ninguna_voz_lo_dice_y_no_revienta() -> None:
    with mock.patch.object(voz, "elegir", return_value=""):
        resultado = voz.hablar("hola")

    assert resultado["hablado"] is False
    assert "Instala Piper" in resultado["motivo"]


def test_si_el_motor_falla_no_revienta() -> None:
    """La respuesta ya está escrita en pantalla: sin voz se sigue."""
    with mock.patch.object(voz, "elegir", return_value="windows"):
        with mock.patch.object(voz, "_con_windows", side_effect=OSError("sin audio")):
            resultado = voz.hablar("hola")

    assert resultado["hablado"] is False
    assert "sin audio" in resultado["motivo"]


# --- Lo que se informa ------------------------------------------------------


def test_informa_de_los_tres_motores() -> None:
    assert set(voz.motores()) == {"piper", "openai", "windows"}


def test_cada_motor_dice_que_le_falta() -> None:
    for datos in voz.motores().values():
        assert datos["nota"]


def test_openai_avisa_de_que_no_suena_latino() -> None:
    """Es de pago y suena neutro: las dos cosas hay que decirlas."""
    nota = voz.motores()["openai"]["nota"]

    assert "pago" in nota
    assert "latino" in nota


@pytest.mark.parametrize("voces", [None, "Sabina (es-MX, Female)"])
def test_windows_avisa_si_no_hay_voz_masculina(voces: str | None) -> None:
    """La regresión que motivó todo esto: este equipo solo tenía voces
    femeninas, y había que decirlo."""
    with mock.patch.object(voz, "_voz_windows", return_value=voces):
        nota = voz._nota_windows()

    assert "masculina" in nota or "sin voces" in nota
