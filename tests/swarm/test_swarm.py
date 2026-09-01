"""``swarm/`` estaba huérfano: cuatro módulos que nadie construía.

Al medirlo salió que **paralelizar los agentes estáticos con hilos es 2,14x
más lento**. Su trabajo no está repartido, está repetido: cada uno recorría
el mismo árbol. Lo que ahí funciona es compartir el recorrido, no multiplicar
los hilos.

Donde sí ayuda es en los cinco agentes de IA, que esperan al proveedor: en
paralelo cuestan lo que la llamada más lenta.

Por eso de los cuatro módulos se conectaron dos —``TaskDispatcher`` y
``ConsensusEngine``— y se podaron ``SwarmManager`` (un tercer orquestador,
cuando ``AgentManager`` ya lo es) y ``AgentCommunication`` (una lista que
copiaba un diccionario).
"""

from __future__ import annotations

import threading
import time

from ai_architect.swarm.consensus_engine import ConsensusEngine
from ai_architect.swarm.task_dispatcher import TaskDispatcher


class AgenteFalso:
    def __init__(self, nombre: str, resultado=None, revienta: str | None = None):
        self.name = nombre
        self._resultado = resultado if resultado is not None else {"status": "OK"}
        self._revienta = revienta

    def review(self, _proyecto: str):
        if self._revienta:
            raise RuntimeError(self._revienta)

        return self._resultado


# --- El despachador ---------------------------------------------------------


def test_ejecuta_a_todos_los_agentes() -> None:
    agentes = [AgenteFalso("uno"), AgenteFalso("dos"), AgenteFalso("tres")]

    informes = TaskDispatcher().dispatch(agentes, lambda a: a.review("."))

    assert set(informes) == {"uno", "dos", "tres"}


def test_devuelve_lo_que_dijo_cada_uno() -> None:
    agentes = [
        AgenteFalso("uno", {"status": "OK", "dato": 1}),
        AgenteFalso("dos", {"status": "OK", "dato": 2}),
    ]

    informes = TaskDispatcher().dispatch(agentes, lambda a: a.review("."))

    assert informes["uno"]["dato"] == 1
    assert informes["dos"]["dato"] == 2


def test_un_agente_que_revienta_no_tumba_a_los_demas() -> None:
    agentes = [
        AgenteFalso("bueno"),
        AgenteFalso("malo", revienta="se rompió"),
        AgenteFalso("otro"),
    ]

    informes = TaskDispatcher().dispatch(agentes, lambda a: a.review("."))

    assert informes["malo"]["status"] == "error"
    assert informes["malo"]["error"] == "se rompió"
    assert informes["bueno"]["status"] == "OK"


def test_sin_agentes_no_revienta() -> None:
    """La regresión: ``ThreadPoolExecutor(max_workers=0)`` lanza ValueError."""
    assert TaskDispatcher().dispatch([], lambda a: a.review(".")) == {}


def test_el_trabajo_lo_decide_quien_despacha() -> None:
    """Los estáticos exponen ``review``; los de IA, ``run``."""
    hechos: list[str] = []

    informes = TaskDispatcher().dispatch(
        [AgenteFalso("uno")],
        lambda a: hechos.append(a.name) or {"status": "OK"},
    )

    assert hechos == ["uno"]
    assert informes["uno"]["status"] == "OK"


def test_se_puede_renombrar_cada_casilla() -> None:
    agentes = [AgenteFalso("Nombre Largo Del Agente")]

    informes = TaskDispatcher().dispatch(
        agentes,
        lambda a: a.review("."),
        nombre=lambda _a: "corto",
    )

    assert list(informes) == ["corto"]


def test_corren_de_verdad_a_la_vez() -> None:
    """El punto entero: cinco esperas simultáneas cuestan como una."""
    espera = 0.15

    class Lento(AgenteFalso):
        def review(self, _proyecto: str):
            time.sleep(espera)
            return {"status": "OK"}

    agentes = [Lento(f"a{i}") for i in range(5)]

    inicio = time.perf_counter()
    TaskDispatcher().dispatch(agentes, lambda a: a.review("."))
    duracion = time.perf_counter() - inicio

    assert duracion < espera * 3  # en serie serían 5 esperas


def test_cada_agente_corre_en_su_hilo() -> None:
    hilos: set[int] = set()
    cerrojo = threading.Lock()

    def anotar(_agente):
        with cerrojo:
            hilos.add(threading.get_ident())
        time.sleep(0.05)
        return {"status": "OK"}

    TaskDispatcher().dispatch([AgenteFalso(f"a{i}") for i in range(4)], anotar)

    assert len(hilos) > 1


# --- El consenso ------------------------------------------------------------


def test_todo_en_verde_se_aprueba() -> None:
    informes = {"uno": {"status": "OK"}, "dos": {"status": "OK"}}

    veredicto = ConsensusEngine().evaluate(informes)

    assert veredicto["approved"] is True
    assert veredicto["success"] == 2
    assert veredicto["total_agents"] == 2


def test_un_agente_caido_no_se_aprueba() -> None:
    """La regresión: solo miraba ``"FAILED"``, y los agentes de este proyecto
    reportan ``"error"``. Un agente caído contaba como éxito, así que el
    consenso aprobaba una inspección que no se había podido hacer."""
    informes = {"uno": {"status": "OK"}, "dos": {"status": "error", "error": "x"}}

    veredicto = ConsensusEngine().evaluate(informes)

    assert veredicto["approved"] is False
    assert veredicto["failures"] == 1
    assert veredicto["failed_agents"] == ["dos"]


def test_failed_en_mayusculas_tambien_cuenta() -> None:
    veredicto = ConsensusEngine().evaluate({"uno": {"status": "FAILED"}})

    assert veredicto["failures"] == 1


def test_los_avisos_se_cuentan_aparte() -> None:
    informes = {"uno": {"status": "WARNING"}, "dos": {"status": "OK"}}

    veredicto = ConsensusEngine().evaluate(informes)

    assert veredicto["warnings"] == 1
    assert veredicto["success"] == 1


def test_con_hallazgos_no_se_aprueba() -> None:
    """Un agente puede terminar bien y aun así haber encontrado algo."""
    informes = {"security": {"status": "OK", "findings": [{"issue": "clave"}]}}

    veredicto = ConsensusEngine().evaluate(informes)

    assert veredicto["approved"] is False
    assert veredicto["agents_with_findings"] == ["security"]


def test_una_lista_de_hallazgos_vacia_no_cuenta() -> None:
    informes = {"security": {"status": "OK", "findings": []}}

    assert ConsensusEngine().evaluate(informes)["approved"] is True


def test_lo_que_no_es_un_diccionario_se_ignora() -> None:
    veredicto = ConsensusEngine().evaluate({"raro": "una cadena"})

    assert veredicto["success"] == 0
    assert veredicto["total_agents"] == 1


def test_sin_informes_no_hay_nada_que_objetar() -> None:
    veredicto = ConsensusEngine().evaluate({})

    assert veredicto["approved"] is True
    assert veredicto["total_agents"] == 0
