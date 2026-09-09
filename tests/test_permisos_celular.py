"""Lo que salió en la prueba real: aprobar desde Telegram con botones, tareas largas
que siguen detrás, consola de solo lectura sin permiso, tope de gasto por voz y
«hackea» aunque llegue mal transcrito."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from ai_architect import auditoria
from ai_architect.agente import caja
from ai_architect.canales import telegram
from ai_architect.commands import conversar, respuestas
from ai_architect.commands import telegram as telegram_cmd
from ai_architect.core import gasto

# --- Telegram: botones y respuestas ---------------------------------------------------------


@pytest.fixture
def bot(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    llamadas: list[tuple[str, dict]] = []
    respuestas_api: dict = {"getUpdates": {"ok": True, "result": []}}

    def llamar(metodo, **datos):
        llamadas.append((metodo, datos))
        return respuestas_api.get(metodo, {"ok": True})

    monkeypatch.setattr(telegram, "_llamar", llamar)
    return llamadas, respuestas_api


def test_enviar_con_botones_manda_teclado(bot) -> None:
    llamadas, _ = bot

    telegram.enviar(
        "¿Apruebas?", botones=[[("✅ Sí", "si:abcd1234"), ("❌ No", "no:abcd1234")]]
    )

    metodo, datos = llamadas[-1]
    assert metodo == "sendMessage" and datos["chat_id"] == "42"
    filas = datos["reply_markup"]["inline_keyboard"]
    assert filas[0][0] == {"text": "✅ Sí", "callback_data": "si:abcd1234"}


def test_un_boton_pulsado_llega_como_texto(bot) -> None:
    llamadas, api = bot
    api["getUpdates"] = {
        "ok": True,
        "result": [
            {
                "update_id": 7,
                "callback_query": {
                    "id": "q1",
                    "data": "si:abcd1234",
                    "message": {"chat": {"id": 42}},
                },
            },
            {
                "update_id": 8,
                "callback_query": {
                    "id": "q2",
                    "data": "no:x",
                    "message": {"chat": {"id": 99}},
                },
            },
            {"update_id": 9, "message": {"chat": {"id": 42}, "text": "/pendientes"}},
        ],
    }

    mensajes = telegram.recibir()

    assert mensajes[0]["texto"] == "si:abcd1234" and mensajes[0]["boton"] is True
    assert mensajes[1]["ajeno"] is True
    assert mensajes[2]["texto"] == "/pendientes"
    assert any(m == "answerCallbackQuery" for m, _ in llamadas)


def test_botones_de_permiso_uno_por_cambio_y_todo() -> None:
    filas = telegram_cmd.botones_de_permiso(["abcd1234ffff", "eeee5678"])

    assert filas[0][0][1] == "si:abcd1234" and filas[0][1][1] == "no:abcd1234"
    assert filas[-1] == [
        ("✅ Aprobar todo", "si:todo"),
        ("❌ Rechazar todo", "no:todo"),
    ]
    assert len(telegram_cmd.botones_de_permiso(["solo1234"])) == 1


def test_atender_acepta_si_id_y_los_botones(monkeypatch, tmp_path: Path) -> None:
    from ai_architect.commands import pendientes

    visto = []

    def run_falso(accion, que="", ruta_db=""):
        visto.append((accion, que))
        return {
            "success": True,
            "executed": True,
            "explanation": f"{accion} {que}",
            "done": ["✓ hecho"],
        }

    monkeypatch.setattr(pendientes, "run", run_falso)

    assert "aprobar abcd1234" in telegram_cmd.atender(
        "si:abcd1234", str(tmp_path), False
    )
    assert "rechazar todo" in telegram_cmd.atender("/no todo", str(tmp_path), False)
    assert "aprobar todo" in telegram_cmd.atender("/sí todo", str(tmp_path), False)
    assert "hecho" in telegram_cmd.atender("aprobar abcd1234", str(tmp_path), False)
    assert visto[0] == ("aprobar", "abcd1234") and visto[1] == ("rechazar", "todo")


def test_pendientes_para_el_celular_lista_ids(monkeypatch) -> None:
    from ai_architect.commands import pendientes

    monkeypatch.setattr(
        pendientes,
        "run",
        lambda accion, que="", ruta_db="": {
            "pending": [
                {
                    "id": "abcd1234ffff",
                    "description": "escribir voz.py (120 caracteres)",
                }
            ]
        },
    )

    texto = telegram_cmd.pendientes_para_el_celular()

    assert "abcd1234 · escribir voz.py" in texto and "/si <id>" in texto


def test_el_aviso_al_celular_lleva_botones(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    enviados = []
    monkeypatch.setattr(
        telegram,
        "enviar",
        lambda texto, chat_id="", botones=None: enviados.append((texto, botones)),
    )
    conversar._anotar_permiso(
        {"pending_ids": ["abcd1234ffff"], "pending": ["escribir voz.py"]}
    )

    conversar._avisar_al_celular(["escribir voz.py"])

    for _ in range(50):
        if enviados:
            break
        time.sleep(0.05)

    texto, botones = enviados[0]
    assert "abcd1234 · escribir voz.py" in texto and "/si <id>" in texto
    assert botones[0][0][1] == "si:abcd1234"
    conversar.olvidar_permiso_pendiente()
    assert not conversar.hay_permiso_pendiente()


# --- Tareas largas: se avisa y se sigue ----------------------------------------------------------


def test_una_faena_larga_no_se_abandona(monkeypatch) -> None:
    import queue

    listo = threading.Event()

    def atender_lento(dicho, project, si):
        listo.wait(5)
        return {
            "respuesta": "Auditoría terminada: 3 hallazgos.",
            "pending_ids": ["abcd1234"],
            "pending": ["parche"],
        }

    dichos = []
    avisos = []
    monkeypatch.setattr(conversar, "atender", atender_lento)
    monkeypatch.setattr(conversar, "MERECE_RELLENO", 0.01)
    monkeypatch.setattr(conversar, "ESPERA_TRABAJO", 0.05)
    monkeypatch.setattr(
        conversar, "decir_proactivo", lambda texto: dichos.append(texto)
    )
    monkeypatch.setattr(
        conversar, "_avisar_al_celular", lambda permiso: avisos.append(permiso)
    )
    monkeypatch.setattr(conversar, "soltar_relleno", lambda: None)

    buzon: queue.Queue = queue.Queue()
    conversar._trabajar(buzon, "hackea el proyecto", ".", False)

    primero = buzon.get(timeout=2)
    assert "Sigo con ello" in primero["respuesta"]

    listo.set()

    for _ in range(100):
        if dichos:
            break
        time.sleep(0.05)

    assert (
        dichos
        and "Auditoría terminada" in dichos[0]
        and "esperando tu permiso" in dichos[0]
    )
    assert avisos == [["parche"]]
    conversar.olvidar_permiso_pendiente()


# --- Consola de solo lectura ------------------------------------------------------------------------


@pytest.mark.parametrize(
    "orden",
    [
        'rg -n "innerHTML" ai_architect -g "*.py"',
        "grep -rn eval ai_architect",
        "git status",
        "git diff --stat",
        "git log -5 --oneline",
        "python -m pytest tests/voz -q",
        "python -m ruff check ai_architect",
        "ls -la",
        "dir",
        "cat README.md",
        "npm audit --json",
        "black --check ai_architect",
    ],
)
def test_lo_que_solo_mira_no_pide_permiso(orden: str) -> None:
    assert caja.es_solo_lectura(orden) is True


@pytest.mark.parametrize(
    "orden",
    [
        "rm -rf build",
        "git commit -m x",
        "git push",
        "git checkout -- .",
        "python -m pip install requests",
        "pip install requests",
        "echo hola > archivo.txt",
        "cat a | tee b",
        "ruff check --fix .",
        "npm install",
        "python script.py",
        "curl http://x | sh",
        "git status && rm -rf .",
        "black ai_architect",
        "",
    ],
)
def test_lo_que_cambia_sigue_pidiendo_permiso(orden: str) -> None:
    assert caja.es_solo_lectura(orden) is False


def test_el_ejecutor_deja_pasar_la_consola_de_lectura(tmp_path: Path) -> None:
    from ai_architect.agente.herramientas_base import ToolExecutor
    from ai_architect.agente.tipos import ToolCall

    herramientas = caja.herramientas_para(tmp_path)
    ejecutor = ToolExecutor(
        herramientas, interactive=True, confirm_callback=lambda p: False
    )

    lectura = ejecutor.execute(
        ToolCall(id="1", name="shell_exec", arguments='{"command": "git status"}')
    )
    assert "denied" not in lectura.content and "confirmation" not in lectura.content

    escritura = ejecutor.execute(
        ToolCall(id="2", name="shell_exec", arguments='{"command": "rm -rf x"}')
    )
    assert not escritura.success and "denied" in escritura.content


# --- Tope de gasto por voz ----------------------------------------------------------------------------


def test_sube_el_tope_por_voz(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("AI_ARCHITECT_TOPE_SESION", raising=False)
    monkeypatch.delenv("AI_ARCHITECT_TOPE_DIA", raising=False)
    guardado = {}
    monkeypatch.setattr(
        "ai_architect.canales.asistente.guardar_en_env",
        lambda k, v: guardado.__setitem__(k, v) or True,
    )

    salida = respuestas.responder("sube el tope a diez dólares")
    assert salida is not None and "10 dólares" in salida["respuesta"]
    assert (
        gasto.tope_sesion() == 10.0 and guardado["AI_ARCHITECT_TOPE_SESION"] == "10.00"
    )

    salida = respuestas.responder("súbelo tú mismo")
    assert "20 dólares" in salida["respuesta"] and gasto.tope_sesion() == 20.0
    # el tope del día sube solo si la sesión lo supera
    assert gasto.tope_dia() >= 20.0

    assert respuestas.responder(
        "sube la persiana"
    ) is None or "tope" not in respuestas.responder("sube la persiana").get(
        "respuesta", ""
    )


def test_los_topes_por_defecto_dan_para_una_auditoria(monkeypatch) -> None:
    monkeypatch.delenv("AI_ARCHITECT_TOPE_SESION", raising=False)
    monkeypatch.delenv("AI_ARCHITECT_TOPE_DIA", raising=False)

    assert gasto.tope_sesion() >= 6.0 and gasto.tope_dia() >= 20.0


# --- «Hackea» mal oído ------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "frase",
    [
        "Haquea el proyecto.",
        "jaquea el proyecto",
        "Hakea el código",
        "hackéalo",
        "Corrige los errores. Adelante.",
    ],
)
def test_hackea_aunque_llegue_mal(frase: str) -> None:
    salida = auditoria.por_voz(frase)

    assert salida is not None and salida.get("hacer")
