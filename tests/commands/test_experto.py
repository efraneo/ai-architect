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
