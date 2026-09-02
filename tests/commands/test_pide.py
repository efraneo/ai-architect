"""`pide`: una frase, y el arquitecto elige qué hacer.

El arquitecto tenía las herramientas —los ocho comandos— pero no había quien
las escogiera. `improve --instruction "..."` acepta una frase, pero solo sabe
hacer una cosa.

Lo que se fija aquí es sobre todo lo que **no** puede pasar: que el modelo
ejecute algo que no está en la tabla, o que toque los archivos del usuario
porque una frase le sonó a permiso.

Ninguna prueba llama a un proveedor: el intérprete se inyecta.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from ai_architect.commands import pide
from ai_architect.core import perfil


@pytest.fixture
def con_perfil(tmp_path: Path):
    """Un perfil ya configurado, para no chocar con la pregunta inicial."""
    archivo = tmp_path / "perfil.json"

    with mock.patch.object(perfil, "ARCHIVO", archivo):
        perfil.configurar("Eathan", archivo=archivo)
        yield archivo


@pytest.fixture(autouse=True)
def saludo_limpio():
    """Cada prueba empieza como una sesión recién abierta.

    El saludo va una sola vez por sesión, así que sin esto una prueba deja
    marcado que ya saludó y la siguiente ve una respuesta sin saludo — o al
    revés, según el orden en que se ejecuten.
    """
    pide.reiniciar_saludo()

    yield

    pide.reiniciar_saludo()


def modelo(respuesta: dict | str):
    """Un intérprete falso que devuelve lo que se le diga."""
    proveedor = mock.Mock()
    proveedor.generate = mock.Mock(
        return_value=respuesta if isinstance(respuesta, str) else json.dumps(respuesta)
    )
    return proveedor


# --- Elige de la tabla, y solo de la tabla ----------------------------------


def test_una_frase_elige_un_comando(tmp_path: Path, con_perfil) -> None:
    with mock.patch("ai_architect.commands.doctor.run", return_value={"status": "ok"}):
        resultado = pide.run(
            str(tmp_path),
            "está todo bien configurado",
            engine=modelo({"comando": "doctor"}),
        )

    assert resultado["command"] == "doctor"
    assert resultado["executed"] is True


def test_un_comando_inventado_no_se_ejecuta(tmp_path: Path, con_perfil) -> None:
    """Lo que no puede pasar: que el modelo se saque un comando de la manga."""
    resultado = pide.run(
        str(tmp_path),
        "borra todo",
        engine=modelo({"comando": "rm -rf"}),
    )

    assert resultado["success"] is False
    assert resultado["executed"] is False
    assert "no existe" in resultado["error"]


def test_si_no_entiende_lo_dice(tmp_path: Path, con_perfil) -> None:
    resultado = pide.run(
        str(tmp_path),
        "hazme un café",
        engine=modelo({"comando": "", "motivo": "eso no lo sé hacer"}),
    )

    assert resultado["success"] is False
    assert "no lo sé hacer" in resultado["error"]


def test_una_respuesta_que_no_es_json(tmp_path: Path, con_perfil) -> None:
    resultado = pide.run(
        str(tmp_path),
        "algo",
        engine=modelo("Claro, yo te ayudo con eso."),
    )

    assert resultado["success"] is False
    assert "no entendí" in resultado["error"]


def test_el_json_dentro_de_texto_se_rescata(tmp_path: Path, con_perfil) -> None:
    """Un modelo puede envolverlo en explicación o en ```json."""
    with mock.patch("ai_architect.commands.doctor.run", return_value={"status": "ok"}):
        resultado = pide.run(
            str(tmp_path),
            "algo",
            engine=modelo('Claro:\n```json\n{"comando": "doctor"}\n```'),
        )

    assert resultado["command"] == "doctor"


def test_un_proveedor_caido_no_revienta(tmp_path: Path, con_perfil) -> None:
    proveedor = mock.Mock()
    proveedor.generate = mock.Mock(side_effect=RuntimeError("sin cuota"))

    resultado = pide.run(str(tmp_path), "algo", engine=proveedor)

    assert resultado["success"] is False
    assert "sin cuota" in resultado["error"]


# --- No toca tus archivos sin permiso ---------------------------------------


def test_lo_que_modifica_pide_permiso(tmp_path: Path, con_perfil) -> None:
    """La regla que más importa: una frase no autoriza a cambiar código."""
    with mock.patch("ai_architect.commands.improve.run") as ejecutar:
        resultado = pide.run(
            str(tmp_path),
            "arregla los except",
            engine=modelo(
                {
                    "comando": "improve",
                    "instruction": "arregla los except",
                    "apply": True,
                }
            ),
        )

    ejecutar.assert_not_called()
    assert resultado["executed"] is False
    assert "--si" in resultado["reason"]
    assert "--apply" in resultado["would_run"]


def test_con_si_ya_se_ejecuta(tmp_path: Path, con_perfil) -> None:
    with mock.patch(
        "ai_architect.commands.improve.run", return_value={"success": True, "files": 1}
    ) as ejecutar:
        resultado = pide.run(
            str(tmp_path),
            "arregla los except",
            si=True,
            engine=modelo({"comando": "improve", "apply": True}),
        )

    ejecutar.assert_called_once()
    assert resultado["executed"] is True


def test_execute_siempre_pide_permiso(tmp_path: Path, con_perfil) -> None:
    """Aplicar un parche toca el repositorio, con bandera o sin ella."""
    with mock.patch("ai_architect.commands.execute.run") as ejecutar:
        resultado = pide.run(
            str(tmp_path),
            "aplica el parche",
            engine=modelo({"comando": "execute", "patch": "x.patch"}),
        )

    ejecutar.assert_not_called()
    assert resultado["executed"] is False


def test_lo_de_solo_lectura_se_ejecuta_sin_preguntar(
    tmp_path: Path, con_perfil
) -> None:
    with mock.patch(
        "ai_architect.commands.review.run", return_value={"success": True, "score": 99}
    ):
        resultado = pide.run(
            str(tmp_path),
            "dame la puntuación",
            engine=modelo({"comando": "review"}),
        )

    assert resultado["executed"] is True


def test_un_comando_que_revienta_no_tumba_pide(tmp_path: Path, con_perfil) -> None:
    with mock.patch(
        "ai_architect.commands.review.run", side_effect=RuntimeError("se rompió")
    ):
        resultado = pide.run(
            str(tmp_path), "revisa", engine=modelo({"comando": "review"})
        )

    assert resultado["success"] is False
    assert "se rompió" in resultado["error"]


# --- El trato ---------------------------------------------------------------


def test_la_primera_vez_pregunta_como_llamarte(tmp_path: Path) -> None:
    archivo = tmp_path / "nuevo.json"

    with mock.patch.object(perfil, "ARCHIVO", archivo):
        resultado = pide.run(
            str(tmp_path), "hola", engine=modelo({"comando": "doctor"})
        )

    assert resultado["needs_profile"] is True
    assert "--soy" in resultado["explanation"]


def test_se_lo_dices_una_vez_y_lo_recuerda(tmp_path: Path) -> None:
    archivo = tmp_path / "nuevo.json"

    with mock.patch.object(perfil, "ARCHIVO", archivo):
        pide.run(str(tmp_path), "", soy="Eathan")

        assert perfil.esta_configurado(archivo) is True
        assert perfil.como_llamarte(archivo) == "Eathan"


def test_la_respuesta_lleva_saludo_y_despedida(tmp_path: Path, con_perfil) -> None:
    with mock.patch(
        "ai_architect.commands.review.run", return_value={"success": True, "score": 99}
    ):
        resultado = pide.run(
            str(tmp_path), "revisa", engine=modelo({"comando": "review"})
        )

    assert "Eathan" in resultado["explanation"]
    assert resultado["explanation"].count("Eathan") >= 2


# --- Lo que se dice del resultado -------------------------------------------


def test_explica_el_estado_del_entorno() -> None:
    texto = pide.explicar(
        "doctor",
        {"success": True, "status": "healthy", "components": {"git": {"status": "OK"}}},
    )

    assert "healthy" in texto
    assert "git: OK" in texto


def test_explica_los_agentes() -> None:
    texto = pide.explicar(
        "agents",
        {
            "success": True,
            "total_findings": 3,
            "verdict": {"total_agents": 11, "agents_with_findings": ["security"]},
        },
    )

    assert "11 agentes" in texto
    assert "3 hallazgos" in texto
    assert "security" in texto


def test_explica_si_tus_archivos_cambiaron() -> None:
    """Con `improve` lo primero que se quiere saber es eso."""
    texto = pide.explicar(
        "improve",
        {"success": True, "files": 1, "working_tree": "restored", "decision": {}},
    )

    assert "lo deshice" in texto


def test_un_fallo_se_dice_tal_cual() -> None:
    texto = pide.explicar("review", {"success": False, "error": "no hay repositorio"})

    assert "no hay repositorio" in texto


# --- Los avisos previos -----------------------------------------------------


def test_sin_frase_no_llama_a_nadie(tmp_path: Path, con_perfil) -> None:
    proveedor = modelo({"comando": "doctor"})

    resultado = pide.run(str(tmp_path), "   ", engine=proveedor)

    proveedor.generate.assert_not_called()
    assert resultado["success"] is False


def test_un_repositorio_que_no_existe(tmp_path: Path, con_perfil) -> None:
    resultado = pide.run(
        str(tmp_path / "no-existe"), "algo", engine=modelo({"comando": "doctor"})
    )

    assert resultado["success"] is False
    assert "No existe" in resultado["error"]


# --- Lo que no es una orden --------------------------------------------------
#
# Hablándole de verdad salió lo obvio: no toda frase es una tarea. A "saluda
# a Rafa de mi parte" respondía "no supe qué comando usar" — o peor, elegía
# `avatar` y reventaba, porque los comandos de interfaz esperan argumentos
# que `pide` no construye.


def test_una_charla_se_contesta_sin_comando(tmp_path: Path, con_perfil) -> None:
    resultado = pide.run(
        str(tmp_path),
        "cuéntame un chiste sobre programadores",
        engine=modelo({"comando": "", "respuesta": "Aquí sigo, listo cuando digas."}),
    )

    assert resultado["success"] is True
    assert resultado["conversation"] is True
    assert resultado["executed"] is False
    assert "Aquí sigo" in resultado["explanation"]


def test_una_charla_tambien_lleva_el_trato(tmp_path: Path, con_perfil) -> None:
    resultado = pide.run(
        str(tmp_path),
        "cuéntame algo",
        engine=modelo({"comando": "", "respuesta": "Buenas."}),
    )

    assert resultado["explanation"].count("Eathan") >= 2


def test_no_se_despide_al_final_de_cada_respuesta(tmp_path: Path, con_perfil) -> None:
    """Despedirse tras cada frase corta el hilo de una conversación hablada."""
    resultado = pide.run(
        str(tmp_path),
        "cuéntame algo",
        engine=modelo({"comando": "", "respuesta": "Buenas."}),
    )

    assert "te puedo ayudar ahora" in resultado["explanation"]
    assert "Buena tarde" not in resultado["explanation"]
    assert "Buena noche" not in resultado["explanation"]


def test_sin_comando_y_sin_respuesta_sigue_siendo_un_fallo(
    tmp_path: Path, con_perfil
) -> None:
    """No se puede convertir todo fallo en charla: eso taparía los de verdad."""
    resultado = pide.run(
        str(tmp_path),
        "haz algo raro",
        engine=modelo({"comando": "", "motivo": "eso no lo sé hacer"}),
    )

    assert resultado["success"] is False
    assert "no lo sé hacer" in resultado["error"]


# --- La interfaz no se elige a sí misma -------------------------------------


def test_los_comandos_de_interfaz_no_estan_en_el_catalogo() -> None:
    """`avatar` esperaba un argumento que `pide` no construye, y reventaba."""
    catalogo, tabla = pide._catalogo()

    for interfaz in ("avatar", "conversar", "voz"):
        assert interfaz not in tabla
        assert f"  {interfaz}:" not in catalogo


def test_los_que_analizan_el_proyecto_si_estan() -> None:
    _, tabla = pide._catalogo()

    for util in ("review", "agents", "analyze", "doctor", "improve"):
        assert util in tabla


def test_elegir_uno_de_interfaz_ya_no_se_ejecuta(tmp_path: Path, con_perfil) -> None:
    with mock.patch("ai_architect.commands.avatar.run") as abrir:
        resultado = pide.run(
            str(tmp_path), "saluda a Rafa", engine=modelo({"comando": "avatar"})
        )

    abrir.assert_not_called()
    assert resultado["success"] is False


# --- Sabe qué hora es -------------------------------------------------------


def test_sabe_la_fecha_y_la_hora() -> None:
    """A "¿qué hora es?" contestaba que no tenía acceso. La tenía delante."""
    from datetime import datetime

    dicho = pide._momento(datetime(2026, 9, 1, 15, 42))

    assert "15:42" in dicho
    assert "martes" in dicho
    assert "septiembre" in dicho
    assert "2026" in dicho


def test_la_hora_se_le_pasa_al_modelo(tmp_path: Path, con_perfil) -> None:
    """Para lo que sí llega al modelo: que sepa cuándo está contestando."""
    proveedor = modelo({"comando": "", "respuesta": "Ya voy."})

    pide.run(str(tmp_path), "cuéntame algo del proyecto", engine=proveedor)

    enviado = proveedor.generate.call_args[0][0]

    assert "LO QUE SABES AHORA MISMO" in enviado
    assert "Son las" in enviado


# --- Lo que no llega al modelo ----------------------------------------------
#
# "¿Qué hora es?" tardaba tres segundos y costaba dinero para leer un reloj
# que está en la máquina.


def test_la_hora_no_llama_a_nadie(tmp_path: Path, con_perfil) -> None:
    proveedor = modelo({"comando": "doctor"})

    resultado = pide.run(str(tmp_path), "¿qué hora es?", engine=proveedor)

    proveedor.generate.assert_not_called()
    assert resultado["instant"] is True
    assert resultado["panel"]["tipo"] == "reloj"


def test_un_saludo_a_secas_tampoco(tmp_path: Path, con_perfil) -> None:
    proveedor = modelo({"comando": "doctor"})

    pide.run(str(tmp_path), "hola", engine=proveedor)

    proveedor.generate.assert_not_called()


def test_un_saludo_con_orden_detras_si_llega(tmp_path: Path, con_perfil) -> None:
    """Lo que importa de "hola, revisa el proyecto" es lo segundo."""
    proveedor = modelo({"comando": "review"})

    with mock.patch(
        "ai_architect.commands.review.run", return_value={"success": True, "score": 9}
    ):
        pide.run(str(tmp_path), "hola, revisa el proyecto entero", engine=proveedor)

    proveedor.generate.assert_called_once()


def test_mover_la_ventana_no_llama_a_nadie(tmp_path: Path, con_perfil) -> None:
    proveedor = modelo({"comando": "doctor"})

    resultado = pide.run(str(tmp_path), "amplíala", engine=proveedor)

    proveedor.generate.assert_not_called()
    assert resultado["window"] == "ampliar"


# --- Lo que se ve en la ventana ---------------------------------------------


def test_la_puntuacion_va_al_panel() -> None:
    cuadro = pide.panel("review", {"success": True, "score": 99.26, "issues": 41})

    assert cuadro["tipo"] == "puntuacion"
    assert cuadro["valor"] == 99.26


def test_los_hallazgos_van_al_panel() -> None:
    cuadro = pide.panel(
        "agents",
        {
            "success": True,
            "total_findings": 9,
            "verdict": {"total_agents": 11, "agents_with_findings": ["security"]},
        },
    )

    assert cuadro["total"] == 9
    assert cuadro["con_hallazgos"] == ["security"]


def test_un_comando_fallido_no_pinta_nada() -> None:
    """Una ventana con datos de algo que falló es peor que ninguna ventana."""
    assert pide.panel("review", {"success": False, "error": "x"}) is None


def test_un_comando_sin_panel_no_inventa_uno() -> None:
    assert pide.panel("execute", {"success": True}) is None


# --- Saludar una vez, no en cada frase --------------------------------------


def test_solo_saluda_la_primera_vez(tmp_path: Path, con_perfil) -> None:
    """ "Buenas tardes, Efraín" delante de cada respuesta cansa a la tercera."""
    pide.reiniciar_saludo()

    primera = pide.run(
        str(tmp_path), "cuéntame algo", engine=modelo({"comando": "", "respuesta": "A"})
    )
    segunda = pide.run(
        str(tmp_path), "y otra cosa", engine=modelo({"comando": "", "respuesta": "B"})
    )

    saludo = perfil.saludo()

    assert saludo in primera["explanation"]
    assert saludo not in segunda["explanation"]


def test_pero_siempre_ofrece_seguir(tmp_path: Path, con_perfil) -> None:
    pide.reiniciar_saludo()

    pide.run(str(tmp_path), "algo", engine=modelo({"comando": "", "respuesta": "A"}))
    segunda = pide.run(
        str(tmp_path), "otra", engine=modelo({"comando": "", "respuesta": "B"})
    )

    assert "te puedo ayudar ahora" in segunda["explanation"]


def test_una_sesion_nueva_vuelve_a_saludar(tmp_path: Path, con_perfil) -> None:
    pide.run(str(tmp_path), "algo", engine=modelo({"comando": "", "respuesta": "A"}))

    pide.reiniciar_saludo()

    otra = pide.run(
        str(tmp_path), "algo", engine=modelo({"comando": "", "respuesta": "B"})
    )

    assert perfil.saludo() in otra["explanation"]


# --- La carpeta que se dice hablando ----------------------------------------


def test_una_carpeta_dicha_se_resuelve(tmp_path: Path, con_perfil) -> None:
    destino = tmp_path / "autosgsst"
    destino.mkdir()

    with mock.patch(
        "ai_architect.core.rutas.resolver", return_value=(destino, [])
    ) as buscar:
        with mock.patch(
            "ai_architect.commands.review.run", return_value={"success": True}
        ) as revisar:
            pide.run(
                str(tmp_path),
                "revisa autosgsst",
                engine=modelo({"comando": "review", "carpeta": "autosgsst"}),
            )

    buscar.assert_called_once()
    assert revisar.call_args[0][0] == str(destino)


def test_si_no_encuentra_la_carpeta_pregunta(tmp_path: Path, con_perfil) -> None:
    """Ejecutar sobre la carpeta equivocada es peor que perder un segundo."""
    parecidas = [tmp_path / "informes", tmp_path / "informes2"]

    with mock.patch("ai_architect.core.rutas.resolver", return_value=(None, parecidas)):
        with mock.patch("ai_architect.commands.review.run") as revisar:
            resultado = pide.run(
                str(tmp_path),
                "revisa informe",
                engine=modelo({"comando": "review", "carpeta": "informe"}),
            )

    revisar.assert_not_called()
    assert "informes" in resultado["explanation"]
    assert "No encuentro" in resultado["explanation"]


def test_sin_carpeta_dicha_no_se_busca_nada(tmp_path: Path, con_perfil) -> None:
    with mock.patch("ai_architect.core.rutas.resolver") as buscar:
        with mock.patch(
            "ai_architect.commands.review.run", return_value={"success": True}
        ):
            pide.run(str(tmp_path), "revisa", engine=modelo({"comando": "review"}))

    buscar.assert_not_called()
