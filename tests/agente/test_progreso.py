"""El tablón de progreso: lo que `hacer` va haciendo, contado en vivo (fase 4)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ai_architect.agente import progreso
from ai_architect.agente.eventos import EventBus, EventType
from ai_architect.agente.motor import InferenceEngine
from ai_architect.commands import hacer


@pytest.fixture
def oido():
    recibidos: list[dict[str, Any]] = []
    progreso.suscribir(recibidos.append)

    yield recibidos

    progreso.desuscribir(recibidos.append)


def test_avisar_llega_a_los_suscritos(oido: list) -> None:
    aviso = progreso.avisar("fase", fase="trabajando")

    assert oido == [aviso] and aviso["tipo"] == "fase" and aviso["cuando"] > 0


def test_un_oyente_roto_no_frena_a_los_demas(oido: list) -> None:
    def roto(_: dict) -> None:
        raise RuntimeError("boom")

    progreso.suscribir(roto)

    try:
        progreso.avisar("fase", fase="listo")

    finally:
        progreso.desuscribir(roto)

    assert oido[-1]["fase"] == "listo"


def test_engancha_las_herramientas_de_un_bus(oido: list) -> None:
    bus = EventBus()
    progreso.enganchar(bus)

    bus.publish(
        EventType.TOOL_CALL_START,
        {"tool": "file_read", "arguments": {"path": "a.py"}},
    )
    bus.publish(
        EventType.TOOL_CALL_END,
        {"tool": "file_read", "success": True, "result": "def  suma():\n  pass"},
    )

    assert [a["tipo"] for a in oido] == ["herramienta_inicio", "herramienta_fin"]
    assert oido[0]["argumentos"] == "a.py"
    assert oido[1]["ok"] and oido[1]["detalle"] == "def suma(): pass"


def test_resume_los_argumentos_por_lo_que_importa() -> None:
    assert (
        progreso.resumir_argumentos({"command": "pytest -q", "cwd": "."}) == "pytest -q"
    )
    assert progreso.resumir_argumentos({"x": 1, "y": 2}) == "x, y"
    assert progreso.resumir_argumentos("a" * 300) == "a" * progreso.RESUMEN


def test_la_bitacora_numera_y_entrega_desde() -> None:
    b = progreso.Bitacora(maximo=3)

    for i in range(5):
        b.anotar({"tipo": "fase", "i": i})

    assert b.ultimo == 5
    assert [a["n"] for a in b.desde(0)["avisos"]] == [3, 4, 5]
    assert b.desde(4) == {"avisos": [b.desde(0)["avisos"][-1]], "n": 5}

    b.limpiar()

    assert b.desde(0)["avisos"] == [] and b.ultimo == 5


# --- `hacer` lo cuenta ------------------------------------------------------------


class MotorGuionado(InferenceEngine):
    engine_id = "guionado"

    def __init__(self, turnos: list[dict[str, Any]]) -> None:
        self.turnos = list(turnos)

    def soporta_herramientas(self) -> bool:
        return True

    @property
    def modelo(self) -> str:
        return "falso"

    def generate(self, messages, *, model, temperature=0.2, max_tokens=1024, **kw):
        if not self.turnos:
            return {"content": "Listo.", "tool_calls": [], "finish_reason": "stop"}

        t = self.turnos.pop(0)

        return {
            "content": t.get("content", ""),
            "tool_calls": t.get("tool_calls", []),
            "finish_reason": "stop",
            "usage": {},
        }


def llamada(nombre: str, **args: Any) -> dict[str, Any]:
    return {"id": f"c_{nombre}", "name": nombre, "arguments": json.dumps(args)}


def test_hacer_cuenta_lo_que_hace_y_lo_que_pide(
    tmp_path: Path, monkeypatch, oido: list
) -> None:
    monkeypatch.setenv("ARCHITECT_HOME", str(tmp_path / "hogar"))
    archivo = tmp_path / "m.py"
    archivo.write_text("a = 1\n", encoding="utf-8")

    motor = MotorGuionado(
        [
            {"tool_calls": [llamada("file_read", path=str(archivo))]},
            {
                "tool_calls": [
                    llamada("file_write", path=str(archivo), content="a = 2\n")
                ]
            },
            {"content": "Propongo a = 2."},
        ]
    )

    salida = hacer.run(str(tmp_path), "cambia a por 2", si=False, motor=motor)

    tipos = [a["tipo"] for a in oido]

    assert tipos[0] == "fase" and oido[0]["fase"] == "trabajando"
    assert "herramienta_inicio" in tipos and "herramienta_fin" in tipos
    assert any(
        a["tipo"] == "permiso" and a["herramienta"] == "file_write" for a in oido
    )
    assert oido[-1] == {**oido[-1], "tipo": "fase", "fase": "permiso", "pendientes": 1}
    assert salida["pending_ids"] and len(salida["pending_ids"]) == 1
