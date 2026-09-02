"""Conversar: hablarle en vez de escribirle.

Lo que se fija aquí es lo que no se ve mirando la pantalla:

- que una orden dicha en voz alta **no** autoriza a tocar archivos,
- que la respuesta viaja con la duración exacta del audio, o la cara
  gesticula en el vacío,
- y que el audio no suena antes de contestar, o la boca llega tarde.

Ninguna prueba abre un puerto, un micrófono ni un proveedor.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

from ai_architect.commands import conversar
from ai_architect.core import perfil


@pytest.fixture(autouse=True)
def sin_perfil_real(tmp_path: Path):
    archivo = tmp_path / "perfil.json"

    with mock.patch.object(perfil, "ARCHIVO", archivo):
        perfil.configurar("Efraín", archivo=archivo)
        yield


@pytest.fixture(autouse=True)
def sin_sintetizar_de_verdad(request):
    """`run` sintetiza cinco muletillas al arrancar, y eso son cinco Piper.

    En una prueba no aportan nada y multiplican por cinco lo que tarda el
    fichero. Las que van precisamente sobre las muletillas se quedan con la
    de verdad —se reconocen por el nombre— y se montan sus propios dobles.
    """
    if "muletilla" in request.node.name:
        yield

        return

    with mock.patch.object(conversar, "preparar_rellenos", return_value=0):
        yield


def respondiendo(explicacion: str = "Todo en orden.", **extra):
    """`pide` ya resuelto, sin llamar a ningún modelo."""
    return {"success": True, "explanation": explicacion, **extra}


# --- La página --------------------------------------------------------------


def test_la_pagina_arranca_en_modo_conversacion() -> None:
    """Sin esto el navegador no enciende el micrófono."""
    pagina = conversar._componer(".")

    datos = json.loads(pagina.split("window.DATOS_ARQUITECTO = ")[-1].split(";")[0])

    assert datos["modo"] == "conversacion"


def test_la_pagina_sabe_de_que_proyecto_se_habla() -> None:
    pagina = conversar._componer("C:/proyecto")

    assert "C:/proyecto" in pagina


# --- Atender una orden ------------------------------------------------------


def test_una_orden_dicha_se_ejecuta() -> None:
    with mock.patch(
        "ai_architect.commands.pide.run", return_value=respondiendo()
    ) as ejecutar:
        with mock.patch.object(
            conversar.motor_de_voz,
            "preparar",
            return_value={"texto": "Todo en orden.", "segundos": 1.4},
        ):
            salida = conversar.atender("revisa el proyecto", ".", si=False)

    assert ejecutar.call_args[1]["frase"] == "revisa el proyecto"
    assert salida["respuesta"] == "Todo en orden."


def test_la_duracion_viaja_con_la_respuesta() -> None:
    """La cara la necesita para gesticular justo mientras suena."""
    with mock.patch("ai_architect.commands.pide.run", return_value=respondiendo()):
        with mock.patch.object(
            conversar.motor_de_voz,
            "preparar",
            return_value={"texto": "Todo en orden.", "segundos": 2.5},
        ):
            salida = conversar.atender("revisa", ".", si=False)

    assert salida["ms"] == 2500


def test_por_voz_no_se_autoriza_a_tocar_archivos() -> None:
    """Que una orden llegue hablada no la convierte en un permiso."""
    with mock.patch(
        "ai_architect.commands.pide.run", return_value=respondiendo()
    ) as ejecutar:
        with mock.patch.object(
            conversar.motor_de_voz, "preparar", return_value={"segundos": 0}
        ):
            conversar.atender("arregla los except", ".", si=False)

    assert ejecutar.call_args[1]["si"] is False


def test_el_permiso_se_da_al_abrir_la_conversacion() -> None:
    """Por voz no hay forma de teclear --si en mitad de una frase."""
    with mock.patch(
        "ai_architect.commands.pide.run", return_value=respondiendo()
    ) as ejecutar:
        with mock.patch.object(
            conversar.motor_de_voz, "preparar", return_value={"segundos": 0}
        ):
            conversar.atender("arregla los except", ".", si=True)

    assert ejecutar.call_args[1]["si"] is True


def test_un_silencio_no_llama_a_nadie() -> None:
    with mock.patch("ai_architect.commands.pide.run") as ejecutar:
        salida = conversar.atender("   ", ".", si=False)

    ejecutar.assert_not_called()
    assert salida["ms"] == 0


def test_una_transcripcion_enorme_se_recorta() -> None:
    """Un micro abierto en una reunión no es una orden."""
    with mock.patch(
        "ai_architect.commands.pide.run", return_value=respondiendo()
    ) as ejecutar:
        with mock.patch.object(
            conversar.motor_de_voz, "preparar", return_value={"segundos": 0}
        ):
            conversar.atender("hola " * 5000, ".", si=False)

    assert len(ejecutar.call_args[1]["frase"]) <= conversar.LIMITE


def test_si_pide_falla_se_dice_en_voz_alta() -> None:
    """Callarse ante un error deja al usuario mirando una cara muda."""
    with mock.patch(
        "ai_architect.commands.pide.run",
        return_value={"success": False, "error": "el proveedor falló"},
    ):
        with mock.patch.object(
            conversar.motor_de_voz,
            "preparar",
            return_value={"texto": "el proveedor falló", "segundos": 1.0},
        ) as preparar:
            salida = conversar.atender("revisa", ".", si=False)

    assert "el proveedor falló" in salida["respuesta"]
    assert "el proveedor falló" in preparar.call_args[0][0]


def test_el_audio_no_se_reproduce_al_atender() -> None:
    """Suena después de contestar: si no, la boca empieza tarde."""
    with mock.patch("ai_architect.commands.pide.run", return_value=respondiendo()):
        with mock.patch.object(
            conversar.motor_de_voz, "preparar", return_value={"segundos": 1.0}
        ):
            with mock.patch.object(conversar.motor_de_voz, "emitir") as sonar:
                salida = conversar.atender("revisa", ".", si=False)

    sonar.assert_not_called()
    assert "_audio" in salida, "el audio va aparte, para emitirlo tras responder"


# --- El servidor ------------------------------------------------------------


def test_el_puerto_ocupado_se_dice_claro() -> None:
    with mock.patch.object(conversar, "_levantar", return_value=(None, "")):
        with mock.patch("webbrowser.open") as abrir:
            resultado = conversar.run(".")

    abrir.assert_not_called()
    assert resultado["success"] is False
    assert "ocupado" in resultado["error"]


def test_abre_la_cara_y_deja_el_servidor_vivo() -> None:
    servidor = mock.Mock()

    with mock.patch.object(
        conversar, "_levantar", return_value=(servidor, "http://x/")
    ):
        with mock.patch("webbrowser.open") as abrir:
            resultado = conversar.run(".", servir_para_siempre=False)

    abrir.assert_called_once_with("http://x/")
    servidor.server_close.assert_not_called()
    assert resultado["success"] is True


def test_si_falta_el_html_se_dice_donde(tmp_path: Path) -> None:
    with mock.patch.object(conversar.avatar, "ROSTRO", tmp_path / "no-esta.html"):
        resultado = conversar.run(".")

    assert resultado["success"] is False
    assert "no-esta.html" in resultado["error"]


def test_ctrl_c_cierra_el_servidor() -> None:
    """Un puerto fijo que queda abierto bloquea la siguiente conversación."""
    servidor = mock.Mock()
    servidor.serve_forever.side_effect = KeyboardInterrupt

    with mock.patch.object(
        conversar, "_levantar", return_value=(servidor, "http://x/")
    ):
        with mock.patch("webbrowser.open"):
            conversar.run(".")

    servidor.server_close.assert_called_once()


# --- Oír con Whisper --------------------------------------------------------


def test_la_pagina_sabe_quien_la_va_a_oir() -> None:
    with mock.patch("ai_architect.voz.escuchar.disponible", return_value=True):
        pagina = conversar._componer(".")

    datos = json.loads(pagina.split("window.DATOS_ARQUITECTO = ")[-1].split(";")[0])

    assert datos["oido"] == "whisper"


def test_sin_clave_se_cae_al_oido_del_navegador() -> None:
    """Peor en español, pero mejor que quedarse sordo."""
    with mock.patch("ai_architect.voz.escuchar.disponible", return_value=False):
        pagina = conversar._componer(".")

    datos = json.loads(pagina.split("window.DATOS_ARQUITECTO = ")[-1].split(";")[0])

    assert datos["oido"] == "navegador"


def test_se_dice_quien_te_oye_y_cuanto_cuesta() -> None:
    """Que el audio salga del equipo no puede ser una sorpresa."""
    with mock.patch("ai_architect.voz.escuchar.disponible", return_value=True):
        assert "OpenAI" in conversar._quien_oye()
        assert "0.006" in conversar._quien_oye()

    with mock.patch("ai_architect.voz.escuchar.disponible", return_value=False):
        assert "Google" in conversar._quien_oye()


# --- No conversar consigo mismo ---------------------------------------------
#
# Pasó en la primera prueba de verdad: oyó "Revisa el changelog", contestó,
# y acto seguido se oyó a sí mismo por los altavoces. El navegador se tapa
# los oídos mientras habla, pero eso depende de que su reloj y el del audio
# vayan a la par —no van— y de que no haya dos pestañas escuchando.


def test_reconoce_su_propia_voz() -> None:
    assert conversar.es_eco(
        "Buenas tardes, Efraín. Puntuación 99.26, 41 incidencias.",
        "Buenas tardes, Efraín. Puntuación 99.26, 41 incidencias. Aprobado.",
    )


def test_un_trozo_de_lo_que_dijo_tambien_es_eco() -> None:
    """El micro coge la mitad de la frase, no la frase entera."""
    assert conversar.es_eco(
        "cuarenta y una incidencias aprobado",
        "Puntuación 99.26, cuarenta y una incidencias. Aprobado.",
    )


def test_las_tildes_y_los_signos_no_estorban() -> None:
    """Whisper puntúa a su manera; comparar en crudo fallaría siempre."""
    assert conversar.es_eco(
        "buenas tardes efrain todo esta en orden",
        "¡Buenas tardes, Efraín! Todo está en orden.",
    )


def test_una_orden_de_verdad_no_es_eco() -> None:
    """Lo que más importa: no tragarse una orden legítima por parecerse."""
    assert not conversar.es_eco(
        "revisa el changelog y dime que falta",
        "Buenas tardes, Efraín. El entorno está healthy. Buena tarde, Efraín.",
    )


def test_una_orden_corta_nunca_se_descarta() -> None:
    """ "sí", "ya" o "para" salen en cualquier respuesta y son órdenes."""
    assert not conversar.es_eco("para", "Ya paré, Efraín, no hay nada que parar.")


def test_sin_nada_dicho_antes_no_hay_eco() -> None:
    assert not conversar.es_eco("revisa el proyecto", "")


def test_lo_que_dice_se_recuerda_para_reconocerlo() -> None:
    with mock.patch("ai_architect.commands.pide.run", return_value=respondiendo()):
        with mock.patch.object(
            conversar.motor_de_voz,
            "preparar",
            return_value={"texto": "Todo en orden, Efraín.", "segundos": 1.0},
        ):
            conversar.atender("revisa", ".", si=False)

    assert conversar._ultimo_dicho == "Todo en orden, Efraín."


# --- Un solo micrófono ------------------------------------------------------
#
# Abrir la cara dos veces dejaba dos pestañas escuchando. Mientras una
# hablaba, la otra la oía por los altavoces y la devolvía como orden: en el
# registro se veían los ecos por duplicado.


def test_cada_pagina_se_lleva_su_turno() -> None:
    primera = conversar._componer(".")
    segunda = conversar._componer(".")

    def turno(pagina: str) -> str:
        return json.loads(pagina.split("window.DATOS_ARQUITECTO = ")[-1].split(";")[0])[
            "turno"
        ]

    assert turno(primera) != turno(segunda)


def test_manda_la_ultima_que_se_abrio() -> None:
    conversar._componer(".")
    ultima = conversar._componer(".")

    esperado = json.loads(ultima.split("window.DATOS_ARQUITECTO = ")[-1].split(";")[0])[
        "turno"
    ]

    assert conversar._turno == esperado


# --- El registro tiene que servir de algo -----------------------------------


def test_el_registro_no_repite_el_saludo() -> None:
    """Imprimía la primera línea, y la primera línea siempre es el saludo."""
    respuesta = "Buenas tardes, Efraín.\n\nPuntuación 99.26.\n\nBuena tarde, Efraín."

    assert conversar._resumen(respuesta) == "Puntuación 99.26."


def test_una_respuesta_de_una_sola_parte_se_deja_entera() -> None:
    assert conversar._resumen("Aquí sigo.") == "Aquí sigo."


def test_una_respuesta_vacia_no_revienta() -> None:
    assert conversar._resumen("") == ""


# --- Que no se quede callado ------------------------------------------------
#
# `agents` tarda medio minuto y en todo ese rato la cara no decía ni hacía
# nada. Parecía colgada.


def test_las_muletillas_se_preparan_al_arrancar(tmp_path: Path) -> None:
    """Sintetizarlas en el momento añadiría la espera que vienen a tapar."""
    falso = tmp_path / "x.wav"
    falso.write_bytes(b"RIFF")

    with mock.patch.object(
        conversar.motor_de_voz,
        "preparar",
        return_value={"archivo": falso, "motor": "piper", "segundos": 1.0},
    ):
        cuantas = (
            conversar.preparar_rellenos.__wrapped__()
            if hasattr(conversar.preparar_rellenos, "__wrapped__")
            else (
                conversar.preparar_rellenos.__wrapped__()
                if hasattr(conversar.preparar_rellenos, "__wrapped__")
                else conversar.preparar_rellenos()
            )
        )

    assert cuantas == len(conversar.RELLENOS)


def test_cada_muletilla_va_a_su_archivo(tmp_path: Path) -> None:
    """Comparten el temporal de `hablar`: la última pisaría a las demás."""
    falso = tmp_path / "x.wav"
    falso.write_bytes(b"RIFF")

    with mock.patch.object(
        conversar.motor_de_voz,
        "preparar",
        return_value={"archivo": falso, "motor": "piper", "segundos": 1.0},
    ):
        (
            conversar.preparar_rellenos.__wrapped__()
            if hasattr(conversar.preparar_rellenos, "__wrapped__")
            else (
                conversar.preparar_rellenos.__wrapped__()
                if hasattr(conversar.preparar_rellenos, "__wrapped__")
                else conversar.preparar_rellenos()
            )
        )

    archivos = {str(r["archivo"]) for r in conversar._rellenos_listos}

    assert len(archivos) == len(conversar.RELLENOS)


def test_sin_voz_no_hay_muletillas() -> None:
    with mock.patch.object(
        conversar.motor_de_voz,
        "preparar",
        return_value={"archivo": None, "motor": "", "segundos": 0},
    ):
        assert (
            conversar.preparar_rellenos.__wrapped__()
            if hasattr(conversar.preparar_rellenos, "__wrapped__")
            else (
                conversar.preparar_rellenos.__wrapped__()
                if hasattr(conversar.preparar_rellenos, "__wrapped__")
                else conversar.preparar_rellenos() == 0
            )
        )

    assert conversar.soltar_relleno() is None


def test_una_tarea_rapida_no_lleva_muletilla() -> None:
    """Decir "dame un segundo" y contestar en el mismo aliento queda peor."""
    buzon = conversar.queue.Queue(maxsize=1)

    with mock.patch.object(
        conversar, "atender", return_value={"respuesta": "ya", "ms": 0}
    ):
        with mock.patch.object(conversar, "soltar_relleno") as muletilla:
            conversar._trabajar(buzon, "hola", ".", False)

    muletilla.assert_not_called()
    assert buzon.get_nowait()["respuesta"] == "ya"


def test_una_tarea_lenta_si(monkeypatch) -> None:
    import time

    buzon = conversar.queue.Queue(maxsize=1)

    monkeypatch.setattr(conversar, "MERECE_RELLENO", 0.05)

    def tarda(*_):
        time.sleep(0.4)

        return {"respuesta": "listo", "ms": 0}

    with mock.patch.object(conversar, "atender", side_effect=tarda):
        with mock.patch.object(
            conversar, "soltar_relleno", return_value={"texto": "Dame un segundo."}
        ) as muletilla:
            conversar._trabajar(buzon, "revisa", ".", False)

    muletilla.assert_called_once()
    assert buzon.get_nowait()["respuesta"] == "listo"


def test_si_la_tarea_revienta_igual_contesta() -> None:
    """Un buzón que nunca se llena deja la página colgada para siempre."""
    buzon = conversar.queue.Queue(maxsize=1)

    with mock.patch.object(conversar, "atender", side_effect=RuntimeError("boom")):
        conversar._trabajar(buzon, "revisa", ".", False)

    assert "no pude terminar" in buzon.get_nowait()["respuesta"]


def test_el_panel_y_la_ventana_viajan_con_la_respuesta() -> None:
    with mock.patch(
        "ai_architect.commands.pide.run",
        return_value={
            "explanation": "Son las tres.",
            "panel": {"tipo": "reloj"},
            "window": "ampliar",
            "instant": True,
        },
    ):
        with mock.patch.object(
            conversar.motor_de_voz, "preparar", return_value={"segundos": 1.0}
        ):
            salida = conversar.atender("qué hora es", ".", si=False)

    assert salida["panel"]["tipo"] == "reloj"
    assert salida["ventana"] == "ampliar"
    assert salida["instantanea"] is True


# --- Que la respuesta no se pierda ------------------------------------------
#
# El fallo que dejaba la cara "pensando" para siempre: la página pide la
# respuesta en cuanto le dan el resguardo —o sea, casi siempre antes de que
# la tarea termine— y al pedirla se sacaba el buzón del diccionario. Cuando
# la tarea acababa ya no encontraba dónde dejar el resultado, lo tiraba, y
# la página esperaba algo que nunca iba a llegar.


def test_la_respuesta_llega_aunque_ya_se_haya_pedido() -> None:
    buzon = conversar.queue.Queue(maxsize=1)

    # Justo lo que hacía el servidor: pedirla antes de que exista.
    conversar._pendientes["x"] = buzon
    conversar._pendientes.pop("x")

    with mock.patch.object(
        conversar, "atender", return_value={"respuesta": "listo", "ms": 0}
    ):
        conversar._trabajar(buzon, "revisa", ".", False)

    assert buzon.get_nowait()["respuesta"] == "listo"


# --- Que solo escuche lo que va con él --------------------------------------


@pytest.fixture(autouse=True)
def conversacion_fria():
    """Cada prueba empieza sin conversación viva detrás."""
    conversar._ultima_vez = 0.0

    yield

    conversar._ultima_vez = 0.0


@pytest.mark.parametrize(
    ("dicho", "esperado"),
    [
        ("Arquitecto, revisa el proyecto", "revisa el proyecto"),
        ("arquitecto revisa el proyecto", "revisa el proyecto"),
        ("Architect, dame la puntuación", "dame la puntuacion"),
    ],
)
def test_si_lo_llamas_por_su_nombre_te_hace_caso(dicho: str, esperado: str) -> None:
    para_mi, orden = conversar.dirigido_a_mi(dicho, ahora=0.0)

    assert para_mi is True
    assert orden == esperado


@pytest.mark.parametrize(
    "ruido",
    [
        "y entonces le dije que no viniera",
        "pásame la sal",
        "mañana nos vemos en la oficina",
        "",
    ],
)
def test_lo_que_no_va_con_el_se_ignora(ruido: str) -> None:
    """Un micro abierto oye la tele, el pasillo y el teléfono de al lado."""
    para_mi, _ = conversar.dirigido_a_mi(ruido, ahora=0.0)

    assert para_mi is False


def test_dentro_de_la_conversacion_no_hay_que_repetir_el_nombre() -> None:
    """Nadie dice el nombre en cada frase de una conversación."""
    conversar._ultima_vez = 100.0

    para_mi, orden = conversar.dirigido_a_mi("y ahora la puntuación", ahora=105.0)

    assert para_mi is True
    assert orden == "y ahora la puntuación"


def test_pasado_el_rato_hay_que_volver_a_llamarlo() -> None:
    conversar._ultima_vez = 100.0

    para_mi, _ = conversar.dirigido_a_mi(
        "y ahora la puntuación", ahora=100.0 + conversar.SEGUIMIENTO + 1
    )

    assert para_mi is False


def test_solo_el_nombre_sirve_de_llamada() -> None:
    """ "Arquitecto" a secas es llamarlo, no una orden vacía."""
    para_mi, orden = conversar.dirigido_a_mi("Arquitecto", ahora=0.0)

    assert para_mi is True
    assert orden.strip() != ""


def test_el_nombre_en_mitad_de_la_frase_no_cuenta() -> None:
    """ "le dije al arquitecto que viniera" es contarlo, no pedírselo."""
    para_mi, _ = conversar.dirigido_a_mi(
        "le dije al arquitecto que viniera mañana", ahora=0.0
    )

    assert para_mi is False


def test_contestar_reabre_la_conversacion() -> None:
    with mock.patch("ai_architect.commands.pide.run", return_value=respondiendo()):
        with mock.patch.object(
            conversar.motor_de_voz, "preparar", return_value={"segundos": 1.0}
        ):
            conversar.atender("revisa", ".", si=False)

    assert conversar._ultima_vez > 0


# --- La ventana de conversación empieza cuando acaba de hablar --------------
#
# Con 25 s y contando desde que *prepara* la respuesta, una contestación
# larga se comía la ventana entera: para cuando el usuario abría la boca ya
# había caducado y su frase se descartaba con un "no era para mí".


def test_la_cuenta_empieza_cuando_termina_de_hablar() -> None:
    with mock.patch("ai_architect.commands.pide.run", return_value=respondiendo()):
        with mock.patch.object(
            conversar.motor_de_voz, "preparar", return_value={"segundos": 30.0}
        ):
            antes = conversar.time.monotonic()

            conversar.atender("revisa", ".", si=False)

    # 30 segundos hablando: la ventana no empieza hasta el final.
    assert conversar._ultima_vez >= antes + 29


def test_una_respuesta_larga_ya_no_se_come_la_ventana() -> None:
    """El caso real: contesta 30 s y la siguiente frase debe entrar."""
    with mock.patch("ai_architect.commands.pide.run", return_value=respondiendo()):
        with mock.patch.object(
            conversar.motor_de_voz, "preparar", return_value={"segundos": 30.0}
        ):
            conversar.atender("revisa", ".", si=False)

    # Diez segundos después de terminar de hablar.
    para_mi, _ = conversar.dirigido_a_mi(
        "pásalo a word", ahora=conversar._ultima_vez + 10
    )

    assert para_mi is True


def test_la_ventana_es_larga_de_verdad() -> None:
    """Leer lo que salió en la ventana y pensar qué pedir lleva su tiempo."""
    assert conversar.SEGUIMIENTO >= 60
