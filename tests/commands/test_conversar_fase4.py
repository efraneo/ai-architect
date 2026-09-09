"""Fase 4 de la conversación: el permiso por voz o por botón, el progreso y la
ventana flotante. Sin red, sin micrófono, sin modelo."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from ai_architect.agente import progreso
from ai_architect.commands import avatar, conversar, pide_orden
from ai_architect.core import perfil


@pytest.fixture(autouse=True)
def limpio(tmp_path: Path):
    with mock.patch.object(perfil, "ARCHIVO", tmp_path / "perfil.json"):
        perfil.configurar("Efraín", archivo=tmp_path / "perfil.json")
        conversar.configurar_oido("libre")
        conversar._permiso_pendiente = []
        conversar._ultima_vez = 0.0
        conversar._ultimo_dicho = ""

        yield

    conversar._permiso_pendiente = []
    conversar.configurar_oido("libre")
    progreso.desuscribir(conversar._bitacora.anotar)


def sin_voz() -> dict:
    return {"archivo": None, "motor": "", "segundos": 0.0, "texto": ""}


def con_pendientes() -> dict:
    return {
        "success": True,
        "executed": True,
        "command": "hacer",
        "explanation": "Propongo cambiar a por 2.",
        "result": {
            "pending": ["abcdef12 · escribir m.py (6 caracteres)"],
            "pending_ids": ["abcdef1234"],
        },
    }


# --- Decidir ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "dicho", ["sí", "Sí, hazlo", "dale", "adelante", "vale", "sí claro"]
)
def test_lo_que_es_un_si(dicho: str) -> None:
    assert conversar.decidir_permiso(dicho) == "si"


@pytest.mark.parametrize(
    "dicho", ["no", "No, déjalo", "cancela", "mejor no", "todavía no"]
)
def test_lo_que_es_un_no(dicho: str) -> None:
    assert conversar.decidir_permiso(dicho) == "no"


@pytest.mark.parametrize(
    "dicho", ["revisa el proyecto", "", "sí pero antes revisa las pruebas"]
)
def test_lo_que_no_es_una_respuesta(dicho: str) -> None:
    assert conversar.decidir_permiso(dicho) == ""


# --- El ciclo entero --------------------------------------------------------------


def test_lo_que_quedo_en_cola_se_pregunta() -> None:
    with mock.patch("ai_architect.commands.pide.run", return_value=con_pendientes()):
        with mock.patch.object(
            conversar.motor_de_voz, "preparar", return_value=sin_voz()
        ):
            salida = conversar.atender("cambia a por 2", ".", si=False)

    assert salida["permiso"] == ["abcdef12 · escribir m.py (6 caracteres)"]
    assert "¿Los aplico?" in salida["respuesta"]
    assert conversar.hay_permiso_pendiente()


def test_un_si_aplica_lo_pendiente() -> None:
    conversar._permiso_pendiente = [
        {"id": "abcdef1234", "descripcion": "escribir m.py"}
    ]

    with mock.patch.object(
        conversar.pendientes,
        "aprobar",
        return_value={"success": True, "done": ["✓ escribir m.py: ok"]},
    ) as aprobar:
        with mock.patch.object(
            conversar.motor_de_voz, "preparar", return_value=sin_voz()
        ):
            with mock.patch("ai_architect.commands.pide.run") as pide:
                salida = conversar.atender("sí", ".", si=False)

    aprobar.assert_called_once_with("abcdef1234")
    pide.assert_not_called()
    assert salida["permiso_resuelto"] == "si" and "apliqué 1" in salida["respuesta"]
    assert not conversar.hay_permiso_pendiente()


def test_un_no_lo_descarta() -> None:
    conversar._permiso_pendiente = [
        {"id": "abcdef1234", "descripcion": "escribir m.py"}
    ]

    with mock.patch.object(
        conversar.pendientes, "rechazar", return_value={"success": True}
    ) as r:
        with mock.patch.object(
            conversar.motor_de_voz, "preparar", return_value=sin_voz()
        ):
            salida = conversar.atender("no", ".", si=False)

    r.assert_called_once_with("abcdef1234")
    assert salida["permiso_resuelto"] == "no" and "no toqué nada" in salida["respuesta"]


def test_otra_orden_no_se_confunde_con_la_respuesta() -> None:
    conversar._permiso_pendiente = [
        {"id": "abcdef1234", "descripcion": "escribir m.py"}
    ]

    with mock.patch(
        "ai_architect.commands.pide.run",
        return_value={"success": True, "explanation": "Hecho."},
    ) as pide:
        with mock.patch.object(
            conversar.motor_de_voz, "preparar", return_value=sin_voz()
        ):
            salida = conversar.atender("revisa las dependencias", ".", si=False)

    pide.assert_called_once()
    assert salida["respuesta"] == "Hecho." and conversar.hay_permiso_pendiente()


def test_si_falla_alguno_se_dice() -> None:
    conversar._permiso_pendiente = [
        {"id": "a1", "descripcion": "uno"},
        {"id": "b2", "descripcion": "dos"},
    ]

    respuestas = [
        {"success": True, "done": ["✓ uno"]},
        {"success": True, "done": ["✗ dos: no se pudo"]},
    ]

    with mock.patch.object(conversar.pendientes, "aprobar", side_effect=respuestas):
        with mock.patch.object(
            conversar.motor_de_voz, "preparar", return_value=sin_voz()
        ):
            salida = conversar.resolver_permiso("si")

    assert "1 de 2" in salida["respuesta"]


def test_sin_nada_pendiente_se_dice() -> None:
    with mock.patch.object(conversar.motor_de_voz, "preparar", return_value=sin_voz()):
        salida = conversar.resolver_permiso("si")

    assert "nada pendiente" in salida["respuesta"]


def test_el_progreso_se_puede_pedir_desde_un_numero() -> None:
    progreso.suscribir(conversar._bitacora.anotar)
    conversar._bitacora.limpiar()
    antes = conversar._bitacora.ultimo

    progreso.avisar("fase", fase="trabajando")
    progreso.avisar("herramienta_inicio", herramienta="file_read", argumentos="a.py")

    salida = conversar.progreso_desde(antes)

    assert [a["tipo"] for a in salida["avisos"]] == ["fase", "herramienta_inicio"]
    assert salida["n"] == antes + 2
    assert conversar.progreso_desde(salida["n"])["avisos"] == []


# --- pide le pasa a hacer lo que necesita -------------------------------------------


def test_pide_arma_los_argumentos_que_hacer_lee() -> None:
    args = pide_orden._argumentos({"instruction": "examina y corrige"}, ".", si=True)

    assert args.si is True and args.frase is None
    assert args.decir is False and args.cara is False
    assert args.instruction == "examina y corrige"


# --- La ventana flotante --------------------------------------------------------------


def test_sin_pywebview_se_avisa_y_se_abre_el_navegador(capsys) -> None:
    servidor = mock.Mock()

    with mock.patch.object(
        conversar, "_levantar", return_value=(servidor, "http://x/")
    ):
        with mock.patch.object(avatar, "hay_ventana_flotante", return_value=False):
            with mock.patch("webbrowser.open") as abrir:
                salida = conversar.run(".", servir_para_siempre=False, flotante=True)

    abrir.assert_called_once_with("http://x/")
    assert salida["floating"] is False
    assert "pywebview" in capsys.readouterr().out


def test_con_pywebview_no_se_abre_el_navegador() -> None:
    servidor = mock.Mock()

    with mock.patch.object(
        conversar, "_levantar", return_value=(servidor, "http://x/")
    ):
        with mock.patch.object(avatar, "hay_ventana_flotante", return_value=True):
            with mock.patch("webbrowser.open") as abrir:
                salida = conversar.run(".", servir_para_siempre=False, flotante=True)

    abrir.assert_not_called()
    assert salida["floating"] is True


def test_la_ventana_flotante_usa_pywebview_si_esta() -> None:
    falso = mock.Mock()

    with mock.patch.dict("sys.modules", {"webview": falso}):
        assert avatar.hay_ventana_flotante()
        assert avatar.ventana_flotante("http://x/") is True

    falso.create_window.assert_called_once()
    assert falso.create_window.call_args.kwargs["on_top"] is True
    assert falso.create_window.call_args.kwargs["frameless"] is True
    falso.start.assert_called_once()


def test_sin_pywebview_la_ventana_dice_que_no() -> None:
    with mock.patch.dict("sys.modules", {"webview": None}):
        assert not avatar.hay_ventana_flotante()
        assert avatar.ventana_flotante("http://x/") is False


def test_flotante_llega_desde_el_cli() -> None:
    from ai_architect import cli

    with mock.patch.object(cli.conversar, "run", return_value={"success": True}) as run:
        with mock.patch("sys.argv", ["ai-architect", "conversar", "--flotante"]):
            cli.main()

    assert run.call_args.kwargs["flotante"] is True


# --- El audio suena en la página -----------------------------------------------------


def test_entregar_convierte_el_archivo_en_url(tmp_path: Path) -> None:
    wav = tmp_path / "v.wav"
    wav.write_bytes(b"RIFFxxxx")

    salida, sonido = conversar.entregar(
        {"respuesta": "hola", "_audio": {"archivo": wav, "segundos": 1.0}}
    )

    assert sonido is None and salida["audio"].startswith("/audio?t=")
    assert conversar.audio_preparado(salida["audio"].split("t=")[1]) == b"RIFFxxxx"
    assert "_audio" not in salida


def test_entregar_devuelve_el_sonido_si_no_hay_archivo() -> None:
    salida, sonido = conversar.entregar(
        {
            "respuesta": "hola",
            "_audio": {"archivo": None, "motor": "windows", "texto": "hola"},
        }
    )

    assert sonido == {"archivo": None, "motor": "windows", "texto": "hola"}
    assert "audio" not in salida


def test_entregar_sin_audio_no_hace_nada() -> None:
    assert conversar.entregar({"respuesta": "x"}) == ({"respuesta": "x"}, None)


def test_sonar_aqui_reproduce_en_el_servidor(tmp_path: Path) -> None:
    wav = tmp_path / "v.wav"
    wav.write_bytes(b"RIFFxxxx")
    salida, _ = conversar.entregar({"_audio": {"archivo": wav}})
    token = salida["audio"].split("t=")[1]

    with mock.patch.object(conversar.motor_de_voz, "emitir") as emitir:
        assert conversar.sonar_aqui(token)

        for _ in range(50):
            if emitir.called:
                break

            import time

            time.sleep(0.02)

    assert emitir.called and str(emitir.call_args.args[0]["archivo"]).endswith(".wav")
    assert not conversar.sonar_aqui("no-existe")


# --- De punta a punta por HTTP -------------------------------------------------------------


def test_orden_por_http_con_resguardo_y_audio_en_la_pagina(tmp_path: Path) -> None:
    """La vía del navegador: POST /orden → resguardo → GET /respuesta trae la URL
    del audio → GET /audio devuelve el WAV. Nada suena en el servidor."""
    import json
    import urllib.request

    from ai_architect.voz import hablar as voz

    wav = tmp_path / "voz.wav"
    voz._escribir_wav(wav, b"\x00\x00" * 2400)

    preparado = {"archivo": wav, "motor": "piper", "segundos": 0.1, "texto": "Hecho."}

    with mock.patch.object(conversar.motor_de_voz, "preparar", return_value=preparado):
        with mock.patch.object(conversar.motor_de_voz, "emitir") as emitir:
            with mock.patch(
                "ai_architect.commands.pide.run",
                return_value={"success": True, "explanation": "Hecho."},
            ):
                servidor, url = conversar._levantar("<html>", ".", False)

                assert servidor is not None, "el puerto 8731 está ocupado"

                import threading

                threading.Thread(target=servidor.serve_forever, daemon=True).start()

                try:
                    peticion = urllib.request.Request(
                        url + "orden",
                        data=json.dumps({"texto": "revisa el proyecto"}).encode(),
                        headers={"Content-Type": "application/json"},
                    )
                    primera = json.loads(
                        urllib.request.urlopen(peticion, timeout=5).read()
                    )

                    assert (
                        primera["resguardo"] and primera["oido"] == "revisa el proyecto"
                    )

                    final = json.loads(
                        urllib.request.urlopen(
                            url + "respuesta?r=" + primera["resguardo"], timeout=10
                        ).read()
                    )

                    assert final["respuesta"] == "Hecho." and final["audio"].startswith(
                        "/audio?t="
                    )
                    assert "_audio" not in final

                    sonido = urllib.request.urlopen(url + final["audio"][1:], timeout=5)

                    assert sonido.headers["Content-Type"] == "audio/wav"
                    assert sonido.read()[:4] == b"RIFF"

                finally:
                    conversar._apagar(servidor)
                    servidor.shutdown()

    emitir.assert_not_called()


def test_por_voz_no_hay_coletilla() -> None:
    from ai_architect.commands import pide

    try:
        pide.conciso(True)
        pide.reiniciar_saludo()
        primera = pide._con_trato("Son las nueve.")
        segunda = pide._con_trato("Hecho.")

    finally:
        pide.conciso(False)

    assert "En qué te puedo ayudar" not in primera and "Son las nueve." in primera
    assert primera.count("\n") >= 1  # el saludo, solo la primera vez
    assert segunda == "Hecho."
    assert "En qué te puedo ayudar" in pide._con_trato("Escribiendo sí.")


def test_conversar_enciende_el_modo_conciso_y_calienta_el_oido() -> None:
    from ai_architect.commands import pide

    servidor = mock.Mock()

    with mock.patch.object(
        conversar, "_levantar", return_value=(servidor, "http://x/")
    ):
        with mock.patch("webbrowser.open"):
            with mock.patch("ai_architect.voz.escuchar.calentar") as calentar:
                conversar.run(".", servir_para_siempre=False)

    calentar.assert_called_once()
    assert pide._conciso is True
    pide.conciso(False)
