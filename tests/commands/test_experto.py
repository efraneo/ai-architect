"""El director: quien contesta cada pregunta.

Lo que se fija aqui es que el reparto sirva de algo. Ninguna prueba llama a
un proveedor.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from ai_architect.commands import experto
from ai_architect.core import perfil


@pytest.fixture(autouse=True)
def sin_perfil_real(tmp_path: Path):
    archivo = tmp_path / "perfil.json"

    with mock.patch.object(perfil, "ARCHIVO", archivo):
        perfil.configurar("Efrain", archivo=archivo)
        yield


def director(plan, respuesta=None):
    """Un proveedor falso: primero reparte, luego contesta."""
    contesta = respuesta or {
        "resumen": "Dos contrasenas en el codigo.",
        "respuesta": "Largo.",
    }

    proveedor = mock.Mock()
    proveedor.generate = mock.Mock(
        side_effect=lambda orden, **k: json.dumps(
            {"especialistas": plan} if "director del equipo" in orden else contesta
        )
    )
    return proveedor


def test_un_especialista_contesta_y_se_le_nombra() -> None:
    salida = experto.responder(
        "que riesgos tengo",
        engine=director([{"quien": "seguridad", "propio": False, "encargo": "x"}]),
    )

    assert salida["specialists"] == ["seguridad"]
    assert "Te contesta seguridad" in salida["explanation"]


def test_el_comodin_no_se_mezcla_con_uno_de_verdad() -> None:
    """A "que riesgos de seguridad tengo" contestaron el agente de seguridad
    y, detras, una definicion de diccionario de la palabra riesgo."""
    salida = experto.responder(
        "que riesgos tengo",
        engine=director(
            [
                {"quien": "seguridad", "propio": True, "encargo": "x"},
                {"quien": "conversacion", "propio": False, "encargo": "y"},
            ]
        ),
    )

    assert salida["specialists"] == ["seguridad"]


def test_sin_nadie_de_oficio_el_comodin_vale() -> None:
    """Quedarse callado seria peor que contestar de forma general."""
    salida = experto.responder(
        "hola que tal",
        engine=director([{"quien": "conversacion", "propio": False, "encargo": "x"}]),
    )

    assert salida["success"] is True


def test_a_la_charla_no_se_le_pone_etiqueta() -> None:
    salida = experto.responder(
        "hola",
        engine=director([{"quien": "conversación", "propio": False, "encargo": "x"}]),
    )

    assert "Te contesta" not in salida["explanation"]


def test_un_agente_inventado_no_pasa_por_propio() -> None:
    """Marcarlo como del proyecto promete una lectura que nadie hizo."""
    plan = experto._dirigir(
        director([{"quien": "astrologia", "propio": True, "encargo": "x"}]),
        "algo",
    )

    assert plan[0]["propio"] is False


def test_nunca_mas_de_tres() -> None:
    muchos = [{"quien": f"a{i}", "propio": False, "encargo": "x"} for i in range(9)]

    assert len(experto._dirigir(director(muchos), "algo")) <= experto.MAXIMO


def test_un_proveedor_caido_no_revienta() -> None:
    roto = mock.Mock()
    roto.generate = mock.Mock(side_effect=RuntimeError("sin cuota"))

    assert experto.responder("algo", engine=roto)["success"] is False


def test_sin_pregunta_no_llama_a_nadie() -> None:
    proveedor = director([])

    experto.responder("   ", engine=proveedor)

    proveedor.generate.assert_not_called()


# --- Respuestas que llegan a medias -----------------------------------------
#
# Se vio ejecutando el .exe: una respuesta larga se corta al llegar al
# límite de salida, el JSON queda sin cerrar, y el texto crudo —con las
# vallas de markdown dentro— acababa saliendo por los altavoces:
#
#     Te contesta seguridad. ```json
#     {
#       "resumen": "Hay varias claves expuestas...


CORTADO = (
    '```json\n{\n  "resumen": "Hay claves expuestas.",\n'
    '  "respuesta": "El analisis revela problemas que deben ser abord'
)


def test_se_rescata_el_resumen_de_un_json_cortado() -> None:
    """Una frase útil vale más que un objeto perfecto que no llegó."""
    leido = experto._json(CORTADO)

    assert leido is not None
    assert leido["resumen"] == "Hay claves expuestas."


def test_lo_que_llego_de_la_respuesta_tambien_se_aprovecha() -> None:
    leido = experto._json(CORTADO)

    assert "El analisis revela problemas" in leido["respuesta"]


def test_las_vallas_de_markdown_no_estorban() -> None:
    leido = experto._json('```json\n{"resumen": "Bien.", "respuesta": "x"}\n```')

    assert leido == {"resumen": "Bien.", "respuesta": "x"}


def test_un_json_entero_se_lee_tal_cual() -> None:
    leido = experto._json('{"resumen": "Bien.", "respuesta": "x"}')

    assert leido["resumen"] == "Bien."


def test_lo_que_no_es_json_ni_lo_parece_devuelve_nada() -> None:
    """Rescatar de más convertiría cualquier texto en una respuesta falsa."""
    assert experto._json("hola qué tal") is None
    assert experto._json("") is None


def test_las_comillas_escapadas_se_deshacen() -> None:
    leido = experto._json('{"resumen": "Dijo \\"hola\\" y se fue.", "respuesta": "x"')

    assert leido["resumen"] == 'Dijo "hola" y se fue.'


def test_el_texto_crudo_no_sale_por_los_altavoces() -> None:
    """Lo que se oye no puede llevar llaves ni vallas dentro."""
    proveedor = mock.Mock()
    proveedor.generate = mock.Mock(
        side_effect=lambda orden, **k: (
            json.dumps(
                {
                    "especialistas": [
                        {"quien": "seguridad", "propio": False, "encargo": "x"}
                    ]
                }
            )
            if "director del equipo" in orden
            else CORTADO
        )
    )

    salida = experto.responder("qué riesgos tengo", engine=proveedor)

    assert "```" not in salida["explanation"]
    assert "{" not in salida["explanation"]
    assert "Hay claves expuestas." in salida["explanation"]
