"""Lo que salió de la tercera prueba real: el transcriptor alucinando su contexto,
«cierra Architect» que no cerraba, «guárdalo en Word en el escritorio» que volvía a
preguntar, y «eso está mal» que no apuntaba nada."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from ai_architect import autoreparacion
from ai_architect.commands import conversar, crear, respuestas
from ai_architect.core import perfil
from ai_architect.voz import escuchar


@pytest.fixture(autouse=True)
def _perfil(tmp_path: Path, monkeypatch):
    archivo = tmp_path / "perfil.json"
    monkeypatch.setattr(perfil, "ARCHIVO", archivo)
    perfil.configurar("Efraín", archivo=archivo)
    conversar._ultima_orden = ""
    conversar._ultimo_dicho = ""
    crear.olvidar()
    yield
    crear.olvidar()


# --- El transcriptor devolvía su contexto ----------------------------------------


def test_el_contexto_devuelto_como_transcripcion_es_ruido() -> None:
    assert escuchar.es_alucinacion(escuchar.CONTEXTO)
    assert escuchar.es_alucinacion(
        "Órdenes habladas a Architect, un asistente de programación en español, al que se llama por su nombre."
    )
    assert not escuchar.es_alucinacion("Architect, revisa el proyecto")
    assert not escuchar.es_alucinacion("pásalo a Word y guárdalo en el escritorio")
    assert not escuchar.es_alucinacion("")


def test_transcribir_descarta_la_alucinacion() -> None:
    respuesta = mock.Mock(text=escuchar.CONTEXTO)

    with mock.patch("openai.OpenAI") as constructor:
        constructor.return_value.audio.transcriptions.create.return_value = respuesta
        escuchar._cliente = None

        salida = escuchar.transcribir(b"audio")

    escuchar._cliente = None
    assert salida["texto"] == "" and salida["error"] == "ruido"


# --- Cerrar, reposo, queja ---------------------------------------------------------


@pytest.mark.parametrize(
    "dicho", ["Cierra Architect", "ciérrate", "termina tu ejecución", "hasta luego"]
)
def test_cerrar_se_cumple(dicho: str) -> None:
    salida = respuestas.responder(dicho)

    assert (
        salida is not None
        and salida["cerrar"] is True
        and "Hasta luego" in salida["respuesta"]
    )


def test_cierra_la_ventana_sigue_siendo_la_ventana() -> None:
    salida = respuestas.responder("cierra la ventana")

    assert (
        salida is not None
        and salida.get("ventana") == "cerrar"
        and not salida.get("cerrar")
    )


@pytest.mark.parametrize(
    "dicho", ["quédate en reposo", "transfórmate en nebulosa", "descansa"]
)
def test_reposo_deshace_el_rostro(dicho: str) -> None:
    salida = respuestas.responder(dicho)

    assert salida is not None and salida["rostro"] == "reposo"


def test_la_queja_se_apunta_como_averia() -> None:
    conversar._ultima_orden = "graba lo que te dicte en Word"
    conversar._ultimo_dicho = "Aquí estoy, listo para ayudar."

    salida = respuestas.responder("eso está mal")

    assert salida is not None and "adelante" in salida["respuesta"]
    averia = autoreparacion.pendiente()
    assert averia and averia["comando"] == "conversacion"
    assert "graba lo que te dicte" in averia["frase"]


def test_sin_orden_previa_la_queja_pregunta() -> None:
    salida = respuestas.responder("no lo hiciste")

    assert salida is not None and "qué hice mal" in salida["respuesta"]
    assert autoreparacion.pendiente() is None


def test_atender_apaga_la_sesion_al_cerrar() -> None:
    with mock.patch.object(
        conversar.motor_de_voz,
        "preparar",
        return_value={"segundos": 2.0, "texto": "Hasta luego."},
    ):
        with mock.patch.object(conversar, "cerrar_sesion") as cerrar:
            salida = conversar.atender("cierra Architect", ".", si=False)

    assert salida["cerrar"] is True and "Hasta luego" in salida["respuesta"]
    cerrar.assert_called_once()
    assert cerrar.call_args.args[0] >= 3.0


def test_cerrar_sesion_apaga_el_servidor_y_la_ventana() -> None:
    servidor = mock.Mock()
    conversar._servidor_activo = servidor

    with mock.patch.object(
        conversar.avatar, "cerrar_ventana_flotante", return_value=True
    ) as ventana:
        conversar.cerrar_sesion(0.2)

        import time

        for _ in range(60):
            if servidor.shutdown.called:
                break

            time.sleep(0.05)

    conversar._servidor_activo = None
    ventana.assert_called_once()
    servidor.shutdown.assert_called_once()


# --- Guardar en Word sin volver a preguntar --------------------------------------


def test_si_la_peticion_dice_donde_no_se_pregunta(tmp_path: Path, monkeypatch) -> None:
    """«…y guárdalo en el escritorio»: se guarda ahí sin volver a preguntar."""
    import json

    monkeypatch.setattr(crear, "escritorio", lambda: tmp_path)
    monkeypatch.setattr(crear, "carpeta_de", lambda _n: tmp_path)
    modelo = mock.Mock()
    modelo.generate.return_value = json.dumps(
        {
            "tipo": "word",
            "titulo": "Notas",
            "resumen": "Listo, en Word.",
            "secciones": [{"titulo": "Uno", "texto": "hola"}],
        }
    )
    guardado = {
        "success": True,
        "executed": True,
        "explanation": "Guardado en Escritorio.",
    }

    with mock.patch.object(crear, "guardar_en", return_value=guardado) as guardar:
        salida = crear.run(
            "un documento de Word con lo dicho y guárdalo en el escritorio",
            engine=modelo,
        )

    assert salida.get("awaiting") != "destino", salida
    guardar.assert_called_once_with(tmp_path)
    assert "Guardado" in salida["explanation"]


def test_pide_manda_la_frase_entera_a_crear_si_nombra_el_sitio() -> None:
    from ai_architect.commands import pide

    recibido: dict = {}

    def crear_falso(args):
        recibido["peticion"] = args.peticion
        return {"success": True, "explanation": "ok"}

    with mock.patch(
        "ai_architect.cli.POR_NOMBRE",
        {"crear": mock.Mock(ejecutar=crear_falso, requiere=())},
    ):
        pide._ejecutar(
            "crear",
            {"peticion": "un documento de Word con lo dicho"},
            ".",
            "graba lo que me dijiste en Word y guárdalo en el escritorio",
            False,
            False,
            False,
        )

    assert (
        recibido["peticion"]
        == "graba lo que me dijiste en Word y guárdalo en el escritorio"
    )
