"""Conversar: hablarle en vez de escribirle.

Lo que se fija aquí es lo que no se ve mirando la pantalla:

- que una orden dicha en voz alta **no** autoriza a tocar archivos,
- que la respuesta viaja con la duración exacta del audio, o la cara
  gesticula en el vacío,
- y que el audio no suena antes de contestar, o la boca llega tarde.

Ninguna prueba abre un puerto, un micrófono ni un proveedor.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from ai_architect.commands import conversar
from ai_architect.core import perfil


@pytest.fixture(autouse=True)
def sin_perfil_real(tmp_path: Path):
    archivo = tmp_path / "perfil.json"

    with mock.patch.object(perfil, "ARCHIVO", archivo):
        perfil.configurar("Efraín", archivo=archivo)
        yield


def respondiendo(explicacion: str = "Todo en orden.", **extra):
    """`pide` ya resuelto, sin llamar a ningún modelo."""
    return {"success": True, "explanation": explicacion, **extra}


# --- La página --------------------------------------------------------------


def test_la_pagina_arranca_en_modo_conversacion() -> None:
    """Sin esto el navegador no enciende el micrófono."""
    pagina = conversar._componer(".")

    datos = json.loads(pagina.split("window.DATOS_ARQUITECTO = ")[-1].split(";")[0])

    assert datos["modo"] == "conversacion"


def test_la_pagina_sabe_de_que_proyecto_se_habla() -> None:
    pagina = conversar._componer("C:/proyecto")

    assert "C:/proyecto" in pagina


# --- Atender una orden ------------------------------------------------------


def test_una_orden_dicha_se_ejecuta() -> None:
    with mock.patch(
        "ai_architect.commands.pide.run", return_value=respondiendo()
    ) as ejecutar:
        with mock.patch.object(
            conversar.motor_de_voz,
            "preparar",
            return_value={"texto": "Todo en orden.", "segundos": 1.4},
        ):
            salida = conversar.atender("revisa el proyecto", ".", si=False)

    assert ejecutar.call_args[1]["frase"] == "revisa el proyecto"
    assert salida["respuesta"] == "Todo en orden."


def test_la_duracion_viaja_con_la_respuesta() -> None:
    """La cara la necesita para gesticular justo mientras suena."""
    with mock.patch("ai_architect.commands.pide.run", return_value=respondiendo()):
        with mock.patch.object(
            conversar.motor_de_voz,
            "preparar",
            return_value={"texto": "Todo en orden.", "segundos": 2.5},
        ):
            salida = conversar.atender("revisa", ".", si=False)

    assert salida["ms"] == 2500


def test_por_voz_no_se_autoriza_a_tocar_archivos() -> None:
    """Que una orden llegue hablada no la convierte en un permiso."""
    with mock.patch(
        "ai_architect.commands.pide.run", return_value=respondiendo()
    ) as ejecutar:
        with mock.patch.object(
            conversar.motor_de_voz, "preparar", return_value={"segundos": 0}
        ):
            conversar.atender("arregla los except", ".", si=False)

    assert ejecutar.call_args[1]["si"] is False


def test_el_permiso_se_da_al_abrir_la_conversacion() -> None:
    """Por voz no hay forma de teclear --si en mitad de una frase."""
    with mock.patch(
        "ai_architect.commands.pide.run", return_value=respondiendo()
    ) as ejecutar:
        with mock.patch.object(
            conversar.motor_de_voz, "preparar", return_value={"segundos": 0}
        ):
            conversar.atender("arregla los except", ".", si=True)

    assert ejecutar.call_args[1]["si"] is True


def test_un_silencio_no_llama_a_nadie() -> None:
    with mock.patch("ai_architect.commands.pide.run") as ejecutar:
        salida = conversar.atender("   ", ".", si=False)

    ejecutar.assert_not_called()
    assert salida["ms"] == 0


def test_una_transcripcion_enorme_se_recorta() -> None:
    """Un micro abierto en una reunión no es una orden."""
    with mock.patch(
        "ai_architect.commands.pide.run", return_value=respondiendo()
    ) as ejecutar:
        with mock.patch.object(
            conversar.motor_de_voz, "preparar", return_value={"segundos": 0}
        ):
            conversar.atender("hola " * 5000, ".", si=False)

    assert len(ejecutar.call_args[1]["frase"]) <= conversar.LIMITE


def test_si_pide_falla_se_dice_en_voz_alta() -> None:
    """Callarse ante un error deja al usuario mirando una cara muda."""
    with mock.patch(
        "ai_architect.commands.pide.run",
        return_value={"success": False, "error": "el proveedor falló"},
    ):
        with mock.patch.object(
            conversar.motor_de_voz,
            "preparar",
            return_value={"texto": "el proveedor falló", "segundos": 1.0},
        ) as preparar:
            salida = conversar.atender("revisa", ".", si=False)

    assert "el proveedor falló" in salida["respuesta"]
    assert "el proveedor falló" in preparar.call_args[0][0]


def test_el_audio_no_se_reproduce_al_atender() -> None:
    """Suena después de contestar: si no, la boca empieza tarde."""
    with mock.patch("ai_architect.commands.pide.run", return_value=respondiendo()):
        with mock.patch.object(
            conversar.motor_de_voz, "preparar", return_value={"segundos": 1.0}
        ):
            with mock.patch.object(conversar.motor_de_voz, "emitir") as sonar:
                salida = conversar.atender("revisa", ".", si=False)

    sonar.assert_not_called()
    assert "_audio" in salida, "el audio va aparte, para emitirlo tras responder"


# --- El servidor ------------------------------------------------------------


def test_el_puerto_ocupado_se_dice_claro() -> None:
    with mock.patch.object(conversar, "_levantar", return_value=(None, "")):
        with mock.patch("webbrowser.open") as abrir:
            resultado = conversar.run(".")

    abrir.assert_not_called()
    assert resultado["success"] is False
    assert "ocupado" in resultado["error"]


def test_abre_la_cara_y_deja_el_servidor_vivo() -> None:
    servidor = mock.Mock()

    with mock.patch.object(
        conversar, "_levantar", return_value=(servidor, "http://x/")
    ):
        with mock.patch("webbrowser.open") as abrir:
            resultado = conversar.run(".", servir_para_siempre=False)

    abrir.assert_called_once_with("http://x/")
    servidor.server_close.assert_not_called()
    assert resultado["success"] is True


def test_si_falta_el_html_se_dice_donde(tmp_path: Path) -> None:
    with mock.patch.object(conversar.avatar, "ROSTRO", tmp_path / "no-esta.html"):
        resultado = conversar.run(".")

    assert resultado["success"] is False
    assert "no-esta.html" in resultado["error"]


def test_ctrl_c_cierra_el_servidor() -> None:
    """Un puerto fijo que queda abierto bloquea la siguiente conversación."""
    servidor = mock.Mock()
    servidor.serve_forever.side_effect = KeyboardInterrupt

    with mock.patch.object(
        conversar, "_levantar", return_value=(servidor, "http://x/")
    ):
        with mock.patch("webbrowser.open"):
            conversar.run(".")

    servidor.server_close.assert_called_once()
