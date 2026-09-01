"""El rostro: que se abra, y que la boca dure lo que dura el audio.

Ninguna prueba abre un navegador ni reproduce sonido. Lo que se fija es el
contrato entre las dos mitades: Python calcula los milisegundos y la página
los recibe por la URL. Si ese número se pierde por el camino, la cara mueve
la boca en el vacío — y eso es justo lo que no se ve en una captura.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from ai_architect.commands import avatar
from ai_architect.core import perfil


@pytest.fixture(autouse=True)
def sin_perfil_real(tmp_path: Path):
    """El perfil del equipo no puede decidir el resultado de una prueba."""
    archivo = tmp_path / "perfil.json"

    with mock.patch.object(perfil, "ARCHIVO", archivo):
        perfil.configurar("Eathan", archivo=archivo)
        yield


@pytest.fixture(autouse=True)
def sin_recuerdo():
    """`_abierto` es de módulo: sin esto, una prueba cambia la siguiente."""
    avatar._abierto = False

    yield

    avatar._abierto = False


def test_el_rostro_existe() -> None:
    """Se distribuye con el paquete: si no está, el comando no sirve."""
    assert avatar.ROSTRO.is_file()
    assert "<canvas" in avatar.ROSTRO.read_text(encoding="utf-8")


def test_abre_el_navegador(tmp_path: Path) -> None:
    with mock.patch("webbrowser.open") as abrir:
        resultado = avatar.run()

    abrir.assert_called_once()
    assert resultado["success"] is True
    assert resultado["url"].startswith("file:")


def test_sin_texto_no_llama_a_la_voz() -> None:
    with mock.patch("webbrowser.open"):
        with mock.patch.object(avatar.motor_de_voz, "preparar") as preparar:
            avatar.run()

    preparar.assert_not_called()


def test_la_duracion_del_audio_viaja_en_la_url() -> None:
    """El único dato que la página necesita de Python."""
    with mock.patch("webbrowser.open") as abrir:
        with mock.patch.object(
            avatar.motor_de_voz,
            "preparar",
            return_value={"archivo": Path("x.wav"), "motor": "openai", "segundos": 5.9},
        ):
            with mock.patch.object(avatar.motor_de_voz, "emitir", return_value=True):
                resultado = avatar.run(decir="hola", esperar=0)

    assert "?ms=5900" in resultado["url"]
    assert "?ms=5900" in abrir.call_args[0][0]


def test_se_espera_a_que_pinte_antes_de_sonar() -> None:
    """Si suena antes de que el navegador dibuje, la boca llega tarde."""
    with mock.patch("webbrowser.open"):
        with mock.patch.object(
            avatar.motor_de_voz,
            "preparar",
            return_value={"archivo": Path("x.wav"), "motor": "openai", "segundos": 1.0},
        ):
            with mock.patch.object(avatar.motor_de_voz, "emitir", return_value=True):
                with mock.patch("time.sleep") as dormir:
                    avatar.run(decir="hola")

    dormir.assert_called_once_with(avatar.ESPERA_NAVEGADOR)


def test_la_segunda_vez_se_espera_menos() -> None:
    """La pestaña ya está abierta: arrancar el navegador solo pasa una vez."""
    with mock.patch("webbrowser.open"):
        with mock.patch.object(
            avatar.motor_de_voz,
            "preparar",
            return_value={"archivo": Path("x.wav"), "motor": "openai", "segundos": 1.0},
        ):
            with mock.patch.object(avatar.motor_de_voz, "emitir", return_value=True):
                with mock.patch("time.sleep") as dormir:
                    avatar.run(decir="una")
                    avatar.run(decir="dos")

    assert dormir.call_args_list[-1][0][0] == avatar.ESPERA_PESTANA


def test_sin_voz_la_cara_sigue_saliendo() -> None:
    """Que no haya audio no puede dejar la pantalla en negro."""
    with mock.patch("webbrowser.open"):
        with mock.patch.object(
            avatar.motor_de_voz,
            "preparar",
            return_value={
                "archivo": None,
                "motor": "",
                "segundos": 0.0,
                "motivo": "sin voz",
            },
        ):
            resultado = avatar.run(decir="hola", esperar=0)

    assert resultado["success"] is True
    assert resultado["spoke"] is False
    assert "sin voz" in resultado["explanation"]
    assert "?ms=" not in resultado["url"]


def test_si_falta_el_html_se_dice_donde(tmp_path: Path) -> None:
    with mock.patch.object(avatar, "ROSTRO", tmp_path / "no-esta.html"):
        resultado = avatar.run()

    assert resultado["success"] is False
    assert "no-esta.html" in resultado["error"]


def test_la_explicacion_saluda_por_su_nombre() -> None:
    with mock.patch("webbrowser.open"):
        resultado = avatar.run()

    assert "Eathan" in resultado["explanation"]
    assert "espacio" in resultado["explanation"]
