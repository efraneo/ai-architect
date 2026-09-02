"""Pasar la voz a texto con Whisper.

El reconocedor de Chrome entendía el español regular y mandaba el audio a
Google. Esto lo transcribe OpenAI y, sobre todo, **le pasa contexto**: los
nombres de los comandos son justo lo que hay que acertar, y es donde más
se equivocaba.

Ninguna prueba llama a la API.
"""

from __future__ import annotations

from unittest import mock

import pytest

from ai_architect.voz import escuchar


def respuesta(texto: str):
    return mock.Mock(text=texto)


# --- Lo que no puede pasar --------------------------------------------------


def test_sin_audio_no_se_llama_a_nadie() -> None:
    with mock.patch("openai.OpenAI") as cliente:
        salida = escuchar.transcribir(b"")

    cliente.assert_not_called()
    assert salida["error"] == "no llegó audio"


def test_un_audio_enorme_no_se_manda() -> None:
    """La API corta en 25 MB; enterarse después de subirlo es tarde."""
    with mock.patch("openai.OpenAI") as cliente:
        salida = escuchar.transcribir(b"x" * (escuchar.LIMITE_BYTES + 1))

    cliente.assert_not_called()
    assert "no cabe" in salida["error"]


def test_si_la_api_falla_no_revienta() -> None:
    """Un fallo al oír no puede tumbar la conversación entera."""
    with mock.patch("openai.OpenAI") as constructor:
        constructor.return_value.audio.transcriptions.create.side_effect = RuntimeError(
            "sin cuota"
        )

        salida = escuchar.transcribir(b"audio")

    assert salida["texto"] == ""
    assert "sin cuota" in salida["error"]


# --- Cómo se pide -----------------------------------------------------------


def test_transcribe_y_devuelve_el_texto() -> None:
    with mock.patch("openai.OpenAI") as constructor:
        constructor.return_value.audio.transcriptions.create.return_value = respuesta(
            "  revisa el proyecto  "
        )

        salida = escuchar.transcribir(b"audio")

    assert salida["texto"] == "revisa el proyecto"
    assert salida["modelo"] == escuchar.MODELOS[0]


def test_se_pide_en_espanol() -> None:
    """Sin decirlo, una orden corta puede transcribirse como si fuera inglés."""
    with mock.patch("openai.OpenAI") as constructor:
        crear = constructor.return_value.audio.transcriptions.create
        crear.return_value = respuesta("hola")

        escuchar.transcribir(b"audio")

    assert crear.call_args[1]["language"] == "es"


def test_se_le_pasa_el_vocabulario_del_proyecto() -> None:
    """Es lo que separa "revisa el repositorio" de "revista el repositorio"."""
    with mock.patch("openai.OpenAI") as constructor:
        crear = constructor.return_value.audio.transcriptions.create
        crear.return_value = respuesta("hola")

        escuchar.transcribir(b"audio")

    pista = crear.call_args[1]["prompt"]

    assert "revisa" in pista
    assert "changelog" in pista
    assert "cobertura" in pista


def test_si_el_primer_modelo_no_esta_se_usa_el_segundo() -> None:
    """`gpt-4o-transcribe` no está en todas las cuentas; `whisper-1` sí."""
    with mock.patch("openai.OpenAI") as constructor:
        crear = constructor.return_value.audio.transcriptions.create
        crear.side_effect = [RuntimeError("model_not_found"), respuesta("hola")]

        salida = escuchar.transcribir(b"audio")

    assert salida["texto"] == "hola"
    assert salida["modelo"] == "whisper-1"


def test_si_ninguno_responde_se_dice_el_ultimo_motivo() -> None:
    with mock.patch("openai.OpenAI") as constructor:
        crear = constructor.return_value.audio.transcriptions.create
        crear.side_effect = [RuntimeError("uno"), RuntimeError("dos")]

        salida = escuchar.transcribir(b"audio")

    assert salida["error"] == "dos"


# --- Si hay con qué oír -----------------------------------------------------


def test_sin_clave_no_hay_whisper(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with mock.patch("ai_architect.voz.hablar._asegurar_entorno"):
        assert escuchar.disponible() is False


def test_con_clave_si(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "algo")

    assert escuchar.disponible() is True


@pytest.mark.parametrize("orden", [0, 1])
def test_los_dos_modelos_son_de_transcripcion(orden: int) -> None:
    """Un descuido aquí manda el audio a un modelo que no sabe oír."""
    assert (
        "transcribe" in escuchar.MODELOS[orden] or "whisper" in escuchar.MODELOS[orden]
    )
