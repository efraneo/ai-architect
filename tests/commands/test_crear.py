"""Producir un documento, y decidir dónde va.

Lo que se fija aquí es sobre todo lo que se pierde si falla: que no se pisen
archivos, que el escritorio sea el de verdad —en un Windows en español con
OneDrive, ``~/Desktop`` no existe— y que el HTML salga bien formado aunque
el modelo devuelva cualquier cosa.

Ninguna prueba abre un diálogo, un navegador ni un proveedor.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from ai_architect.commands import crear
from ai_architect.core import perfil

DOCUMENTO = {
    "tipo": "documento",
    "titulo": "La fotosíntesis",
    "resumen": "Las plantas convierten luz en azúcar.",
    "secciones": [{"titulo": "Qué es", "parrafos": ["Un proceso.", "Y otro."]}],
}

TABLA = {
    "tipo": "tabla",
    "titulo": "Comparativa",
    "resumen": "Dos filas.",
    "columnas": ["Lenguaje", "Año"],
    "filas": [["Python", "1991"], ["Rust", "2010"]],
}

GRAFICA = {
    "tipo": "grafica",
    "titulo": "Ventas",
    "resumen": "Suben.",
    "forma": "barras",
    "eje": "millones",
    "etiquetas": ["ene", "feb"],
    "valores": [10, 25],
}


@pytest.fixture(autouse=True)
def limpio(tmp_path: Path):
    crear.olvidar()

    archivo = tmp_path / "perfil.json"

    with mock.patch.object(perfil, "ARCHIVO", archivo):
        perfil.configurar("Efraín", archivo=archivo)
        yield

    crear.olvidar()


def modelo(datos: dict):
    proveedor = mock.Mock()
    proveedor.generate = mock.Mock(return_value=json.dumps(datos))
    return proveedor


# --- Generar ----------------------------------------------------------------


def test_prepara_el_documento_y_pregunta_donde() -> None:
    salida = crear.run("resume la fotosíntesis", engine=modelo(DOCUMENTO))

    assert salida["success"] is True
    assert salida["awaiting"] == "destino"
    assert "Dónde lo guardo" in salida["explanation"]
    assert crear.hay_pendiente() is True


def test_lo_que_se_dice_en_voz_alta_es_el_resumen() -> None:
    salida = crear.run("resume la fotosíntesis", engine=modelo(DOCUMENTO))

    assert "convierten luz" in salida["explanation"]


def test_sin_peticion_no_llama_a_nadie() -> None:
    proveedor = modelo(DOCUMENTO)

    crear.run("   ", engine=proveedor)

    proveedor.generate.assert_not_called()


def test_un_proveedor_caido_no_revienta() -> None:
    roto = mock.Mock()
    roto.generate = mock.Mock(side_effect=RuntimeError("sin cuota"))

    assert crear.run("algo", engine=roto)["success"] is False


def test_una_respuesta_que_no_es_json() -> None:
    proveedor = mock.Mock()
    proveedor.generate = mock.Mock(return_value="claro que sí")

    assert crear.run("algo", engine=proveedor)["success"] is False


# --- El HTML ----------------------------------------------------------------


def test_el_documento_sale_bien_formado() -> None:
    crear.run("x", engine=modelo(DOCUMENTO))

    html = crear._pendiente["contenido"]

    assert "<h1>La fotosíntesis</h1>" in html
    assert "<h2>Qué es</h2>" in html
    assert html.count("<p>") >= 2


def test_lo_que_venga_del_modelo_se_escapa() -> None:
    """Un título con etiquetas dentro no puede romper la página."""
    crear.run("x", engine=modelo({**DOCUMENTO, "titulo": "<script>alert(1)</script>"}))

    assert "<script>alert" not in crear._pendiente["contenido"]
    assert "&lt;script&gt;" in crear._pendiente["contenido"]


def test_la_tabla_sale_con_sus_celdas() -> None:
    crear.run("x", engine=modelo(TABLA))

    html = crear._pendiente["contenido"]

    assert html.count("<td>") == 4
    assert "<th>Lenguaje</th>" in html


def test_la_grafica_es_un_svg() -> None:
    crear.run("x", engine=modelo(GRAFICA))

    html = crear._pendiente["contenido"]

    assert "<svg" in html
    assert html.count("<rect") == 2


def test_una_grafica_descuadrada_se_rechaza() -> None:
    """Más valores que etiquetas dibuja una gráfica que miente."""
    salida = crear.run("x", engine=modelo({**GRAFICA, "valores": [1, 2, 3]}))

    assert salida["success"] is False


# --- Guardar ----------------------------------------------------------------


def test_guarda_y_deja_de_estar_pendiente(tmp_path: Path) -> None:
    crear.run("x", engine=modelo(DOCUMENTO))

    with mock.patch.object(crear, "_abrir"):
        salida = crear.guardar_en(tmp_path)

    assert Path(salida["path"]).is_file()
    assert crear.hay_pendiente() is False


def test_nunca_pisa_un_archivo_que_ya_esta(tmp_path: Path) -> None:
    """Un documento perdido no se recupera."""
    for _ in range(2):
        crear.run("x", engine=modelo(DOCUMENTO))

        with mock.patch.object(crear, "_abrir"):
            crear.guardar_en(tmp_path)

    assert len(list(tmp_path.glob("*.html"))) == 2


def test_una_tabla_se_guarda_tambien_en_csv(tmp_path: Path) -> None:
    """El HTML se mira; el CSV se abre en Excel."""
    crear.run("x", engine=modelo(TABLA))

    with mock.patch.object(crear, "_abrir"):
        salida = crear.guardar_en(tmp_path)

    hojas = list(tmp_path.glob("*.csv"))

    assert len(hojas) == 1
    assert "Python" in hojas[0].read_text(encoding="utf-8-sig")
    assert salida["extras"]


def test_sin_nada_preparado_no_guarda_nada(tmp_path: Path) -> None:
    assert crear.guardar_en(tmp_path)["success"] is False


# --- Dónde ------------------------------------------------------------------


def test_el_escritorio_es_el_de_verdad() -> None:
    assert crear.escritorio().is_dir()


@pytest.mark.parametrize("dicho", ["en el escritorio", "guárdalo en el escritorio"])
def test_entiende_el_escritorio(dicho: str, tmp_path: Path) -> None:
    crear.run("x", engine=modelo(DOCUMENTO))

    with mock.patch.object(crear, "guardar_en", return_value={"success": True}) as g:
        with mock.patch.object(crear, "escritorio", return_value=tmp_path):
            crear.donde_guardarlo(dicho)

    g.assert_called_once_with(tmp_path)


@pytest.mark.parametrize(
    "dicho", ["lo elijo yo", "quiero elegir", "abre el explorador"]
)
def test_pedir_elegir_abre_el_explorador(dicho: str) -> None:
    crear.run("x", engine=modelo(DOCUMENTO))

    with mock.patch.object(crear, "_dialogo", return_value="") as dialogo:
        crear.donde_guardarlo(dicho)

    dialogo.assert_called_once()


def test_si_cierra_el_explorador_no_se_pierde_lo_hecho() -> None:
    crear.run("x", engine=modelo(DOCUMENTO))

    with mock.patch.object(crear, "_dialogo", return_value=""):
        salida = crear.guardar_donde_diga()

    assert salida["success"] is True
    assert crear.hay_pendiente() is True, "sigue preparado para otro destino"


def test_el_explorador_manda_sobre_el_nombre(tmp_path: Path) -> None:
    """Si se molestó en escribir un nombre en el diálogo, es el que quiere."""
    suyo = tmp_path / "mi trabajo.html"

    crear.run("x", engine=modelo(DOCUMENTO))

    with mock.patch.object(crear, "_dialogo", return_value=str(suyo)):
        with mock.patch.object(crear, "_abrir"):
            salida = crear.guardar_donde_diga()

    assert salida["path"] == str(suyo)
    assert suyo.is_file()


def test_se_puede_cancelar() -> None:
    crear.run("x", engine=modelo(DOCUMENTO))

    salida = crear.donde_guardarlo("déjalo, no lo guardes")

    assert salida["success"] is True
    assert crear.hay_pendiente() is False


def test_sin_nada_pendiente_no_interpreta_destinos() -> None:
    assert crear.donde_guardarlo("en el escritorio") is None


def test_lo_que_no_es_un_destino_devuelve_nada() -> None:
    """Debe caer al modelo, no adivinarse como carpeta."""
    crear.run("x", engine=modelo(DOCUMENTO))

    with mock.patch("ai_architect.core.rutas.resolver", return_value=(None, [])):
        assert crear.donde_guardarlo("cuéntame otra cosa") is None
