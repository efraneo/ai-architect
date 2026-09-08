"""La palabra de activación: «Architect», con lo que el micrófono le hace.

La primera versión exigía el nombre exacto y falló porque el arranque de la
frase llegaba recortado («arquitect»). Esto comprueba que ahora se reconoce
aunque venga a trozos, con muletilla, al final, y que en modo nombre se abre
una ventana en la que no hay que repetirlo.
"""

from __future__ import annotations

import pytest

from ai_architect.voz import nombre


@pytest.mark.parametrize(
    "palabra",
    [
        "Architect",
        "arquitecto",
        "Arquitecta",
        "arquitect",
        "arquitec",
        "architec",
        "arkitecto",
    ],
)
def test_reconoce_su_nombre_aunque_llegue_recortado(palabra: str) -> None:
    assert nombre.es_el_nombre(palabra)


@pytest.mark.parametrize(
    "palabra",
    ["arquitectura", "archivo", "arqueria", "revisa", "arq", "arquitectonico"],
)
def test_no_confunde_palabras_parecidas(palabra: str) -> None:
    assert not nombre.es_el_nombre(palabra)


def test_separa_el_nombre_al_principio() -> None:
    assert nombre.separar("Architect, revisa el proyecto") == (
        True,
        "revisa el proyecto",
    )


def test_separa_con_muletilla_delante() -> None:
    assert nombre.separar("oye arquitecto pásalo a Word") == (True, "pásalo a Word")


def test_separa_el_nombre_al_final() -> None:
    assert nombre.separar("revisa las dependencias, arquitecto") == (
        True,
        "revisa las dependencias",
    )


def test_conserva_la_orden_tal_como_se_dijo() -> None:
    """Lo que se manda a `pide` lleva sus tildes y mayúsculas: no la versión plana."""
    assert nombre.separar("Arquitect ¿Qué problemas tiene Efra_BOT?") == (
        True,
        "¿Qué problemas tiene Efra_BOT?",
    )


def test_sin_nombre_se_devuelve_entera() -> None:
    assert nombre.separar("revisa la arquitectura del proyecto") == (
        False,
        "revisa la arquitectura del proyecto",
    )


def test_el_nombre_solo() -> None:
    assert nombre.separar("Architect") == (True, "")


# --- decidir ------------------------------------------------------------------


def test_en_modo_libre_todo_va_para_el() -> None:
    d = nombre.decidir("revisa el proyecto", modo="libre")

    assert d.para_mi and d.orden == "revisa el proyecto" and not d.nombrado


def test_en_modo_nombre_sin_nombrarlo_no_es_para_el() -> None:
    d = nombre.decidir(
        "revisa el proyecto", modo="nombre", ultima_vez=0.0, ahora=1000.0
    )

    assert not d.para_mi and d.orden == "revisa el proyecto"


def test_en_modo_nombre_nombrado_si() -> None:
    d = nombre.decidir("Architect, revisa el proyecto", modo="nombre", ahora=1000.0)

    assert d.para_mi and d.nombrado and d.orden == "revisa el proyecto"


def test_dentro_de_la_ventana_no_hace_falta_repetirlo() -> None:
    d = nombre.decidir(
        "y ahora pásalo a Word", modo="nombre", ultima_vez=1000.0, ahora=1000.0 + 30
    )

    assert d.para_mi and not d.nombrado


def test_fuera_de_la_ventana_vuelve_a_hacer_falta() -> None:
    d = nombre.decidir(
        "y ahora pásalo a Word",
        modo="nombre",
        ultima_vez=1000.0,
        ahora=1000.0 + nombre.SEGUIMIENTO + 1,
    )

    assert not d.para_mi


def test_mientras_habla_la_ventana_esta_cerrada() -> None:
    """`ultima_vez` apunta al final de su respuesta: antes de eso, sin nombre no entra.
    Es lo que evita que su propio eco por los altavoces cuente como orden."""
    d = nombre.decidir(
        "buenas tardes efraín", modo="nombre", ultima_vez=1030.0, ahora=1000.0
    )

    assert not d.para_mi


def test_el_nombre_solo_es_llamarlo() -> None:
    d = nombre.decidir("arquitecto", modo="nombre", ahora=1000.0)

    assert d.para_mi and d.nombrado and d.solo_nombre and d.orden == "arquitecto"


def test_el_silencio_no_es_nada() -> None:
    assert nombre.decidir("   ", modo="nombre") == (False, "", False, False)


def test_la_ventana_es_larga_de_verdad() -> None:
    assert nombre.SEGUIMIENTO >= 60
