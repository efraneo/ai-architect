"""Quinta ronda: cerrar y descansar de cualquier forma, cuentas por voz."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_architect.commands import calcular, respuestas
from ai_architect.core import perfil


@pytest.fixture(autouse=True)
def _perfil(tmp_path: Path, monkeypatch):
    archivo = tmp_path / "perfil.json"
    monkeypatch.setattr(perfil, "ARCHIVO", archivo)
    perfil.configurar("Efraín", archivo=archivo)


@pytest.mark.parametrize(
    "dicho",
    [
        "Cerrar",
        "No, cierra.",
        "Despídete.",
        "cierra Architect",
        "Apágate ya",
        "termina el proyecto",
        "detente",
        "cierra la sesión",
        "ya, ciérrate",
        "termina tu ejecución, Architect",
    ],
)
def test_cualquier_forma_de_cerrar(dicho: str) -> None:
    salida = respuestas.responder(dicho)

    assert salida is not None and salida.get("cerrar") is True, dicho


@pytest.mark.parametrize(
    "dicho", ["cierra la ventana", "para la música", "termina el informe y guárdalo"]
)
def test_lo_que_no_es_cerrar(dicho: str) -> None:
    salida = respuestas.responder(dicho)

    assert salida is None or not salida.get("cerrar"), dicho


@pytest.mark.parametrize(
    "dicho",
    [
        "descansa",
        "Hiberna.",
        "Architect, hiberna hasta que te llame",
        "quédate en reposo",
        "ponte a dormir",
        "transfórmate en nebulosa",
        "descansa un rato",
    ],
)
def test_cualquier_forma_de_descansar(dicho: str) -> None:
    salida = respuestas.responder(dicho)

    assert salida is not None and salida.get("rostro") == "reposo", dicho


@pytest.mark.parametrize(
    ("dicho", "esperado"),
    [
        ("cuánto es 25 por 4", 100),
        ("suma 3 y 5", 8),
        ("multiplica 12 por 12", 144),
        ("2 más 2", 4),
        ("el 15 por ciento de 200", 30),
        ("raíz cuadrada de 81", 9),
        ("cuánto es 100 entre 8", 12.5),
        ("resta 10 y 3", 7),
        ("cinco por seis", 30),
        ("3 al cuadrado", 9),
    ],
)
def test_calcula_por_voz(dicho: str, esperado: float) -> None:
    salida = calcular.calcular(dicho)

    assert salida is not None and salida["resultado"] == pytest.approx(esperado), dicho
    assert respuestas.responder(dicho) is not None


@pytest.mark.parametrize(
    "dicho", ["revisa el proyecto", "qué hora es", "abre Word", "suma las dependencias"]
)
def test_lo_que_no_es_una_cuenta(dicho: str) -> None:
    assert calcular.calcular(dicho) is None


def test_la_cuenta_se_dice_bonita() -> None:
    assert calcular.calcular("cuánto es 25 por 4")["respuesta"] == "25 por 4 es 100."
    assert "12,5" in calcular.calcular("100 entre 8")["respuesta"]
    assert "1.000" in calcular.calcular("cuánto es 500 más 500")["respuesta"]


def test_la_cuenta_por_ciento_y_lo_legible() -> None:
    assert calcular.calcular("el 15 por ciento de 200")["resultado"] == 30
    assert calcular.calcular("cuánto es 25 por 4")["respuesta"] == "25 por 4 es 100."
    assert calcular.calcular("cuánto es el 15 por ciento de 200")[
        "respuesta"
    ].startswith("El 15 por ciento de 200 es 30")


@pytest.mark.parametrize(
    ("dicho", "accion"),
    [
        ("maximiza ventana", "maximizar"),
        ("Maximiza la ventana", "maximizar"),
        ("minimiza ventana", "minimizar"),
        ("Architect, minimiza la ventana de la presentación", "minimizar"),
        ("restaura la ventana", "restaurar"),
    ],
)
def test_maximizar_y_minimizar_la_ventana_de_architect(dicho: str, accion: str) -> None:
    salida = respuestas.responder(dicho)

    assert salida is not None and salida["ventana_app"] == accion, dicho


def test_ampliar_sigue_siendo_el_panel() -> None:
    salida = respuestas.responder("amplíala")

    assert (
        salida is not None
        and salida.get("ventana") == "ampliar"
        and not salida.get("ventana_app")
    )


def test_atender_maximiza_la_ventana_flotante() -> None:
    from unittest import mock

    from ai_architect.commands import conversar

    with mock.patch.object(
        conversar.motor_de_voz, "preparar", return_value={"segundos": 0}
    ):
        with mock.patch.object(
            conversar.avatar, "accion_ventana", return_value=True
        ) as accion:
            salida = conversar.atender("maximiza ventana", ".", si=False)

    accion.assert_called_once_with("maximizar")
    assert "Maximizada" in salida["respuesta"]

    with mock.patch.object(
        conversar.motor_de_voz, "preparar", return_value={"segundos": 0}
    ):
        with mock.patch.object(conversar.avatar, "accion_ventana", return_value=False):
            salida = conversar.atender("minimiza ventana", ".", si=False)

    assert "flotante" in salida["respuesta"]
