"""Dictar a Word: signos dichos con palabras, tablas, y el flujo en la conversación."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from ai_architect.commands import conversar, dictado, respuestas
from ai_architect.core import perfil
from ai_architect.office import word


@pytest.fixture(autouse=True)
def _limpio(tmp_path: Path, monkeypatch):
    archivo = tmp_path / "perfil.json"
    monkeypatch.setattr(perfil, "ARCHIVO", archivo)
    perfil.configurar("Efraín", archivo=archivo)
    dictado.terminar()
    yield
    dictado.terminar()


@pytest.fixture
def word_falso(monkeypatch):
    monkeypatch.setattr(word, "disponible", lambda: True)
    monkeypatch.setattr(word, "abrir", lambda: {"ok": True, "documentos": 1})
    escrito: list[str] = []
    monkeypatch.setattr(
        word,
        "escribir",
        lambda t: escrito.append(t) or {"ok": True, "escrito": word.puntuar(t)},
    )
    tablas: list[tuple] = []
    monkeypatch.setattr(
        word,
        "tabla",
        lambda f, c, e=None: tablas.append((f, c, e))
        or {"ok": True, "filas": f, "columnas": c},
    )
    monkeypatch.setattr(word, "parrafo", lambda: {"ok": True})
    monkeypatch.setattr(word, "deshacer", lambda v=1: {"ok": True})
    monkeypatch.setattr(
        word,
        "guardar",
        lambda n="", c=None: {
            "ok": True,
            "ruta": f"C:/Escritorio/{n or 'Dictado'}.docx",
        },
    )
    return {"escrito": escrito, "tablas": tablas}


# --- Los signos --------------------------------------------------------------------


@pytest.mark.parametrize(
    ("dicho", "esperado"),
    [
        ("hola coma mundo punto", "Hola, mundo."),
        (
            "primero punto y seguido segundo punto y aparte tercero",
            "Primero. Segundo.\nTercero",
        ),
        ("uno punto y coma dos dos puntos tres", "Uno; dos: tres"),
        ("abre paréntesis nota cierra paréntesis coma sigue", "(nota), sigue"),
        ("qué tal signo de interrogación", "Qué tal?"),
        ("una línea nueva línea otra", "Una línea\nOtra"),
    ],
)
def test_puntuar(dicho: str, esperado: str) -> None:
    assert word.puntuar(dicho) == esperado


# --- Empezar, dictar, terminar --------------------------------------------------------


@pytest.mark.parametrize(
    "frase",
    [
        "Escribe lo siguiente en Word",
        "te voy a dictar",
        "Abre Word y escribe",
        "toma nota en Word",
    ],
)
def test_frases_que_empiezan_el_dictado(frase: str) -> None:
    assert dictado.quiere_empezar(frase)


def test_sin_word_lo_dice(monkeypatch) -> None:
    monkeypatch.setattr(word, "disponible", lambda: False)

    salida = respuestas.responder("escribe lo siguiente en Word")

    assert salida is not None and "Word" in salida["respuesta"] and not dictado.activo()


def test_empieza_dicta_y_termina(word_falso) -> None:
    salida = respuestas.responder("Escribe lo siguiente en Word")

    assert salida is not None and salida["dictando"] is True and dictado.activo()

    assert (
        dictado.atender("La reunión es el lunes coma a las tres punto")["respuesta"]
        == ""
    )
    assert word_falso["escrito"] == ["La reunión es el lunes coma a las tres punto"]

    fin = dictado.atender("termina el dictado")

    assert fin["dictando"] is False and not dictado.activo()


def test_el_texto_que_viene_en_la_orden_se_escribe_ya(word_falso) -> None:
    respuestas.responder("escribe lo siguiente en Word: la reunión es el lunes")

    assert word_falso["escrito"] == ["la reunión es el lunes"] and dictado.activo()


def test_la_tabla_pregunta_y_la_inserta(word_falso) -> None:
    dictado.empezar()

    assert "filas" in dictado.atender("agrega una tabla")["respuesta"]
    salida = dictado.atender(
        "tres filas y cuatro columnas con los títulos nombre, edad y cargo"
    )

    assert "3 por 4" in salida["respuesta"]
    assert word_falso["tablas"] == [(3, 4, ["nombre", "edad", "cargo"])]


def test_la_tabla_con_medidas_en_la_misma_frase(word_falso) -> None:
    dictado.empezar()
    dictado.atender("inserta una tabla de 2 por 5")

    assert word_falso["tablas"] == [(2, 5, [])]


def test_las_ordenes_de_architect_no_son_texto(word_falso) -> None:
    dictado.empezar()

    assert dictado.atender("cierra Architect") is None
    assert dictado.atender("qué hora es") is None
    assert dictado.activo()


def test_guardar_y_deshacer(word_falso) -> None:
    dictado.empezar()

    assert "Guardado" in dictado.atender("guarda el documento como acta")["respuesta"]
    assert dictado.atender("borra eso")["respuesta"] == "Borrado."


def test_conversar_manda_lo_oido_al_dictado(word_falso) -> None:
    dictado.empezar()

    with mock.patch("ai_architect.commands.pide.run") as pide:
        salida = conversar.atender("hola coma mundo punto", ".", si=False)

    pide.assert_not_called()
    assert salida["respuesta"] == "" and salida["ms"] == 0
    assert word_falso["escrito"] == ["hola coma mundo punto"]


def test_conversar_cierra_aunque_este_dictando(word_falso) -> None:
    dictado.empezar()

    with mock.patch.object(
        conversar.motor_de_voz, "preparar", return_value={"segundos": 0}
    ):
        with mock.patch.object(conversar, "cerrar_sesion"):
            salida = conversar.atender("cierra Architect", ".", si=False)

    assert salida["cerrar"] is True
