"""Cortarlo a media frase y no quedarse mudo cuando un motor falla (fase 3)."""

from __future__ import annotations

import subprocess
import sys
import threading
import time
from pathlib import Path
from unittest import mock

import pytest

from ai_architect.core import perfil
from ai_architect.voz import hablar as voz


@pytest.fixture(autouse=True)
def aislado(tmp_path: Path):
    voz.reanimar()

    with mock.patch.object(perfil, "ARCHIVO", tmp_path / "perfil.json"):
        yield

    voz.reanimar()


def _motores(**cuales: bool) -> dict:
    return {
        n: {"disponible": cuales.get(n, False), "voz": n, "nota": ""}
        for n in ("piper", "openai", "windows")
    }


# --- Repliegue de motores -------------------------------------------------------


def test_si_el_motor_falla_se_pasa_al_siguiente(tmp_path: Path) -> None:
    wav = tmp_path / "voz.wav"
    voz._escribir_wav(wav, b"\x00\x00" * 2400)

    with mock.patch.object(
        voz, "motores", return_value=_motores(piper=True, openai=True)
    ):
        with mock.patch.object(
            voz, "_wav_piper", side_effect=RuntimeError("piper roto")
        ):
            with mock.patch.object(voz, "_wav_openai", return_value=wav):
                listo = voz.preparar("hola")

    assert listo["motor"] == "openai" and listo["archivo"] == wav
    assert voz.caido("piper") and not voz.caido("openai")


def test_el_caido_queda_en_cuarentena_y_luego_vuelve() -> None:
    voz.descartar("piper")

    with mock.patch.object(
        voz, "motores", return_value=_motores(piper=True, openai=True)
    ):
        assert voz.elegir() == "openai"

        voz._caidos["piper"] = time.monotonic() - voz.CUARENTENA - 1

        assert voz.elegir() == "piper"


def test_si_todos_fallan_se_dice_sin_lanzar() -> None:
    with mock.patch.object(
        voz, "motores", return_value=_motores(piper=True, openai=True)
    ):
        with mock.patch.object(voz, "_wav_piper", side_effect=RuntimeError("uno")):
            with mock.patch.object(voz, "_wav_openai", side_effect=RuntimeError("dos")):
                listo = voz.preparar("hola")

    assert listo["archivo"] is None and listo["motivo"] == "dos"


def test_hablar_tambien_se_repliega() -> None:
    with mock.patch.object(
        voz, "motores", return_value=_motores(piper=True, openai=True)
    ):
        with mock.patch.object(
            voz, "_con_piper", side_effect=RuntimeError("piper roto")
        ):
            with mock.patch.object(voz, "_con_openai") as openai:
                salida = voz.hablar("hola")

    assert salida["hablado"] and salida["motor"] == "openai"
    openai.assert_called_once()


def test_reanimar_olvida_los_fallos() -> None:
    voz.descartar("piper")
    voz.reanimar()

    assert not voz.caido("piper")


# --- Callar -----------------------------------------------------------------------


def test_sin_nada_sonando_callar_no_hace_nada() -> None:
    assert voz.callar() is False and not voz.esta_hablando()


def test_callar_mata_el_proceso_que_estaba_sonando() -> None:
    """Se simula un reproductor con un proceso que dormiría cinco segundos."""
    proceso = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(5)"])

    def sonar() -> None:
        with voz._sonando():
            voz._esperar(proceso)

    hilo = threading.Thread(target=sonar)
    inicio = time.monotonic()
    hilo.start()

    for _ in range(50):
        if voz.esta_hablando():
            break

        time.sleep(0.02)

    assert voz.esta_hablando()
    assert voz.callar() is True

    hilo.join(timeout=3)

    assert not hilo.is_alive()
    assert time.monotonic() - inicio < 3
    assert proceso.poll() is not None
    assert not voz.esta_hablando()
