"""Cuarta prueba real: abrir programas, mejoras pedidas de viva voz, cerrar de más
formas, el registro con la respuesta de verdad y la ventana tras hablar."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from ai_architect import autoreparacion
from ai_architect.commands import abrir, conversar, pide, respuestas
from ai_architect.core import perfil


@pytest.fixture(autouse=True)
def _perfil(tmp_path: Path, monkeypatch):
    archivo = tmp_path / "perfil.json"
    monkeypatch.setattr(perfil, "ARCHIVO", archivo)
    perfil.configurar("Efraín", archivo=archivo)
    conversar._ultima_orden = ""
    conversar._ultimo_dicho = ""
    conversar._ultima_vez = 0.0
    conversar.configurar_oido("libre")
    pide.reiniciar_saludo()


# --- Abrir programas -----------------------------------------------------------------


def test_abre_programas_conocidos() -> None:
    with mock.patch.object(abrir, "_lanzar") as lanzar:
        assert abrir.abrir("Word")["ok"]
        assert abrir.abrir("google chrome")["ok"]
        assert (
            abrir.abrir("el bloc de notas")["ok"] or abrir.abrir("bloc de notas")["ok"]
        )

    lanzados = [c.args[0] for c in lanzar.call_args_list]
    assert "winword" in lanzados and "chrome" in lanzados and "notepad" in lanzados


def test_abre_una_web_y_una_ruta(tmp_path: Path) -> None:
    with mock.patch.object(abrir.webbrowser, "open") as web:
        assert abrir.abrir("xentris.tech")["ok"]

    assert web.call_args.args[0] == "https://xentris.tech"

    archivo = tmp_path / "notas.txt"
    archivo.write_text("x", encoding="utf-8")

    with mock.patch.object(abrir, "_lanzar") as lanzar:
        assert abrir.abrir(str(archivo))["ok"]

    assert lanzar.call_args.args[0] == str(archivo)


def test_lo_que_no_existe_se_dice() -> None:
    with mock.patch.object(abrir, "_lanzar", side_effect=OSError("no")):
        salida = abrir.abrir("programa inventado")

    assert not salida["ok"] and "No encontré" in salida["explicacion"]


def test_por_voz_abre_word_sin_modelo() -> None:
    with mock.patch.object(abrir, "_lanzar") as lanzar:
        salida = respuestas.responder("Abre Word.")

    assert salida is not None and "Abriendo word" in salida["respuesta"]
    assert lanzar.call_args.args[0] == "winword"


def test_abrir_el_archivo_no_es_un_programa() -> None:
    assert respuestas.responder("abre el archivo main.py") is None


def test_abrir_en_el_celular_no_es_del_pc() -> None:
    with mock.patch.object(abrir, "_lanzar") as lanzar:
        respuestas.responder("abre WhatsApp en el celular")

    lanzar.assert_not_called()


# --- Mejoras pedidas -----------------------------------------------------------------------


def test_quiero_que_puedas_se_apunta_como_mejora() -> None:
    conversar._ultima_orden = "abre Word"

    salida = respuestas.responder("Quiero que puedas abrir Word")

    assert (
        salida is not None
        and "mejora" in salida["respuesta"]
        and "adelante" in salida["respuesta"]
    )
    averia = autoreparacion.pendiente()
    assert averia["comando"] == "mejora"
    assert "TU PROPIO CÓDIGO" in autoreparacion.orden_de_reparacion(averia)
    assert "capacidad nueva" in autoreparacion.orden_de_reparacion(averia)


def test_adelante_con_una_mejora_lo_dice_asi(tmp_path: Path, monkeypatch) -> None:
    f = tmp_path / "fuente"
    f.mkdir()
    (f / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    monkeypatch.setenv("ARCHITECT_FUENTE", str(f))
    autoreparacion.registrar("mejora", "abrir programas", "capacidad")

    with mock.patch(
        "ai_architect.commands.hacer.run",
        return_value={"explanation": "Añadí abrir.py."},
    ):
        with mock.patch.object(
            autoreparacion, "correr_pruebas", return_value={"ok": True, "resumen": "ok"}
        ):
            dicho = autoreparacion.adelante(en_hilo=False)

    assert "programo la mejora" in dicho
    assert "Mejora" in autoreparacion.ultimo_informe()


# --- Cerrar y registro -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "dicho", ["Cerrar", "No, cierra.", "Despídete.", "ya puedes cerrar"]
)
def test_mas_formas_de_cerrar(dicho: str) -> None:
    salida = respuestas.responder(dicho)

    assert salida is not None and salida.get("cerrar") is True


def test_el_registro_guarda_la_respuesta_y_no_el_saludo() -> None:
    assert conversar._resumen(
        "Buenas noches, Efraín.\n\nHoy es lunes 8 de septiembre."
    ) == ("Hoy es lunes 8 de septiembre.")
    assert conversar._resumen("Cerrada.") == "Cerrada."
    assert conversar._resumen(
        "Buenas tardes, Efraín.\n\nSon las cinco.\n\n¿En qué te puedo ayudar ahora, Efraín?"
    ) == ("Son las cinco.")


def test_toda_respuesta_queda_para_pasarla_a_word() -> None:
    from ai_architect.commands import crear

    with mock.patch.object(crear, "recordar") as recordar:
        pide.run(".", frase="qué hora es")

    assert recordar.called and "Son las" in recordar.call_args.args[1]


def test_si_la_pagina_no_interrumpe_la_ventana_ya_esta_abierta() -> None:
    conversar.configurar_oido("nombre")
    conversar._ultima_vez = (
        conversar.time.monotonic() + 30
    )  # el audio «seguía» según la estimación

    with mock.patch.object(
        conversar.motor_de_voz, "preparar", return_value={"segundos": 0}
    ):
        with mock.patch(
            "ai_architect.commands.pide.run",
            return_value={"success": True, "explanation": "Lunes."},
        ):
            salida = conversar.atender_lo_oido(
                "¿qué día es hoy?", ".", False, interrumpe=False
            )

            assert salida.get("resguardo"), salida
            conversar._pendientes.pop(salida["resguardo"]).get(timeout=5)
