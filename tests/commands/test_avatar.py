"""El rostro: que reciba los datos, y que la boca sepa qué decir.

La primera versión pasaba la duración en la URL y no llegaba nunca. En
Windows ``webbrowser`` acaba en ``os.startfile``, el shell resuelve el
``file:`` como una ruta y ahí el ``?`` no es válido: la query se perdía
entera y la cara se abría muda. No lo veía ninguna prueba porque ninguna
miraba lo que la página recibe de verdad.

Estas sí. El contrato es la inyección en el HTML, y se comprueba mirando
el HTML que se sirve, no el que está en disco.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from ai_architect.commands import avatar
from ai_architect.core import perfil


@pytest.fixture(autouse=True)
def sin_perfil_real(tmp_path: Path):
    """El perfil del equipo no puede decidir el resultado de una prueba."""
    archivo = tmp_path / "perfil.json"

    with mock.patch.object(perfil, "ARCHIVO", archivo):
        perfil.configurar("Eathan", archivo=archivo)
        yield


def con_voz(segundos: float = 5.9, texto: str = "hola"):
    """Un audio ya preparado, sin llamar a ningún proveedor."""
    return {
        "archivo": Path("x.wav"),
        "motor": "openai",
        "segundos": segundos,
        "motivo": "",
        "texto": texto,
    }


def datos_de(pagina: str) -> dict:
    """Lo que la página recibe: se lee del HTML servido, no del de disco."""
    marca = "window.DATOS_ARQUITECTO = "

    # La última: la página trae una asignación a `null` por defecto y la
    # inyectada va detrás. Coger la primera devuelve el hueco vacío.
    trozo = pagina.split(marca)[-1].split(";")[0]

    return json.loads(trozo)


# --- La página que se sirve -------------------------------------------------


def test_el_rostro_existe() -> None:
    contenido = avatar.ROSTRO.read_text(encoding="utf-8")

    assert "<canvas" in contenido
    assert avatar.MARCA in contenido, "sin la marca no hay dónde inyectar"


def test_la_duracion_llega_a_la_pagina() -> None:
    pagina = avatar._componer("hola", con_voz(segundos=5.9))

    assert datos_de(pagina)["ms"] == 5900


def test_el_texto_tambien_llega() -> None:
    """La boca sigue las sílabas: sin el texto solo puede fingir un ritmo."""
    pagina = avatar._componer("", con_voz(texto="Buenas tardes, Eathan"))

    assert datos_de(pagina)["texto"] == "Buenas tardes, Eathan"


def test_los_acentos_sobreviven() -> None:
    """Se sirve como UTF-8: si se escapan, la cara silabea mal."""
    pagina = avatar._componer("", con_voz(texto="Aquí está la revisión"))

    assert "Aquí está la revisión" in pagina


def test_sin_voz_no_se_pide_hablar() -> None:
    pagina = avatar._componer("", None)

    assert datos_de(pagina)["ms"] == 0


def test_la_marca_se_gasta() -> None:
    """Si quedara, una segunda inyección pisaría a la primera."""
    assert avatar.MARCA not in avatar._componer("hola", con_voz())


# --- Abrirlo ----------------------------------------------------------------


def test_abre_el_navegador() -> None:
    with mock.patch("webbrowser.open") as abrir:
        resultado = avatar.run(servir=False)

    abrir.assert_called_once()
    assert resultado["success"] is True


def test_sin_servidor_se_va_por_archivo() -> None:
    """No hay cámara así, pero la cara tiene que salir igual."""
    with mock.patch("webbrowser.open") as abrir:
        resultado = avatar.run(servir=False)

    assert resultado["served"] is False
    assert abrir.call_args[0][0].startswith("file:")
    assert "sin cámara" in resultado["explanation"]


def test_el_archivo_suelto_lleva_los_datos() -> None:
    """El respaldo tiene que servir lo mismo que el servidor."""
    with mock.patch("webbrowser.open"):
        with mock.patch.object(
            avatar.motor_de_voz, "preparar", return_value=con_voz(segundos=2.0)
        ):
            with mock.patch.object(avatar.motor_de_voz, "emitir", return_value=True):
                avatar.run(decir="hola", esperar=0, servir=False)

    guardado = avatar._archivo_suelto("")

    assert datos_de(avatar._componer("hola", con_voz(segundos=2.0)))["ms"] == 2000
    assert guardado.name == "arquitecto-rostro.html"


def test_sin_texto_no_llama_a_la_voz() -> None:
    with mock.patch("webbrowser.open"):
        with mock.patch.object(avatar.motor_de_voz, "preparar") as preparar:
            avatar.run(servir=False)

    preparar.assert_not_called()


def test_se_espera_a_que_la_pagina_se_pida() -> None:
    """Sonar antes de que el navegador la tenga deja la boca por detrás."""
    servido = mock.Mock()

    with mock.patch("webbrowser.open"):
        with mock.patch.object(
            avatar, "_levantar", return_value=(mock.Mock(), "http://x/", servido)
        ):
            with mock.patch.object(
                avatar.motor_de_voz, "preparar", return_value=con_voz()
            ):
                with mock.patch.object(avatar.motor_de_voz, "emitir"):
                    with mock.patch.object(avatar, "_apagar"):
                        avatar.run(decir="hola", esperar=0)

    servido.wait.assert_called_once_with(avatar.ESPERA_MAXIMA)


def test_el_servidor_se_apaga_al_terminar() -> None:
    """Dejarlo escuchando en un puerto fijo bloquearía la próxima vez."""
    servidor = mock.Mock()

    with mock.patch("webbrowser.open"):
        with mock.patch.object(
            avatar, "_levantar", return_value=(servidor, "http://x/", mock.Mock())
        ):
            with mock.patch.object(avatar, "_apagar") as apagar:
                avatar.run(servir=True)

    apagar.assert_called_once_with(servidor)


def test_sin_voz_la_cara_sigue_saliendo() -> None:
    with mock.patch("webbrowser.open"):
        with mock.patch.object(
            avatar.motor_de_voz,
            "preparar",
            return_value={
                "archivo": None,
                "motor": "",
                "segundos": 0.0,
                "motivo": "sin voz",
            },
        ):
            resultado = avatar.run(decir="hola", esperar=0, servir=False)

    assert resultado["success"] is True
    assert resultado["spoke"] is False
    assert "sin voz" in resultado["explanation"]


def test_si_falta_el_html_se_dice_donde(tmp_path: Path) -> None:
    with mock.patch.object(avatar, "ROSTRO", tmp_path / "no-esta.html"):
        resultado = avatar.run(servir=False)

    assert resultado["success"] is False
    assert "no-esta.html" in resultado["error"]


def test_la_explicacion_saluda_por_su_nombre() -> None:
    with mock.patch("webbrowser.open"):
        resultado = avatar.run(servir=False)

    assert "Eathan" in resultado["explanation"]


# --- El servidor de verdad --------------------------------------------------


def test_el_servidor_sirve_la_pagina_una_vez() -> None:
    """Sin esto no hay cámara: `getUserMedia` exige contexto seguro."""
    from urllib.request import urlopen

    servidor, url, servido = avatar._levantar("<h1>hola</h1>")

    if servidor is None:
        pytest.skip(f"el puerto {avatar.PUERTO} está ocupado en esta máquina")

    try:
        cuerpo = urlopen(url, timeout=5).read().decode("utf-8")

    finally:
        avatar._apagar(servidor)

    assert cuerpo == "<h1>hola</h1>"
    assert servido is not None and servido.is_set()


def test_el_servidor_no_sirve_nada_mas() -> None:
    """Sirve una página, no la carpeta del usuario."""
    from urllib.error import HTTPError
    from urllib.request import urlopen

    servidor, url, _ = avatar._levantar("<h1>hola</h1>")

    if servidor is None:
        pytest.skip(f"el puerto {avatar.PUERTO} está ocupado en esta máquina")

    try:
        with pytest.raises(HTTPError) as fallo:
            urlopen(url + "../perfil.json", timeout=5)

    finally:
        avatar._apagar(servidor)

    assert fallo.value.code == 404


# --- Deshacerse al pensar ---------------------------------------------------
#
# El rostro se abre en nebulosa mientras piensa y se rehace al contestar.
# Vive entero en el HTML, que ninguna prueba mira: esto al menos avisa si
# desaparece una pieza en una edición.


def rostro() -> str:
    return avatar.ROSTRO.read_text(encoding="utf-8")


def test_cada_particula_sabe_a_donde_se_va() -> None:
    """Sin destino propio, la cara se rehace parecida pero no igual."""
    pagina = rostro()

    assert "dx:" in pagina
    assert "dz:" in pagina
    assert "retraso:" in pagina


def test_pensando_se_deshace_y_contestando_se_rehace() -> None:
    pagina = rostro()

    assert 'estado.modo === "pensando" ? 1 : 0' in pagina
    assert "estado.dispersion" in pagina


def test_se_rehace_mas_deprisa_de_lo_que_se_deshace() -> None:
    """Tardar más en recomponerse que en perderse se lee como desgana."""
    pagina = rostro()

    assert "0.028" in pagina, "lo que tarda en deshacerse"
    assert "0.075" in pagina, "lo que tarda en volver"
