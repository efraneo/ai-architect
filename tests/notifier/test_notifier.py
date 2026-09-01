"""El aviso por Telegram: la única capacidad que tenía la pila vieja.

`main.py` -> `engine.py` -> `agent.py` era una segunda aplicación entera,
huérfana, que apuntaba con rutas fijas a otro proyecto
(``../QUANT_TITAN_PRO``). Todo lo que hacía —analizar, planificar, pasar las
pruebas— ya lo cubre el CLI **menos una cosa**: avisar al terminar. Por eso
esto se conectó en vez de tirarse con el resto.

Y venía con tres fallos: sin token construía la URL con ``None`` y hacía la
petición igual; una excepción de red tumbaba la mejora entera; y dependía de
``python-dotenv``, que **no está declarado ni instalado** — el paquete
llevaba tiempo siendo inimportable.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

import pytest
import requests

from ai_architect.notifier.env_file import leer, valor
from ai_architect.notifier.improvement_notice import (
    avisar,
    notificaciones_activas,
    redactar,
)
from ai_architect.notifier.models import Notification, NotificationLevel
from ai_architect.notifier.telegram_notifier import TelegramNotifier

# --- Leer el .env sin dependencias ------------------------------------------


def test_lee_pares_del_archivo(tmp_path: Path) -> None:
    archivo = tmp_path / ".env"
    archivo.write_text("TOKEN=abc\nCHAT=123\n", encoding="utf-8")

    assert leer(archivo) == {"TOKEN": "abc", "CHAT": "123"}


def test_ignora_comentarios_y_lineas_vacias(tmp_path: Path) -> None:
    archivo = tmp_path / ".env"
    archivo.write_text("# un comentario\n\nTOKEN=abc\n", encoding="utf-8")

    assert leer(archivo) == {"TOKEN": "abc"}


def test_quita_las_comillas(tmp_path: Path) -> None:
    """Las comillas son del formato del archivo, no parte del valor."""
    archivo = tmp_path / ".env"
    archivo.write_text("TOKEN=\"abc\"\nCHAT='123'\n", encoding="utf-8")

    assert leer(archivo) == {"TOKEN": "abc", "CHAT": "123"}


def test_admite_export(tmp_path: Path) -> None:
    archivo = tmp_path / ".env"
    archivo.write_text("export TOKEN=abc\n", encoding="utf-8")

    assert leer(archivo) == {"TOKEN": "abc"}


def test_un_valor_con_iguales_dentro(tmp_path: Path) -> None:
    archivo = tmp_path / ".env"
    archivo.write_text("URL=https://x.com/?a=1\n", encoding="utf-8")

    assert leer(archivo)["URL"] == "https://x.com/?a=1"


def test_un_archivo_que_no_existe_no_revienta(tmp_path: Path) -> None:
    assert leer(tmp_path / "no-existe") == {}


def test_el_entorno_manda_sobre_el_archivo(tmp_path: Path) -> None:
    """La regresión: ``load_dotenv`` sin ``override=False`` pisaba lo que ya
    se había exportado a propósito."""
    archivo = tmp_path / ".env"
    archivo.write_text("TOKEN=del-archivo\n", encoding="utf-8")

    with mock.patch.dict(os.environ, {"TOKEN": "del-entorno"}):
        assert valor("TOKEN", archivo) == "del-entorno"


def test_si_no_esta_en_el_entorno_se_usa_el_archivo(tmp_path: Path) -> None:
    archivo = tmp_path / ".env"
    archivo.write_text("TOKEN=del-archivo\n", encoding="utf-8")

    with mock.patch.dict(os.environ, {}, clear=True):
        assert valor("TOKEN", archivo) == "del-archivo"


# --- El notificador ---------------------------------------------------------


@pytest.fixture
def sin_entorno():
    with mock.patch.dict(os.environ, {}, clear=True):
        yield


def test_sin_token_no_se_llama_a_la_api(tmp_path: Path, sin_entorno) -> None:
    """La regresión: construía ``.../botNone/sendMessage`` y hacía el POST."""
    notificador = TelegramNotifier(tmp_path / "no-existe")

    with mock.patch("requests.post") as post:
        resultado = notificador.send(Notification("t", "m", NotificationLevel.INFO))

    post.assert_not_called()
    assert resultado.success is False
    assert "TELEGRAM_BOT_TOKEN" in resultado.response


def test_con_token_si_se_envia(tmp_path: Path) -> None:
    entorno = {"TELEGRAM_BOT_TOKEN": "abc", "TELEGRAM_CHAT_ID": "123"}

    with mock.patch.dict(os.environ, entorno):
        notificador = TelegramNotifier(tmp_path / "no-existe")

        with mock.patch("requests.post") as post:
            post.return_value = mock.Mock(ok=True, text="{}")

            resultado = notificador.send(
                Notification("t", "m", NotificationLevel.SUCCESS)
            )

    post.assert_called_once()
    assert resultado.success is True


def test_un_fallo_de_red_no_lanza(tmp_path: Path) -> None:
    """La regresión: la excepción subía y tumbaba la mejora."""
    entorno = {"TELEGRAM_BOT_TOKEN": "abc", "TELEGRAM_CHAT_ID": "123"}

    with mock.patch.dict(os.environ, entorno):
        notificador = TelegramNotifier(tmp_path / "no-existe")

        with mock.patch(
            "requests.post",
            side_effect=requests.ConnectionError("sin red"),
        ):
            resultado = notificador.send(
                Notification("t", "m", NotificationLevel.ERROR)
            )

    assert resultado.success is False
    assert "sin red" in resultado.response


# --- El interruptor ---------------------------------------------------------


def test_por_defecto_no_se_avisa() -> None:
    """Avisar es una llamada de red a un servicio externo."""
    with mock.patch.dict(os.environ, {}, clear=True):
        assert notificaciones_activas() is False


def test_se_enciende_con_notify() -> None:
    with mock.patch.dict(os.environ, {"NOTIFY": "true"}):
        assert notificaciones_activas() is True


# --- El mensaje -------------------------------------------------------------


def test_el_mensaje_lleva_lo_que_paso() -> None:
    mensaje = redactar(
        {
            "instruction": "extrae el validador",
            "patch_id": "abc123",
            "approved": True,
            "files": 3,
            "duration": 12.5,
            "tests": {"executed": True, "success": True},
        }
    )

    assert "extrae el validador" in mensaje
    assert "abc123" in mensaje
    assert "aprobado" in mensaje
    assert "verde" in mensaje


def test_una_suite_en_rojo_se_dice() -> None:
    mensaje = redactar({"tests": {"executed": True, "success": False}})

    assert "rojo" in mensaje


def test_una_suite_sin_ejecutar_no_se_da_por_buena() -> None:
    mensaje = redactar({"tests": {"executed": False, "success": False}})

    assert "sin ejecutar" in mensaje


def test_un_resultado_incompleto_no_revienta() -> None:
    assert isinstance(redactar({}), str)


# --- El aviso ---------------------------------------------------------------


def test_apagado_no_se_avisa() -> None:
    notificador = mock.Mock()
    resultado: dict = {}

    with mock.patch.dict(os.environ, {"NOTIFY": "false"}):
        avisar(resultado, notificador)

    notificador.success.assert_not_called()
    assert "notified" not in resultado


def test_encendido_se_avisa() -> None:
    notificador = mock.Mock()
    notificador.success.return_value = mock.Mock(success=True)

    resultado: dict = {"instruction": "algo", "approved": True}

    with mock.patch.dict(os.environ, {"NOTIFY": "true"}):
        avisar(resultado, notificador)

    notificador.success.assert_called_once()
    assert resultado["notified"] is True


def test_si_el_aviso_falla_la_mejora_no_se_entera() -> None:
    """El parche ya está generado y guardado: un aviso no puede tumbarlo."""
    notificador = mock.Mock()
    notificador.success = mock.Mock(side_effect=RuntimeError("se rompió"))

    resultado: dict = {}

    with mock.patch.dict(os.environ, {"NOTIFY": "true"}):
        avisar(resultado, notificador)

    assert resultado["notified"] is False
    assert resultado["notify_error"] == "se rompió"
