"""Tests for ``ClaudeProvider``.

The provider had no tests at all, and it was broken: it forwarded
``temperature`` to ``messages.create()``, a parameter Anthropic removed from
its current models, and its default model (``claude-sonnet-4``) does not
exist. Every call raised ``TypeError``.

These tests pin down the two decisions that came out of that fix:

* ``temperature`` stays in the signature, because it is part of the
  ``BaseProvider`` contract, but it is **not** forwarded to the API.
* The answer is looked up by block type, not by position: with thinking
  enabled the first block is reasoning, not text.

None of them hit the network.
"""

from __future__ import annotations

import os
from typing import Any
from unittest import mock

import pytest

from ai_architect.providers.claude_provider import (
    DEFAULT_EFFORT,
    MAX_TOKENS,
    ClaudeProvider,
)


class BloqueFalso:
    """Imitates a content block of the response."""

    def __init__(self, tipo: str, texto: str = "") -> None:
        self.type = tipo
        self.text = texto
        if tipo == "thinking":
            self.thinking = texto


class RespuestaFalsa:
    def __init__(self, bloques: list[BloqueFalso]) -> None:
        self.content = bloques


@pytest.fixture
def proveedor() -> ClaudeProvider:
    """A provider with a client, without touching the real environment."""
    with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "clave-de-prueba"}):
        return ClaudeProvider()


# --- Modelo por defecto -----------------------------------------------------


def test_el_modelo_por_defecto_existe() -> None:
    """It used to be ``claude-sonnet-4``, which is not a real model."""
    with mock.patch.dict(os.environ, {}, clear=True):
        assert ClaudeProvider().default_model() == "claude-opus-5"


def test_el_modelo_se_puede_fijar_por_entorno() -> None:
    with mock.patch.dict(os.environ, {"CLAUDE_MODEL": "claude-haiku-4-5"}):
        assert ClaudeProvider().default_model() == "claude-haiku-4-5"


# --- Disponibilidad ---------------------------------------------------------


def test_sin_clave_no_esta_disponible() -> None:
    with mock.patch.dict(os.environ, {}, clear=True):
        assert ClaudeProvider().available() is False


def test_con_clave_esta_disponible(proveedor: ClaudeProvider) -> None:
    assert proveedor.available() is True


def test_generar_sin_clave_falla_con_un_mensaje_claro() -> None:
    with mock.patch.dict(os.environ, {}, clear=True):
        proveedor = ClaudeProvider()

        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            proveedor.generate("hola")


# --- temperature -> effort --------------------------------------------------


@pytest.mark.parametrize(
    ("temperatura", "esperado"),
    [
        (0.0, "xhigh"),
        (0.10, "xhigh"),
        (0.15, "xhigh"),
        (0.20, "high"),
        (0.50, "high"),
        (0.70, "medium"),
        (1.00, "medium"),
    ],
)
def test_la_temperatura_se_traduce_a_esfuerzo(
    temperatura: float, esperado: str
) -> None:
    """A low temperature means "be precise", and that maps to *more* effort."""
    assert ClaudeProvider.effort_for(temperatura) == esperado


def test_el_esfuerzo_siempre_es_un_valor_que_la_api_acepta() -> None:
    validos = {"low", "medium", "high", "xhigh", "max"}

    for decima in range(0, 21):
        assert ClaudeProvider.effort_for(decima / 10) in validos


# --- La llamada a la API ----------------------------------------------------


def llamada_de(proveedor: ClaudeProvider, **kwargs: Any) -> dict[str, Any]:
    """Run ``generate`` with a fake client and return the arguments it sent."""
    crear = mock.Mock(return_value=RespuestaFalsa([BloqueFalso("text", "respuesta")]))
    proveedor.client = mock.Mock()  # type: ignore[assignment]
    proveedor.client.messages.create = crear

    proveedor.generate("un prompt", **kwargs)

    return crear.call_args.kwargs


def test_no_envia_temperature_a_la_api(proveedor: ClaudeProvider) -> None:
    """The regression: Anthropic removed it and the SDK rejects it."""
    enviado = llamada_de(proveedor, temperature=0.1)

    assert "temperature" not in enviado
    assert "top_p" not in enviado
    assert "top_k" not in enviado


def test_acepta_temperature_por_el_contrato_de_baseprovider(
    proveedor: ClaudeProvider,
) -> None:
    """The other providers do use it, so the call must not fail."""
    enviado = llamada_de(proveedor, temperature=0.1)

    assert enviado["output_config"] == {"effort": "xhigh"}


def test_el_esfuerzo_explicito_manda_sobre_la_temperatura(
    proveedor: ClaudeProvider,
) -> None:
    enviado = llamada_de(proveedor, temperature=0.9, effort="max")

    assert enviado["output_config"] == {"effort": "max"}


def test_sin_argumentos_usa_el_esfuerzo_por_defecto(proveedor: ClaudeProvider) -> None:
    enviado = llamada_de(proveedor)

    assert enviado["output_config"] == {"effort": DEFAULT_EFFORT}


def test_envia_el_modelo_el_tope_y_el_prompt(proveedor: ClaudeProvider) -> None:
    enviado = llamada_de(proveedor)

    assert enviado["model"] == proveedor.model
    assert enviado["max_tokens"] == MAX_TOKENS
    assert enviado["messages"] == [{"role": "user", "content": "un prompt"}]


# --- Lectura de la respuesta ------------------------------------------------


def responder_con(proveedor: ClaudeProvider, bloques: list[BloqueFalso]) -> str:
    proveedor.client = mock.Mock()  # type: ignore[assignment]
    proveedor.client.messages.create = mock.Mock(return_value=RespuestaFalsa(bloques))

    return proveedor.generate("hola")


def test_devuelve_el_texto(proveedor: ClaudeProvider) -> None:
    assert responder_con(proveedor, [BloqueFalso("text", "  hola  ")]) == "hola"


def test_salta_el_bloque_de_razonamiento(proveedor: ClaudeProvider) -> None:
    """The bug: it read ``content[0]``, which is the thinking block."""
    bloques = [
        BloqueFalso("thinking", "estoy pensando"),
        BloqueFalso("text", "la respuesta"),
    ]

    assert responder_con(proveedor, bloques) == "la respuesta"


def test_sin_bloques_de_texto_devuelve_cadena_vacia(proveedor: ClaudeProvider) -> None:
    assert responder_con(proveedor, [BloqueFalso("thinking", "solo pienso")]) == ""


def test_respuesta_vacia_no_revienta(proveedor: ClaudeProvider) -> None:
    assert responder_con(proveedor, []) == ""


# --- Conteo de tokens -------------------------------------------------------


def test_contar_tokens_sin_cliente_devuelve_cero() -> None:
    with mock.patch.dict(os.environ, {}, clear=True):
        assert ClaudeProvider().count_tokens("texto") == 0


def test_contar_tokens_devuelve_el_valor_de_la_api(proveedor: ClaudeProvider) -> None:
    proveedor.client = mock.Mock()  # type: ignore[assignment]
    proveedor.client.messages.count_tokens = mock.Mock(
        return_value=mock.Mock(input_tokens=42)
    )

    assert proveedor.count_tokens("texto") == 42


def test_contar_tokens_absorbe_los_fallos(proveedor: ClaudeProvider) -> None:
    """Counting tokens is auxiliary: a failure must not stop the flow."""
    proveedor.client = mock.Mock()  # type: ignore[assignment]
    proveedor.client.messages.count_tokens = mock.Mock(
        side_effect=RuntimeError("caída")
    )

    assert proveedor.count_tokens("texto") == 0
