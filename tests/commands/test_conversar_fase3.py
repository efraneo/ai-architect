"""Fase 3 de la conversación: el nombre, la ventana y cortarlo a media frase.

Sin red, sin micrófono, sin modelo: `pide` y la voz se doblan.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from ai_architect.commands import conversar
from ai_architect.core import perfil


@pytest.fixture(autouse=True)
def limpio(tmp_path: Path):
    with mock.patch.object(perfil, "ARCHIVO", tmp_path / "perfil.json"):
        perfil.configurar("Efraín", archivo=tmp_path / "perfil.json")
        conversar.configurar_oido("libre")
        conversar._ultima_vez = 0.0
        conversar._ultimo_dicho = ""

        yield

    conversar.configurar_oido("libre")
    conversar._ultima_vez = 0.0
    conversar._ultimo_dicho = ""


def sin_voz() -> dict:
    return {"archivo": None, "motor": "", "segundos": 0.0, "texto": ""}


# --- El modo ---------------------------------------------------------------------


def test_por_defecto_hay_que_llamarlo() -> None:
    conversar.configurar_oido("nombre")

    para_mi, _ = conversar.dirigido_a_mi("revisa el proyecto", ahora=5000.0)

    assert not para_mi


def test_nombrado_atiende_y_abre_la_ventana() -> None:
    conversar.configurar_oido("nombre")

    para_mi, orden = conversar.dirigido_a_mi(
        "Architect, revisa el proyecto", ahora=5000.0
    )

    assert para_mi and orden == "revisa el proyecto"

    para_mi, orden = conversar.dirigido_a_mi("y pásalo a Word", ahora=5000.0 + 20)

    assert para_mi and orden == "y pásalo a Word"


def test_un_modo_desconocido_se_rechaza() -> None:
    with pytest.raises(ValueError):
        conversar.configurar_oido("a gritos")


def test_la_pagina_sabe_el_modo() -> None:
    conversar.configurar_oido("nombre")

    with mock.patch("ai_architect.voz.escuchar.disponible", return_value=False):
        pagina = conversar._componer(".")

    assert '"modo_oido": "nombre"' in pagina and '"nombre": "Architect"' in pagina


def test_el_aviso_explica_como_llamarlo() -> None:
    conversar.configurar_oido("nombre")

    assert "Architect, revisa" in conversar._como_llamarlo()
    assert "calla" in conversar._como_llamarlo()

    conversar.configurar_oido("libre")

    assert "sin más" in conversar._como_llamarlo()


# --- Callar -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "dicho", ["calla", "Cállate ya", "para", "espera un momento", "silencio", "basta"]
)
def test_lo_que_se_dice_para_que_se_calle(dicho: str) -> None:
    assert conversar.es_orden_de_parar(dicho)


@pytest.mark.parametrize("dicho", ["revisa el proyecto", "para qué sirve esto", ""])
def test_lo_que_no_es_callar(dicho: str) -> None:
    assert not conversar.es_orden_de_parar(dicho)


def test_mientras_habla_su_eco_se_descarta() -> None:
    conversar._ultimo_dicho = "El entorno está healthy. Provider ready, agents ready."

    with mock.patch.object(conversar.motor_de_voz, "callar") as callar:
        salida = conversar.atender_lo_oido(
            "el entorno esta healthy provider ready", ".", False, interrumpe=True
        )

    assert salida["error"] == "eco"
    callar.assert_not_called()


def test_si_le_dices_calla_mientras_habla_se_calla() -> None:
    conversar._ultimo_dicho = "una respuesta muy larga que no se acaba nunca"

    with mock.patch.object(
        conversar.motor_de_voz, "callar", return_value=True
    ) as callar:
        salida = conversar.atender_lo_oido(
            "Architect, calla", ".", False, interrumpe=True
        )

    assert salida["callado"] and salida["respuesta"] == ""
    callar.assert_called_once()
    assert conversar._ultimo_dicho == ""


def test_una_orden_nueva_mientras_habla_lo_corta_y_se_atiende() -> None:
    conversar._ultimo_dicho = "una respuesta muy larga que no se acaba nunca"

    with mock.patch.object(conversar.motor_de_voz, "callar", return_value=True):
        with mock.patch.object(
            conversar.motor_de_voz, "preparar", return_value=sin_voz()
        ):
            with mock.patch(
                "ai_architect.commands.pide.run",
                return_value={"success": True, "explanation": "Hecho."},
            ) as pide:
                salida = conversar.atender_lo_oido(
                    "Architect, mejor revisa las dependencias",
                    ".",
                    False,
                    interrumpe=True,
                )

                buzon = conversar._pendientes.pop(salida["resguardo"])
                respuesta = buzon.get(timeout=5)

    assert salida["interrumpido"] and respuesta["respuesta"] == "Hecho."
    assert pide.call_args.kwargs["frase"] == "mejor revisa las dependencias"


def test_en_modo_nombre_lo_ajeno_no_se_atiende_por_el_navegador() -> None:
    conversar.configurar_oido("nombre")

    with mock.patch("ai_architect.commands.pide.run") as pide:
        salida = conversar.atender_lo_oido("revisa el proyecto", ".", False)

    assert salida["ajeno"] and salida["oido"] == "revisa el proyecto"
    pide.assert_not_called()


def test_su_nombre_a_secas_se_contesta_con_un_dime() -> None:
    conversar.configurar_oido("nombre")

    with mock.patch.object(conversar.motor_de_voz, "preparar", return_value=sin_voz()):
        with mock.patch("ai_architect.commands.pide.run") as pide:
            salida = conversar.atender_lo_oido("Architect", ".", False)

    assert salida["respuesta"] == "Dime, Efraín." and salida["instantanea"]
    pide.assert_not_called()
    assert conversar._ultima_vez > 0


# --- La vía de Whisper -------------------------------------------------------------


def test_lo_oido_sin_texto_no_hace_nada() -> None:
    salida = conversar.atender_lo_oido("", ".", False, error="ruido")

    assert salida["respuesta"] == "" and salida["error"] == "ruido"


def test_un_trozo_corto_mientras_habla_es_eco() -> None:
    with mock.patch.object(conversar.motor_de_voz, "callar") as callar:
        salida = conversar.atender_lo_oido("buenas tardes", ".", False, interrumpe=True)

    assert salida["error"] == "eco"
    callar.assert_not_called()


def test_lo_oido_con_el_nombre_mientras_habla_lo_corta() -> None:
    conversar.configurar_oido("nombre")

    with mock.patch.object(conversar.motor_de_voz, "callar", return_value=True):
        salida = conversar.atender_lo_oido(
            "Arquitecto, calla", ".", False, interrumpe=True
        )

    assert salida["callado"]


def test_lo_oido_se_atiende_aparte_con_resguardo() -> None:
    with mock.patch.object(conversar.motor_de_voz, "preparar", return_value=sin_voz()):
        with mock.patch(
            "ai_architect.commands.pide.run",
            return_value={"success": True, "explanation": "Listo."},
        ):
            salida = conversar.atender_lo_oido("revisa el proyecto", ".", False)

            assert salida["resguardo"] and salida["oido"] == "revisa el proyecto"

            buzon = conversar._pendientes.pop(salida["resguardo"])
            respuesta = buzon.get(timeout=5)

    assert respuesta["respuesta"] == "Listo."


def test_lo_oido_ajeno_en_modo_nombre() -> None:
    conversar.configurar_oido("nombre")

    salida = conversar.atender_lo_oido("qué tal la reunión", ".", False)

    assert salida["ajeno"]


# --- El CLI ----------------------------------------------------------------------------


def test_sin_nombre_llega_al_comando() -> None:
    from ai_architect import cli

    with mock.patch.object(cli.conversar, "run", return_value={"success": True}) as run:
        with mock.patch("sys.argv", ["ai-architect", "conversar", "--sin-nombre"]):
            cli.main()

    assert run.call_args.kwargs["nombre"] is False


def test_por_defecto_conversar_pide_el_nombre() -> None:
    from ai_architect import cli

    with mock.patch.object(cli.conversar, "run", return_value={"success": True}) as run:
        with mock.patch("sys.argv", ["ai-architect", "conversar"]):
            cli.main()

    assert run.call_args.kwargs["nombre"] is True
