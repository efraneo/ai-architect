"""La vida diaria: agenda, casa, mundo, lo hablado y lo proactivo. Sin red:
todo lo que sale de la máquina se dobla."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pytest

from ai_architect import agenda, investigar, proactivo
from ai_architect.agente.memoria import episodios
from ai_architect.canales import hogar
from ai_architect.commands import respuestas

AHORA = datetime(2026, 9, 9, 14, 5)  # miércoles


# --- agenda ------------------------------------------------------------------------


def test_recuerdame_a_las_tres_es_hoy_a_las_quince() -> None:
    momento, texto = agenda.cuando("llamar a Juan a las tres", AHORA)

    assert momento == datetime(2026, 9, 9, 15, 0) and texto == "llamar a Juan"


def test_en_veinte_minutos() -> None:
    momento, texto = agenda.cuando("que revise el horno en veinte minutos", AHORA)

    assert momento == datetime(2026, 9, 9, 14, 25) and texto == "revise el horno"


def test_manana_a_las_ocho_y_media() -> None:
    momento, texto = agenda.cuando("pagar el recibo mañana a las 8 y media", AHORA)

    assert momento == datetime(2026, 9, 10, 8, 30) and texto == "pagar el recibo"


def test_a_las_diez_de_la_noche() -> None:
    momento, _ = agenda.cuando("sacar la basura a las diez de la noche", AHORA)

    assert momento == datetime(2026, 9, 9, 22, 0)


def test_una_hora_ya_pasada_es_manana() -> None:
    momento, _ = agenda.cuando("reunión a las 13:00", AHORA)

    assert momento == datetime(2026, 9, 10, 13, 0)


def test_por_voz_apunta_y_luego_vence() -> None:
    salida = agenda.por_voz("Recuérdame llamar a Juan a las tres", AHORA)

    assert (
        salida is not None
        and "Apuntado: llamar a Juan, hoy a las 15:00" in salida["respuesta"]
    )
    assert agenda.pendientes(AHORA.date())[0]["texto"] == "llamar a Juan"
    assert agenda.vencidos(datetime(2026, 9, 9, 14, 59)) == []

    vencido = agenda.vencidos(datetime(2026, 9, 9, 15, 0))

    assert [v["texto"] for v in vencido] == ["llamar a Juan"]
    assert agenda.vencidos(datetime(2026, 9, 9, 15, 1)) == []  # se dice una vez


def test_que_tengo_hoy_y_cancelar() -> None:
    agenda.por_voz("avísame en dos horas que saque el pan", AHORA)
    agenda.por_voz("recuérdame mañana a las nueve el dentista", AHORA)

    hoy = agenda.por_voz("qué tengo hoy", AHORA)
    manana = agenda.por_voz("qué tengo mañana", AHORA)

    assert (
        hoy is not None
        and "saque el pan" in hoy["respuesta"]
        and "dentista" not in hoy["respuesta"]
    )
    assert manana is not None and "dentista" in manana["respuesta"]
    assert (
        "cancelé 2" in agenda.por_voz("cancela los recordatorios", AHORA)["respuesta"]
    )
    assert "No tienes nada" in agenda.por_voz("qué tengo hoy", AHORA)["respuesta"]


def test_sin_hora_pregunta_y_recuerda_que_es_memoria() -> None:
    assert (
        "A qué hora" in agenda.por_voz("recuérdame comprar leche", AHORA)["respuesta"]
    )
    assert agenda.por_voz("recuerda que mi café es expreso doble", AHORA) is None
    assert agenda.por_voz("abre Word", AHORA) is None


def test_el_contexto_dice_la_hora_y_lo_pendiente() -> None:
    agenda.por_voz("recuérdame el dentista a las cuatro", AHORA)

    texto = agenda.contexto(AHORA)

    assert texto.startswith("Son las 14:05 (tarde)") and "dentista a las 16:00" in texto


# --- investigar ------------------------------------------------------------------------


def test_el_clima_se_lee_de_open_meteo(monkeypatch) -> None:
    def falso(url):
        if "geocoding" in url:
            return {
                "results": [
                    {
                        "name": "Bogotá",
                        "country": "Colombia",
                        "latitude": 4.6,
                        "longitude": -74.1,
                    }
                ]
            }

        return {
            "current": {
                "temperature_2m": 17.4,
                "precipitation": 0,
                "weather_code": 3,
                "wind_speed_10m": 9,
            },
            "hourly": {
                "time": [
                    (
                        datetime.now().replace(minute=0, second=0, microsecond=0)
                    ).isoformat()
                ],
                "precipitation_probability": [80],
            },
        }

    monkeypatch.setattr(investigar, "_json", falso)
    monkeypatch.setenv("ARCHITECT_CIUDAD", "Bogotá")

    datos = investigar.clima()

    assert (
        datos["ok"]
        and datos["estado"] == "nublado"
        and datos["probabilidad_lluvia_3h"] == 80
    )
    assert "17 grados, nublado" in investigar.clima_en_palabras(datos)
    assert "80 %" in investigar.clima_en_palabras(datos)
    assert "80 %" in investigar.alerta_de_lluvia()


def test_sin_ciudad_la_pide(monkeypatch) -> None:
    monkeypatch.delenv("ARCHITECT_CIUDAD", raising=False)

    salida = investigar.por_voz("qué clima hace")

    assert salida is not None and "qué ciudad" in salida["respuesta"]


def test_la_ciudad_sale_de_la_memoria(monkeypatch) -> None:
    from ai_architect.agente import memoria

    monkeypatch.delenv("ARCHITECT_CIUDAD", raising=False)
    memoria.recordar("vivo en Bucaramanga")

    assert investigar.ciudad() == "Bucaramanga"


def test_las_noticias_se_leen_del_rss(monkeypatch) -> None:
    rss = (
        "<rss><channel><item><title>Sube el dólar - El Tiempo</title><source>El Tiempo</source></item>"
        "<item><title>Lluvias en Bogotá</title></item></channel></rss>"
    ).encode()
    monkeypatch.setattr(investigar, "_obtener", lambda url: rss)

    salida = investigar.por_voz("noticias de economía")

    assert salida is not None and "Sube el dólar" in salida["respuesta"]
    assert "El Tiempo" in salida["panel"]["cuerpo"]


def test_el_trafico_dice_que_falta_la_clave() -> None:
    salida = investigar.por_voz("cómo está el tráfico")

    assert salida is not None and "Google Maps" in salida["respuesta"]


def test_correos_urgentes(monkeypatch) -> None:
    from ai_architect.canales import correo

    monkeypatch.setattr(correo, "puede_leer", lambda: True)
    monkeypatch.setattr(
        correo,
        "leer",
        lambda n=5: {
            "ok": True,
            "correos": [
                {"de": "Rafael", "asunto": "URGENTE: firma hoy", "texto": ""},
                {"de": "Tienda", "asunto": "Ofertas", "texto": "hola"},
            ],
        },
    )

    salida = investigar.por_voz("tengo correos nuevos")

    assert (
        salida is not None
        and "1 correo(s)" in salida["respuesta"]
        and "Rafael" in salida["respuesta"]
    )
    assert "Rafael" in investigar.aviso_de_correo()


# --- hogar ---------------------------------------------------------------------------------


CASA = [
    {
        "entity_id": "light.sala",
        "state": "off",
        "attributes": {"friendly_name": "Luz de la sala"},
    },
    {
        "entity_id": "cover.garaje",
        "state": "closed",
        "attributes": {"friendly_name": "Puerta del garaje"},
    },
    {
        "entity_id": "sensor.temperatura",
        "state": "21.5",
        "attributes": {"friendly_name": "Temperatura", "unit_of_measurement": "°C"},
    },
]


@pytest.fixture
def casa(monkeypatch):
    monkeypatch.setenv("HOGAR_URL", "http://casa.local:8123")
    monkeypatch.setenv("HOGAR_TOKEN", "t")
    llamadas: list[tuple[str, dict | None]] = []

    def pedir(ruta, cuerpo=None):
        llamadas.append((ruta, cuerpo))
        return CASA if ruta == "states" else []

    monkeypatch.setattr(hogar, "_pedir", pedir)
    return llamadas


def test_enciende_la_luz_de_la_sala(casa) -> None:
    salida = hogar.por_voz("enciende la luz de la sala")

    assert salida is not None and "Luz de la sala encendido" in salida["respuesta"]
    assert casa[-1] == ("services/light/turn_on", {"entity_id": "light.sala"})


def test_abre_el_garaje_es_open_cover(casa) -> None:
    hogar.por_voz("abre la puerta del garaje")

    assert casa[-1][0] == "services/cover/open_cover"


def test_como_esta_la_puerta(casa) -> None:
    assert "cerrado" in hogar.por_voz("cómo está la puerta del garaje")["respuesta"]
    assert "21.5 °C" in hogar.por_voz("cómo está la temperatura")["respuesta"]


def test_abre_word_no_es_de_la_casa(casa) -> None:
    assert hogar.por_voz("abre Word") is None
    assert hogar.por_voz("cierra Architect") is None


def test_sin_configurar_pide_los_datos(monkeypatch) -> None:
    salida = hogar.por_voz("enciende la luz de la cocina")

    assert salida is not None and "Home Assistant" in str(salida)


def test_lo_que_no_existe_se_dice(casa) -> None:
    assert "no encuentro" in hogar.por_voz("apaga la lámpara del sótano")["respuesta"]


# --- episodios --------------------------------------------------------------------------------


@pytest.fixture
def registro() -> Path:
    ruta = episodios.ruta_registro()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        "2026-09-07 10:00:00 > Dejé las llaves en el cajón de la cocina.\n"
        "2026-09-07 10:00:05 < Apuntado.\n"
        "2026-09-08 09:30:00 > Revisa el proyecto.\n"
        "2026-09-08 09:30:20 < 13 agentes revisaron el proyecto.\n"
        "2026-09-08 09:31:00 ~ (eco descartado) hola\n"
        "2026-09-09 11:00:00 > Abre Word.\n",
        encoding="utf-8",
    )
    return ruta


def test_donde_deje_las_llaves(registro) -> None:
    salida = episodios.por_voz("dónde dejé las llaves", date(2026, 9, 9))

    assert salida is not None and "cajón de la cocina" in salida["respuesta"]
    assert "el lunes 7" in salida["respuesta"]


def test_que_hablamos_ayer(registro) -> None:
    salida = episodios.por_voz("qué hablamos ayer", date(2026, 9, 9))

    assert (
        "Revisa el proyecto" in salida["respuesta"]
        and "13 agentes" in salida["respuesta"]
    )
    assert "eco" not in salida["panel"]["cuerpo"]


def test_que_te_dije_el_lunes_sobre_las_llaves(registro) -> None:
    salida = episodios.por_voz(
        "qué te dije el lunes sobre las llaves", date(2026, 9, 9)
    )

    assert "cajón" in salida["respuesta"] and "Apuntado" not in salida["respuesta"]


def test_sin_registro_no_inventa() -> None:
    salida = episodios.por_voz("qué te dije de las llaves", date(2026, 9, 9))

    assert salida is not None and "No encuentro" in salida["respuesta"]
    assert episodios.por_voz("abre Word") is None


# --- proactivo ----------------------------------------------------------------------------------


def test_el_latido_dice_los_recordatorios_vencidos(monkeypatch) -> None:
    proactivo.reiniciar()
    monkeypatch.setitem(proactivo.DISPARADORES, "lluvia", lambda ahora: [])
    monkeypatch.setitem(proactivo.DISPARADORES, "correo", lambda ahora: [])
    monkeypatch.setitem(proactivo.DISPARADORES, "ci", lambda ahora: [])
    agenda.por_voz("recuérdame el dentista a las cuatro", AHORA)

    assert proactivo.latido(datetime(2026, 9, 9, 15, 59)) == []
    avisos = proactivo.latido(datetime(2026, 9, 9, 16, 0))

    assert len(avisos) == 1 and "te recuerdo: el dentista" in avisos[0]


def test_la_lluvia_no_se_repite_ni_se_consulta_a_cada_latido(monkeypatch) -> None:
    proactivo.reiniciar()
    veces = []
    monkeypatch.setattr(
        investigar, "alerta_de_lluvia", lambda: veces.append(1) or "Ojo: lluvia."
    )

    assert proactivo.lluvia(AHORA) == ["Ojo: lluvia."]
    assert proactivo.lluvia(AHORA) == []  # espaciado
    assert len(veces) == 1

    proactivo._ultima_vez.clear()
    assert proactivo.lluvia(AHORA) == []  # mismo aviso, no se repite


def test_un_disparador_roto_no_calla_a_los_demas(monkeypatch) -> None:
    proactivo.reiniciar()

    def explota(ahora):
        raise RuntimeError("sin red")

    monkeypatch.setitem(proactivo.DISPARADORES, "lluvia", explota)
    monkeypatch.setitem(proactivo.DISPARADORES, "correo", lambda ahora: ["correo"])
    monkeypatch.setitem(proactivo.DISPARADORES, "ci", lambda ahora: [])

    assert proactivo.latido(AHORA) == ["correo"]


# --- todo junto, por la voz -----------------------------------------------------------------------


def test_respuestas_atiende_la_vida_diaria(casa, monkeypatch) -> None:
    assert (
        "Apuntado"
        in respuestas.responder("recuérdame llamar a Juan en una hora")["respuesta"]
    )
    assert "encendido" in respuestas.responder("prende la luz de la sala")["respuesta"]
    assert "Google Maps" in respuestas.responder("cómo está el tráfico")["respuesta"]
    # «recuerda que…» sigue siendo memoria de hechos, no agenda
    assert "a las" not in respuestas.responder("recuerda que vivo en Cali").get(
        "respuesta", ""
    )


def test_el_guion_lleva_la_hora(tmp_path: Path) -> None:
    from ai_architect.agente.guion import prompt_sistema

    assert "Son las " in prompt_sistema(tmp_path, "Efraín", False)


def test_la_agenda_se_guarda_en_la_carpeta_de_architect() -> None:
    agenda.recordar("x", AHORA)

    assert json.loads(agenda.ruta().read_text(encoding="utf-8"))[0]["texto"] == "x"
