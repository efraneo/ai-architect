"""Fase 2 de la fusión: memoria de hechos, skills en carpeta, MCP y cola de aprobaciones.

Todo corre sin red y sin modelo real. ``ARCHITECT_HOME`` apunta a una carpeta temporal para
que ni la memoria ni la cola toquen la de verdad.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ai_architect.agente import caja, mcp, memoria, skills
from ai_architect.agente.motor import InferenceEngine
from ai_architect.commands import hacer, pendientes, respuestas
from ai_architect.commands import memoria as cmd_memoria


@pytest.fixture(autouse=True)
def casa(tmp_path: Path, monkeypatch) -> Path:
    hogar = tmp_path / "hogar"
    monkeypatch.setenv("ARCHITECT_HOME", str(hogar))
    from ai_architect.core import perfil

    archivo = tmp_path / "perfil.json"
    monkeypatch.setattr(perfil, "ARCHIVO", archivo)
    perfil.configurar("Efraín", archivo=archivo)
    return hogar


class MotorGuionado(InferenceEngine):
    engine_id = "guionado"

    def __init__(self, turnos: list[dict[str, Any]]) -> None:
        self.turnos = list(turnos)
        self.recibido: list[list[Any]] = []

    def soporta_herramientas(self) -> bool:
        return True

    @property
    def modelo(self) -> str:
        return "falso"

    def generate(self, messages, *, model, temperature=0.2, max_tokens=1024, **kw):
        self.recibido.append(list(messages))
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


# --- memoria -----------------------------------------------------------------


def test_recuerda_lista_y_olvida(casa: Path):
    assert memoria.hechos() == []
    assert memoria.recordar("trabajo en Xentris Tech")
    assert memoria.recordar("prefiero pytest a unittest")
    assert not memoria.recordar("   ")
    textos = [h.text for h in memoria.hechos()]
    assert textos == ["trabajo en Xentris Tech", "prefiero pytest a unittest"]
    assert memoria.ruta().is_file() and str(casa) in str(memoria.ruta())
    bloque = memoria.para_prompt()
    assert "memoria a largo plazo" in bloque and "Xentris" in bloque
    assert (
        memoria.olvidar() == 2
        and memoria.hechos() == []
        and memoria.para_prompt() == ""
    )


def test_el_comando_memoria_entiende_recuerda_que_y_olvida_todo():
    salida = cmd_memoria.run("recuerda que mi bot se llama Efra_BOT")
    assert salida["success"] and "Efra_BOT" in salida["explanation"]
    assert cmd_memoria.run("")["facts"] == ["mi bot se llama Efra_BOT"]
    assert "olvidé 1" in cmd_memoria.run("olvida todo")["explanation"]
    assert cmd_memoria.run("")["facts"] == []


def test_recuerda_que_se_resuelve_sin_modelo_en_respuestas():
    rapida = respuestas.responder("Recuerda que mi empresa es Xentris")
    assert rapida is not None and "Xentris" in rapida["respuesta"]
    assert [h.text for h in memoria.hechos()] == ["mi empresa es Xentris"]
    lista = respuestas.responder("¿qué sabes de mí?")
    assert lista is not None and "Xentris" in lista["respuesta"]
    assert respuestas.responder("revisa el proyecto") is None


def test_aprende_sola_de_la_charla_con_el_extractor():
    motor = MotorGuionado(
        [{"content": '["El usuario se llama Efraín", "Usa Windows 11"]'}]
    )
    memoria.aprender_de(
        "hola, soy Efraín y uso Windows 11", "Encantado.", motor, en_hilo=False
    )
    hechos = memoria.hechos()
    assert {h.text for h in hechos} == {"El usuario se llama Efraín", "Usa Windows 11"}
    assert all(h.trust == "auto" for h in hechos)
    # repetir no duplica
    motor2 = MotorGuionado([{"content": '["Usa Windows 11"]'}])
    memoria.aprender_de("uso windows", "", motor2, en_hilo=False)
    assert len(memoria.hechos()) == 2


def test_auto_activa_respeta_pruebas_y_entorno(monkeypatch):
    assert not memoria.auto_activa(object())
    assert memoria.auto_activa(None)
    monkeypatch.setenv("ARCHITECT_MEMORIA_AUTO", "0")
    assert not memoria.auto_activa(None)


def test_la_memoria_entra_en_el_prompt_de_hacer(tmp_path: Path):
    memoria.recordar("prefiero respuestas cortas")
    motor = MotorGuionado([{"content": "hecho"}])
    salida = hacer.run(str(tmp_path), "di hola", si=False, motor=motor)
    assert salida["success"]
    assert "prefiero respuestas cortas" in str(motor.recibido[0][0].content)


# --- skills --------------------------------------------------------------------


def _skill(carpeta: Path, nombre: str) -> None:
    (carpeta / nombre).mkdir(parents=True)
    (carpeta / nombre / "skill.toml").write_text(
        f"""[skill]
name = "{nombre}"
description = "lee un archivo y lo resume"
version = "0.1.0"

[[skill.steps]]
tool_name = "file_read"
arguments_template = '{{"path": "{{ruta}}"}}'
output_key = "contenido"
""",
        encoding="utf-8",
    )


def test_descubre_skills_del_proyecto_y_globales(tmp_path: Path, casa: Path):
    repo = tmp_path / "repo"
    _skill(repo / ".architect" / "skills", "resumir")
    _skill(casa / "skills", "global-lint")
    gestor = skills.gestor_para(repo)
    assert set(gestor.skill_names()) == {"resumir", "global-lint"}
    herramientas = caja.herramientas_para(repo, con_skills=True)
    nombres = caja.nombres(herramientas)
    assert "skill_resumir" in nombres and "skill_global-lint" in nombres
    assert "file_write" in nombres  # la caja base sigue ahí


def test_sin_skills_la_caja_es_la_de_siempre(tmp_path: Path):
    base = caja.nombres(caja.herramientas_para(tmp_path))
    con = caja.nombres(caja.herramientas_para(tmp_path, con_skills=True, con_mcp=True))
    assert base == con


def test_el_comando_skills_lista(tmp_path: Path):
    from ai_architect.commands import skills as cmd_skills

    _skill(tmp_path / ".architect" / "skills", "resumir")
    salida = cmd_skills.run(str(tmp_path))
    assert salida["success"] and salida["skills"][0]["nombre"] == "resumir"
    assert "resumir" in salida["explanation"]


# --- MCP -----------------------------------------------------------------------


def test_mcp_sin_config_no_hace_nada(casa: Path):
    assert mcp.servidores_configurados() == []
    assert mcp.herramientas_mcp() == ([], [])
    from ai_architect.commands import mcp as cmd_mcp

    salida = cmd_mcp.run()
    assert salida["success"] and "No hay servidores" in salida["explanation"]


def test_mcp_lee_la_lista_de_servidores(casa: Path):
    casa.mkdir(parents=True, exist_ok=True)
    mcp.ruta_config().write_text(
        json.dumps({"servers": [{"name": "uno", "url": "http://127.0.0.1:9/mcp"}]}),
        encoding="utf-8",
    )
    assert [s["name"] for s in mcp.servidores_configurados()] == ["uno"]
    # un servidor que no responde no revienta: se ignora
    herramientas, clientes = mcp.herramientas_mcp()
    assert herramientas == [] and clientes == []


# --- aprobaciones --------------------------------------------------------------


def test_sin_permiso_lo_que_quiso_escribir_queda_en_cola(tmp_path: Path):
    archivo = tmp_path / "modulo.py"
    archivo.write_text("a = 1\n", encoding="utf-8")
    motor = MotorGuionado(
        [
            {
                "tool_calls": [
                    llamada("file_write", path=str(archivo), content="a = 2\n")
                ]
            },
            {"content": "Propongo cambiar a = 1 por a = 2."},
        ]
    )
    salida = hacer.run(str(tmp_path), "cambia a por 2", si=False, motor=motor)
    assert salida["success"] and not salida["executed"]
    assert archivo.read_text(encoding="utf-8") == "a = 1\n"
    assert (
        len(salida["pending"]) == 1 and "cola de aprobaciones" in salida["explanation"]
    )

    lista = pendientes.run("listar")
    assert len(lista["pending"]) == 1
    accion = lista["pending"][0]
    assert accion["payload"]["herramienta"] == "file_write"
    assert accion["payload"]["repositorio"] == str(tmp_path.resolve())

    aprobado = pendientes.run("aprobar", accion["id"][:8])
    assert aprobado["success"] and aprobado["executed"]
    assert archivo.read_text(encoding="utf-8") == "a = 2\n"
    assert pendientes.run("listar")["pending"] == []


def test_aprobar_todo_y_rechazar(tmp_path: Path):
    a = pendientes.encolar(
        tmp_path,
        "file_write",
        {"path": str(tmp_path / "x.txt"), "content": "x"},
        "orden",
    )
    b = pendientes.encolar(
        tmp_path,
        "file_write",
        {"path": str(tmp_path / "y.txt"), "content": "y"},
        "orden",
    )
    assert not pendientes.run("aprobar", "zzzz")["success"]
    assert pendientes.run("rechazar", b.id[:8])["success"]
    assert [p["id"] for p in pendientes.run("listar")["pending"]] == [a.id]
    todo = pendientes.run("aprobar", "todo")
    assert todo["success"] and (tmp_path / "x.txt").read_text(encoding="utf-8") == "x"
    assert not (tmp_path / "y.txt").exists()
    assert pendientes.run("listar")["pending"] == []


def test_con_permiso_no_encola_nada(tmp_path: Path):
    archivo = tmp_path / "m.py"
    archivo.write_text("a = 1\n", encoding="utf-8")
    motor = MotorGuionado(
        [
            {
                "tool_calls": [
                    llamada("file_write", path=str(archivo), content="a = 2\n")
                ]
            },
            {"content": "Hecho."},
        ]
    )
    salida = hacer.run(str(tmp_path), "cambia", si=True, motor=motor)
    assert salida["executed"] and salida["pending"] == []
    assert pendientes.run("listar")["pending"] == []


def test_lo_trivial_no_entra_en_la_memoria():
    """En la primera prueba real solo aprendió «el usuario habla español», dos veces."""
    motor = MotorGuionado(
        [
            {
                "content": '["El usuario se comunica en español", "Trabaja en Xentris Tech"]'
            }
        ]
    )
    memoria.aprender_de("hola", "Hola.", motor, en_hilo=False)
    assert [h.text for h in memoria.hechos()] == ["Trabaja en Xentris Tech"]
    # y el extractor recibe el guion en español, no el de OpenJarvis
    assert "DURABLES" in str(motor.recibido[0][0].content)


def test_guarda_en_tu_memoria_que_va_a_la_memoria():
    """En la prueba real se fue al especialista de seguridad."""
    from ai_architect.commands import respuestas

    salida = respuestas.responder(
        "Guarda en tu memoria que no me debes decir qué malo tienes"
    )
    assert salida is not None and "Apuntado" in salida["respuesta"]
    assert [h.text for h in memoria.hechos()] == ["no me debes decir qué malo tienes"]
