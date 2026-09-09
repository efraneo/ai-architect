"""Mandar el celular: entender la frase, formar la orden y mandarla por Telegram."""

from __future__ import annotations

from unittest import mock

import pytest

from ai_architect.canales import celular
from ai_architect.commands import celular as cmd_celular
from ai_architect.commands import respuestas


@pytest.fixture(autouse=True)
def perfil_de_prueba(tmp_path, monkeypatch):
    """Sin perfil, `pide` contesta «es la primera vez que hablamos» en vez de la orden."""
    from pathlib import Path as _P

    from ai_architect.core import perfil

    archivo = _P(tmp_path) / "perfil.json"
    monkeypatch.setattr(perfil, "ARCHIVO", archivo)
    perfil.configurar("Efraín", archivo=archivo)


@pytest.fixture
def con_telegram(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t0k")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")


@pytest.mark.parametrize(
    ("frase", "esperado"),
    [
        ("llama a Juan", ("llamar", "Juan")),
        ("Llámale a mi mamá", ("llamar", "mi mamá")),
        ("marca 3001234567", ("llamar", "3001234567")),
        ("cuelga", ("colgar", "")),
        ("cuelga la llamada", ("colgar", "")),
        ("bloquea el celular", ("bloquear", "")),
        ("bloquea la pantalla", ("bloquear", "")),
        ("pon la canción Tití me preguntó", ("musica", "Tití me preguntó")),
        ("pon música de Bad Bunny", ("musica", "Bad Bunny")),
        ("reproduce Bohemian Rhapsody en el celular", ("musica", "Bohemian Rhapsody")),
        ("pausa la música", ("pausar", "")),
        ("siguiente canción", ("siguiente", "")),
        ("volumen al 30", ("volumen", "30")),
        ("abre WhatsApp en el celular", ("abrir", "WhatsApp")),
        ("¿dónde está mi celular?", ("sonar", "")),
        ("desbloquea el celular", ("desbloquear", "")),
    ],
)
def test_entiende_las_ordenes(frase: str, esperado: tuple) -> None:
    assert celular.entender(frase) == esperado


@pytest.mark.parametrize(
    "frase",
    ["revisa el proyecto", "abre el archivo main.py", "pon atención", "qué hora es"],
)
def test_lo_que_no_es_del_celular(frase: str) -> None:
    assert celular.entender(frase) is None


def test_forma_la_orden_como_la_lee_el_telefono() -> None:
    assert celular.formar("musica", "Tití") == "\U0001f4f1 MUSICA|Tití"
    assert celular.formar("colgar") == "\U0001f4f1 COLGAR|"


def test_los_contactos_se_guardan_y_resuelven() -> None:
    assert celular.guardar_contacto("Juan Pérez", "+57 300 123 4567")
    assert celular.numero_de("juan") == "+573001234567"
    assert celular.numero_de("Juan Pérez") == "+573001234567"
    assert celular.numero_de("300 555 1234") == "3005551234"
    assert celular.numero_de("Pedro") == "Pedro"
    assert not celular.guardar_contacto("", "123")


def test_ordenar_manda_por_telegram(con_telegram) -> None:
    with mock.patch.object(
        celular.telegram, "enviar", return_value={"ok": True}
    ) as enviar:
        salida = celular.ordenar("bloquear")

    assert salida["ok"] and enviar.call_args.args[0] == "\U0001f4f1 BLOQUEAR|"


def test_ordenar_llamar_resuelve_el_contacto(con_telegram) -> None:
    celular.guardar_contacto("Ana", "3001112233")

    with mock.patch.object(
        celular.telegram, "enviar", return_value={"ok": True}
    ) as enviar:
        assert celular.ordenar("llamar", "Ana")["ok"]

    assert enviar.call_args.args[0] == "\U0001f4f1 LLAMAR|3001112233"


def test_sin_telegram_no_se_puede() -> None:
    assert "Telegram" in celular.ordenar("bloquear")["error"]


def test_una_accion_desconocida() -> None:
    assert "no sé" in celular.ordenar("volar")["error"]


# --- Por voz, al instante -------------------------------------------------------------


def test_por_voz_lo_seguro_sale_al_momento(con_telegram) -> None:
    with mock.patch.object(
        celular.telegram, "enviar", return_value={"ok": True}
    ) as enviar:
        salida = respuestas.responder("pausa la música")

    assert salida is not None and salida["respuesta"] == "Pausada."
    assert enviar.call_args.args[0] == "\U0001f4f1 PAUSAR|"


def test_por_voz_llamar_pide_permiso(con_telegram) -> None:
    from ai_architect.commands import pendientes

    with mock.patch.object(celular.telegram, "enviar") as enviar:
        salida = respuestas.responder("llama a Juan")

    assert salida is not None and "¿Llamo a Juan?" in salida["respuesta"]
    assert salida["pregunta_permiso"] and len(salida["pending_ids"]) == 1
    enviar.assert_not_called()

    # Al aprobar, la herramienta celular_llamar manda la orden.
    with mock.patch.object(
        celular.telegram, "enviar", return_value={"ok": True}
    ) as enviar:
        aprobado = pendientes.run("aprobar", salida["pending_ids"][0][:8])

    assert aprobado["success"] and enviar.call_args.args[0] == "\U0001f4f1 LLAMAR|Juan"


def test_por_voz_desbloquear_se_explica() -> None:
    salida = respuestas.responder("desbloquea el celular")

    assert salida is not None and "no lo permite" in salida["respuesta"]


def test_sin_bot_por_voz_lo_dice() -> None:
    salida = respuestas.responder("bloquea el celular")

    assert salida is not None and "Telegram" in salida["respuesta"]


def test_recuerda_el_numero_de_un_contacto(con_telegram) -> None:
    salida = respuestas.responder("recuerda que el número de Juan es 300 123 4567")

    assert salida is not None and "Apuntado" in salida["respuesta"]
    assert celular.numero_de("juan") == "3001234567"


def test_la_pregunta_de_permiso_no_se_repite(con_telegram) -> None:
    from ai_architect.commands import conversar

    conversar._permiso_pendiente = []

    with mock.patch.object(
        conversar.motor_de_voz, "preparar", return_value={"segundos": 0}
    ):
        with mock.patch.object(celular.telegram, "enviar"):
            salida = conversar.atender("llama a Juan", ".", si=False)

    assert "¿Llamo a Juan?" in salida["respuesta"]
    assert "¿Los aplico?" not in salida["respuesta"]
    assert conversar.hay_permiso_pendiente()
    conversar._permiso_pendiente = []


# --- El comando ------------------------------------------------------------------------


def test_el_comando_celular(con_telegram) -> None:
    assert "órdenes" in cmd_celular.run()["explanation"]

    with mock.patch.object(celular.telegram, "enviar", return_value={"ok": True}):
        salida = cmd_celular.run("pon música de Shakira")

    assert salida["success"] and "MUSICA|Shakira" in salida["explanation"]
    assert not cmd_celular.run("hazme un café")["success"]
    assert "no lo permite" in cmd_celular.run("desbloquea el celular")["explanation"]
