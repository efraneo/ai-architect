"""`architect hacer`: una orden completa con herramientas, sin red y sin modelo real.

El motor falso devuelve, turno a turno, lo que devolvería un modelo con function calling:
primero pide leer un archivo, luego escribirlo, y al final contesta. Así se prueba la política
de permisos (sin --si se niega la escritura) y que las herramientas quedan acotadas al repo.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ai_architect.agente import caja
from ai_architect.agente.motor import InferenceEngine, MotorArquitecto
from ai_architect.commands import hacer


class MotorGuionado(InferenceEngine):
    """Devuelve las respuestas en orden; cada una puede traer tool_calls."""

    engine_id = "guionado"

    def __init__(self, turnos: list[dict[str, Any]]) -> None:
        self.turnos = list(turnos)
        self.recibido: list[list[Any]] = []

    def soporta_herramientas(self) -> bool:
        return True

    @property
    def modelo(self) -> str:
        return "falso"

    def generate(self, messages, *, model, temperature=0.2, max_tokens=1024, **kwargs):
        self.recibido.append(list(messages))
        if not self.turnos:
            return {
                "content": "Listo.",
                "tool_calls": [],
                "finish_reason": "stop",
                "usage": {},
            }
        t = self.turnos.pop(0)
        return {
            "content": t.get("content", ""),
            "tool_calls": t.get("tool_calls", []),
            "finish_reason": "stop",
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        }


def llamada(nombre: str, **args: Any) -> dict[str, Any]:
    return {"id": f"c_{nombre}", "name": nombre, "arguments": json.dumps(args)}


@pytest.fixture
def repo(tmp_path: Path, monkeypatch) -> Path:
    (tmp_path / "modulo.py").write_text(
        "def suma(a, b):\n    return a - b\n", encoding="utf-8"
    )
    from ai_architect.core import perfil

    archivo = tmp_path / "perfil.json"
    monkeypatch.setattr(perfil, "ARCHIVO", archivo)
    perfil.configurar("Eathan", archivo=archivo)
    return tmp_path


def test_sin_permiso_examina_y_propone_pero_no_escribe(repo: Path):
    motor = MotorGuionado(
        [
            {"tool_calls": [llamada("file_read", path=str(repo / "modulo.py"))]},
            {
                "tool_calls": [
                    llamada(
                        "file_write",
                        path=str(repo / "modulo.py"),
                        content="def suma(a, b):\n    return a + b\n",
                    )
                ]
            },
            {
                "content": "La resta debería ser suma; propongo cambiar `a - b` por `a + b`."
            },
        ]
    )
    salida = hacer.run(str(repo), "corrige la función suma", si=False, motor=motor)
    assert salida["success"] and not salida["executed"]
    assert "file_read" in salida["tools"] and "file_write" in salida["tools"]
    assert (repo / "modulo.py").read_text(
        encoding="utf-8"
    ) == "def suma(a, b):\n    return a - b\n"
    assert (
        "No modifiqué nada" in salida["explanation"]
        and "propongo" in salida["explanation"]
    )
    # al modelo se le dijo que sin permiso solo propone
    assert "NO tienes permiso" in str(motor.recibido[0][0].content)


def test_con_permiso_escribe_y_lo_cuenta(repo: Path):
    motor = MotorGuionado(
        [
            {
                "tool_calls": [
                    llamada(
                        "file_write",
                        path=str(repo / "modulo.py"),
                        content="def suma(a, b):\n    return a + b\n",
                    )
                ]
            },
            {"content": "Corregí modulo.py: ahora suma."},
        ]
    )
    salida = hacer.run(str(repo), "corrige la función suma", si=True, motor=motor)
    assert salida["success"] and salida["executed"]
    assert (repo / "modulo.py").read_text(
        encoding="utf-8"
    ) == "def suma(a, b):\n    return a + b\n"
    assert (
        "Corregí" in salida["explanation"] and "file_write" in salida["panel"]["cuerpo"]
    )


def test_no_lee_fuera_del_repositorio(repo: Path, tmp_path_factory):
    fuera = tmp_path_factory.mktemp("fuera") / "secreto.txt"
    fuera.write_text("no", encoding="utf-8")
    motor = MotorGuionado(
        [{"tool_calls": [llamada("file_read", path=str(fuera))]}, {"content": "hecho"}]
    )
    salida = hacer.run(str(repo), "lee eso", si=True, motor=motor)
    resultado_tool = motor.recibido[-1][-1]
    assert resultado_tool.role.value == "tool" and "no" != resultado_tool.content
    assert not any("no" == str(m.content).strip() for m in motor.recibido[-1])
    assert salida["success"]


def test_la_caja_esta_acotada_y_las_que_escriben_piden_permiso(repo: Path):
    herramientas = caja.herramientas_para(repo)
    nombres = caja.nombres(herramientas)
    assert {
        "file_read",
        "file_write",
        "apply_patch",
        "shell_exec",
        "git_status",
        "git_diff",
        "git_log",
        "git_commit",
    } <= set(nombres)
    for h in herramientas:
        assert h.spec.requires_confirmation == (h.spec.name in caja.ESCRIBEN)


def test_sin_repositorio_o_sin_orden_avisa(tmp_path: Path):
    assert not hacer.run(str(tmp_path / "no_existe"), "algo")["success"]
    assert not hacer.run(str(tmp_path), "   ")["success"]


def test_el_motor_aplana_la_conversacion_para_proveedores_de_texto():
    class Proveedor:
        def generate(self, prompt: str, **kw):
            return "respuesta: " + prompt[:20]

    motor = MotorArquitecto(Proveedor())
    assert not motor.soporta_herramientas()
    from ai_architect.agente.tipos import Message, Role

    r = motor.generate([Message(role=Role.USER, content="hola")], model="x")
    assert r["content"].startswith("respuesta: [user]") and r["tool_calls"] == []
