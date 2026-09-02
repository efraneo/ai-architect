"""Lo que no hace falta preguntarle a un modelo.

"¿Qué hora es?" tardaba tres segundos y costaba dinero para leer un reloj
que está en la máquina. Aquí se resuelven en el sitio las preguntas cuya
respuesta ya está determinada por la frase y por el reloj.

La otra mitad de estas pruebas es la que importa de verdad: que el atajo
**no se coma** una orden legítima. Un atajo que adivina mal es peor que
tres segundos de espera.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest

from ai_architect.commands import respuestas
from ai_architect.core import perfil

TARDE = datetime(2026, 9, 1, 15, 42)
MANANA = datetime(2026, 9, 1, 9, 15)
NOCHE = datetime(2026, 9, 1, 22, 30)


@pytest.fixture(autouse=True)
def sin_perfil_real(tmp_path: Path):
    archivo = tmp_path / "perfil.json"

    with mock.patch.object(perfil, "ARCHIVO", archivo):
        perfil.configurar("Efraín", archivo=archivo)
        yield


# --- La hora ----------------------------------------------------------------


@pytest.mark.parametrize(
    "frase",
    ["¿qué hora es?", "que horas son", "dime la hora", "oye, ¿qué hora es ya?"],
)
def test_la_hora_se_contesta_sola(frase: str) -> None:
    salida = respuestas.responder(frase, TARDE)

    assert salida is not None
    assert "4 menos" in salida["respuesta"] or "3 y 42" in salida["respuesta"]


def test_la_hora_se_dice_como_se_dice() -> None:
    """ "15:42" en voz alta suena a marcador, no a respuesta."""
    assert (
        "3 y 42 de la tarde" in respuestas.responder("qué hora es", TARDE)["respuesta"]
    )


@pytest.mark.parametrize(
    ("momento", "esperado"),
    [
        (datetime(2026, 9, 1, 9, 0), "9 en punto de la mañana"),
        (datetime(2026, 9, 1, 13, 15), "1 y cuarto de la tarde"),
        (datetime(2026, 9, 1, 20, 30), "8 y media de la noche"),
        (datetime(2026, 9, 1, 10, 45), "11 menos cuarto de la mañana"),
    ],
)
def test_las_horas_redondas_se_dicen_en_palabras(
    momento: datetime, esperado: str
) -> None:
    assert esperado in respuestas.responder("qué hora es", momento)["respuesta"]


def test_la_hora_deja_un_reloj_en_pantalla() -> None:
    """Preguntar la hora suele ser mirar el reloj, no oírla y olvidarla."""
    panel = respuestas.responder("qué hora es", TARDE)["panel"]

    assert panel["tipo"] == "reloj"
    assert panel["hora"] == "15:42"
    assert "septiembre" in panel["fecha"]


def test_la_fecha_tambien() -> None:
    salida = respuestas.responder("¿qué día es hoy?", TARDE)

    assert "martes 1 de septiembre" in salida["respuesta"]
    assert salida["panel"]["tipo"] == "reloj"


# --- La ventana -------------------------------------------------------------


@pytest.mark.parametrize("frase", ["amplíala", "agranda la ventana", "maximiza eso"])
def test_ampliar(frase: str) -> None:
    assert respuestas.responder(frase, TARDE)["ventana"] == "ampliar"


@pytest.mark.parametrize("frase", ["ciérrala", "cierra la ventana", "quita la ventana"])
def test_cerrar(frase: str) -> None:
    assert respuestas.responder(frase, TARDE)["ventana"] == "cerrar"


def test_reducir() -> None:
    assert respuestas.responder("hazla pequeña", TARDE)["ventana"] == "reducir"


def test_cerrar_gana_a_ampliar() -> None:
    """ "cierra la ventana" lleva dentro palabras de las dos listas."""
    assert respuestas.responder("cierra la ventana", TARDE)["ventana"] == "cerrar"


# --- Cortesía ---------------------------------------------------------------


def test_un_saludo_a_secas() -> None:
    assert "Buenas tardes, Efraín" in respuestas.responder("hola", TARDE)["respuesta"]


def test_el_saludo_va_con_la_hora() -> None:
    assert "Buenos días" in respuestas.responder("hola", MANANA)["respuesta"]
    assert "Buenas noches" in respuestas.responder("hola", NOCHE)["respuesta"]


def test_las_gracias() -> None:
    assert respuestas.responder("muchas gracias", TARDE)["respuesta"] == "A ti."


def test_quien_eres() -> None:
    assert "arquitecto" in respuestas.responder("¿quién eres?", TARDE)["respuesta"]


def test_que_sabes_hacer() -> None:
    dicho = respuestas.responder("¿qué sabes hacer?", TARDE)["respuesta"]

    assert "changelog" in dicho
    assert "agentes" in dicho


# --- Lo que NO se ataja -----------------------------------------------------
#
# La mitad que importa: un atajo que se traga una orden de verdad es peor
# que la espera que venía a quitar.


@pytest.mark.parametrize(
    "frase",
    [
        "revisa el proyecto y dime la puntuación",
        "pásame los agentes",
        "arregla los except vacíos",
        "cuántos archivos tiene el repositorio",
        "arma el changelog de esta versión",
        "cómo está el entorno",
        "",
        "   ",
    ],
)
def test_esto_es_cosa_del_modelo(frase: str) -> None:
    assert respuestas.responder(frase, TARDE) is None


def test_un_saludo_con_orden_detras_no_se_ataja() -> None:
    """Lo que importa de "hola, revisa el proyecto" es lo segundo."""
    assert respuestas.responder("hola, revisa el proyecto entero", TARDE) is None


def test_hablar_de_la_hora_no_es_preguntarla() -> None:
    """ "a qué hora se ejecutan las pruebas" es una pregunta del proyecto."""
    salida = respuestas.responder("mide cuánto tarda cada prueba", TARDE)

    assert salida is None
