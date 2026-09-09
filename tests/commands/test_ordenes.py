"""Separar órdenes encadenadas y atenderlas en orden."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from ai_architect.commands import ordenes, pide
from ai_architect.core import perfil


@pytest.fixture(autouse=True)
def _perfil(tmp_path: Path, monkeypatch):
    archivo = tmp_path / "perfil.json"
    monkeypatch.setattr(perfil, "ARCHIVO", archivo)
    perfil.configurar("Efraín", archivo=archivo)
    pide.reiniciar_saludo()


@pytest.mark.parametrize(
    ("frase", "esperado"),
    [
        (
            "guárdalo en Word y ponlo en el escritorio",
            ["guárdalo en Word", "ponlo en el escritorio"],
        ),
        (
            "revisa el proyecto y luego cierra la ventana",
            ["revisa el proyecto", "cierra la ventana"],
        ),
        (
            "llama a Juan; después bloquea el celular",
            ["llama a Juan", "bloquea el celular"],
        ),
        ("qué hora es y también qué día es", ["qué hora es", "qué día es"]),
        (
            "pausa la música, entonces abre WhatsApp en el celular",
            ["pausa la música", "abre WhatsApp en el celular"],
        ),
    ],
)
def test_separa_ordenes_encadenadas(frase: str, esperado: list[str]) -> None:
    assert ordenes.separar(frase) == esperado


@pytest.mark.parametrize(
    "frase",
    [
        "revisa el proyecto y dime qué tal está",
        "analiza las dependencias y la cobertura",
        "recuerda que trabajo en Xentris y en Bogotá",
        "qué hora es",
        'crea un documento que diga "revisa y corrige"',
    ],
)
def test_lo_que_no_se_separa(frase: str) -> None:
    assert ordenes.separar(frase) == [frase]


def test_no_mas_de_cuatro() -> None:
    frase = "abre a, luego abre b, luego abre c, luego abre d, luego abre e"
    assert len(ordenes.separar(frase)) == 4


def test_pide_atiende_cada_parte_y_junta_la_respuesta() -> None:
    salida = pide.run(".", frase="qué hora es y luego cierra la ventana")

    assert salida["command"] == "varias" and salida["success"]
    assert salida["parts"] == ["qué hora es", "cierra la ventana"]
    assert salida["window"] == "cerrar"
    assert "Son las" in salida["explanation"] and "Cerrada" in salida["explanation"]


def test_pide_para_en_el_cierre() -> None:
    with mock.patch("ai_architect.commands.pide._preguntar") as preguntar:
        salida = pide.run(".", frase="cierra Architect y luego revisa el proyecto")

    assert salida["cerrar"] is True and len(salida["results"]) == 1
    preguntar.assert_not_called()
