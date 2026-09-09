"""Los agentes del entorno (agenda, hogar, investigación, sistema): revisan la
máquina y la vida diaria, obedecen órdenes y entran en el equipo."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ai_architect import agenda
from ai_architect.agente.herramientas import equipo
from ai_architect.agents import ordenes
from ai_architect.agents.agent_manager import AgentManager
from ai_architect.canales import hogar


def test_los_cuatro_estan_en_el_manager_pero_no_en_la_inspeccion(
    tmp_path: Path,
) -> None:
    gestor = AgentManager()

    assert gestor.agenda.name.startswith("Agenda")
    assert gestor.hogar.name.startswith("Hogar")
    assert gestor.investigacion.name.startswith("Investigaci")
    assert gestor.sistema.name.startswith("Sistema")
    assert not {"agenda", "hogar", "investigacion", "sistema", "voz"} & set(
        gestor.inspect(str(tmp_path))
    )


def test_el_equipo_los_incluye_como_herramientas(tmp_path: Path) -> None:
    from ai_architect.agente import caja

    nombres = caja.nombres(caja.herramientas_para(tmp_path))

    for clave in equipo.DEL_ENTORNO:
        assert f"agente_{clave}" in nombres, clave


def test_la_herramienta_equipo_suma_a_los_del_entorno(
    tmp_path: Path, monkeypatch
) -> None:
    from unittest import mock

    with (
        mock.patch.object(AgentManager, "inspect", return_value={}),
        mock.patch.object(AgentManager, "veredicto", return_value={"approved": True}),
    ):
        resultado = equipo.EquipoTool(str(tmp_path)).execute()

    assert resultado.success
    for clave in ("agenda", "hogar", "investigacion", "sistema", "voz"):
        assert f"{clave}:" in resultado.content, clave


def test_agenda_agent_cuenta_lo_de_hoy() -> None:
    ahora = datetime.now().replace(hour=8, minute=0)
    agenda.recordar("dentista", ahora.replace(hour=16))

    informe = AgentManager().agenda.review(".")

    assert informe["hoy"] == 1 and informe["findings"][0]["issue"].startswith(
        "dentista"
    )
    assert informe["contexto"].startswith("Son las ")


def test_hogar_agent_sin_configurar_lo_pide() -> None:
    informe = AgentManager().hogar.review(".")

    assert informe["configurado"] is False
    assert "configura el hogar" in informe["findings"][0]["issue"]


def test_hogar_agent_con_casa(monkeypatch) -> None:
    monkeypatch.setenv("HOGAR_URL", "http://casa")
    monkeypatch.setenv("HOGAR_TOKEN", "t")
    monkeypatch.setattr(
        hogar,
        "dispositivos",
        lambda: [
            {
                "id": "light.sala",
                "dominio": "light",
                "nombre": "Sala",
                "estado": "on",
                "unidad": "",
            },
            {
                "id": "switch.x",
                "dominio": "switch",
                "nombre": "Bomba",
                "estado": "unavailable",
                "unidad": "",
            },
        ],
    )

    informe = AgentManager().hogar.review(".")

    assert informe["dispositivos"] == 2 and informe["encendidos"] == ["Sala"]
    assert informe["findings"][0]["issue"] == "Bomba no responde"


def test_investigacion_agent_dice_que_falta(monkeypatch) -> None:
    monkeypatch.delenv("ARCHITECT_CIUDAD", raising=False)

    informe = AgentManager().investigacion.review(".")

    tipos = {h["type"] for h in informe["findings"]}
    assert "ciudad" in tipos and "correo" in tipos


def test_sistema_agent_conoce_la_maquina(tmp_path: Path) -> None:
    informe = AgentManager().sistema.review(str(tmp_path))

    assert informe["sistema"] and informe["disco_libre_gb"] > 0
    assert "word" in informe["programas_conocidos"]


# --- las órdenes del entorno --------------------------------------------------------------


def test_ordenar_recordar_apunta_en_la_agenda(tmp_path: Path) -> None:
    salida = ordenes.ejecutar(
        "agenda", "recordar", str(tmp_path), frase="llamar a Juan en dos horas"
    )

    assert salida["ok"] and "Apuntado: llamar a Juan" in salida["hecho"]
    assert agenda.pendientes()[0]["texto"] == "llamar a Juan"
    assert ordenes.ejecutar("agenda", "que_toca", str(tmp_path))["pendientes"]
    assert (
        "1 recordatorio"
        in ordenes.ejecutar("agenda", "cancelar", str(tmp_path))["hecho"]
    )


def test_ordenar_encender_en_la_casa(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        hogar,
        "accion",
        lambda nombre, encender: {
            "ok": True,
            "dispositivo": "Luz de la sala",
            "accion": "turn_on",
        },
    )

    salida = ordenes.ejecutar(
        "hogar", "encender", str(tmp_path), dispositivo="luz de la sala"
    )

    assert salida["ok"] and salida["hecho"] == "Luz de la sala: turn_on"
    sin = ordenes.ejecutar("hogar", "estado", str(tmp_path))
    assert sin["ok"] is False and "sin configurar" in sin["hecho"]


def test_consultar_clima_y_noticias(monkeypatch, tmp_path: Path) -> None:
    from ai_architect import investigar

    monkeypatch.setattr(
        investigar,
        "clima",
        lambda lugar="": {
            "ok": True,
            "ciudad": "Bogotá",
            "temperatura": 18.0,
            "estado": "nublado",
            "lluvia_ahora": False,
            "probabilidad_lluvia_3h": 10,
        },
    )
    monkeypatch.setattr(
        investigar,
        "noticias",
        lambda tema="", cuantas=5: {
            "ok": True,
            "tema": tema,
            "titulares": [{"titulo": "Algo pasó", "fuente": ""}],
        },
    )

    assert (
        "18 grados"
        in ordenes.ejecutar("investigacion", "clima", str(tmp_path))["hecho"]
    )
    assert (
        "Algo pasó"
        in ordenes.ejecutar("investigacion", "noticias", str(tmp_path), tema="x")[
            "hecho"
        ]
    )
    assert ordenes.tareas_de("investigacion")["clima"].cambia is False


def test_consultar_abrir_programa(monkeypatch, tmp_path: Path) -> None:
    from ai_architect.commands import abrir

    monkeypatch.setattr(
        abrir,
        "abrir",
        lambda que: {"ok": True, "que": que, "explicacion": "Abriendo Word."},
    )

    salida = ordenes.ejecutar("sistema", "abrir", str(tmp_path), que="word")

    assert salida["ok"] and salida["hecho"] == "Abriendo Word."
    assert ordenes.tareas_de("sistema")["abrir"].cambia is False


def test_la_descripcion_de_consultar_lista_lo_nuevo(tmp_path: Path) -> None:
    texto = equipo.ConsultarTool(str(tmp_path)).spec.description

    assert "investigacion: clima" in texto and "sistema: abrir" in texto
    assert "hogar: estado" in texto
