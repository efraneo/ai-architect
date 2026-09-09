"""
=========================================================
Hacer

Una orden completa sobre el repositorio, de punta a punta.
=========================================================

Hasta aquí Architect tenía comandos: analizar, revisar, mejorar con un parche. Esto es otra
cosa: se le da una orden en lenguaje natural —"examina el módulo de pagos, corre las pruebas,
corrige lo que falle y proponme cómo simplificarlo"— y él mismo decide qué leer, qué ejecutar
y qué cambiar, con herramientas, en varios turnos, hasta terminar y contarlo.

El bucle de agente, las herramientas de repositorio y la guardia contra bucles vienen de
OpenJarvis (Apache-2.0), fusionados en ``ai_architect.agente``.

Dos reglas, las mismas de siempre:

1. **Sin ``--si`` no escribe.** Examina, prueba en modo lectura y PROPONE los cambios como un
   parche en su informe. Cada intento de escribir se le niega y se le pide que proponga.
2. **Con ``--si`` escribe, pero deja rastro.** Cada herramienta que modifica algo queda en la
   bitácora de la respuesta, y las pruebas se corren después de cada cambio.

Y una tercera, de la fase 2: **lo que se le niega no se pierde.** Cada escritura que intentó
sin ``--si`` queda en la cola de aprobaciones (``architect pendientes``) con sus argumentos
exactos, para autorizarla después desde la consola, el rostro o el celular
(``architect aprobar --frase <id>`` o ``todo``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_architect.agente import caja, memoria, progreso
from ai_architect.agente.agente_base import AgentContext
from ai_architect.agente.eventos import Event, EventBus, EventType
from ai_architect.agente.guion import prompt_sistema
from ai_architect.agente.motor import InferenceEngine, MotorArquitecto
from ai_architect.commands import pendientes
from ai_architect.core import perfil

MAX_TURNOS = 24


def run(
    project: str,
    frase: str,
    si: bool = False,
    decir: bool = False,
    cara: bool = False,
    engine: Any = None,
    motor: InferenceEngine | None = None,
    bus: EventBus | None = None,
) -> dict[str, Any]:
    """Ejecuta la orden con el agente de herramientas y devuelve el informe.

    ``engine`` es un proveedor inyectable (como en el resto de comandos); ``motor`` permite
    inyectar directamente un ``InferenceEngine`` en las pruebas.
    """
    repositorio = Path(project).resolve()
    if not repositorio.is_dir():
        return _error(f"No existe el repositorio: {repositorio}")
    if not frase.strip():
        return _error("No dijiste qué quieres que haga.")

    motor = motor or MotorArquitecto(engine)
    bitacora: list[dict[str, Any]] = []
    bus = bus or EventBus()

    # Lo que va haciendo se cuenta en vivo (el rostro lo enseña en tarjetas).
    progreso.enganchar(bus)
    progreso.avisar("fase", fase="trabajando", orden=frase.strip()[:120])

    def confirmar(
        mensaje: str,
    ) -> bool:  # noqa: ARG001 - la política es la de la sesión, no la del mensaje
        return si

    herramientas = caja.herramientas_para(
        repositorio, con_skills=True, con_mcp=True, confirmar=confirmar, bus=bus
    )

    # Lo que quiso escribir sin permiso va a la cola, con sus argumentos exactos.
    encoladas: list[str] = []
    ids_encolados: list[str] = []

    def antes(nombre: str, argumentos: dict[str, Any]) -> bool:
        if si or nombre not in caja.ESCRIBEN:
            return True

        # Mirar no cambia nada: rg, grep, git status, pytest… pasan sin permiso.
        if nombre == "shell_exec" and caja.es_solo_lectura(
            str(argumentos.get("command", ""))
        ):
            return True
        try:
            accion = pendientes.encolar(repositorio, nombre, argumentos, frase)
            encoladas.append(f"{accion.id[:8]} · {accion.description}")
            ids_encolados.append(accion.id)
            progreso.avisar(
                "permiso",
                id=accion.id,
                herramienta=nombre,
                descripcion=accion.description,
            )
        except Exception:  # noqa: BLE001 - la cola es un extra; la negativa se mantiene
            pass
        return False

    def anotar(evento: Event) -> None:
        datos = evento.data
        if isinstance(datos, dict) and datos.get("tool"):
            bitacora.append(
                {
                    "herramienta": datos.get("tool"),
                    "ok": datos.get("success"),
                    "detalle": str(datos.get("result", ""))[:300],
                }
            )

    try:
        bus.subscribe(EventType.TOOL_CALL_END, anotar)
    except Exception:  # noqa: BLE001 - sin bitácora fina se sigue igual
        pass

    from ai_architect.agente.orquestador import OrchestratorAgent

    modo = (
        "function_calling"
        if getattr(motor, "soporta_herramientas", lambda: False)()
        else "structured"
    )
    agente = OrchestratorAgent(
        motor,
        getattr(motor, "modelo", "") or "",
        tools=herramientas,
        bus=bus,
        max_turns=MAX_TURNOS,
        mode=modo,
        system_prompt=prompt_sistema(
            repositorio, perfil.como_llamarte(), si, _memoria_segura()
        ),
        parallel_tools=False,
        interactive=True,
        confirm_callback=confirmar,
        before_tool_call=antes,
    )

    try:
        resultado = agente.run(
            frase,
            AgentContext(metadata={"repositorio": str(repositorio), "permiso": si}),
        )
    except Exception as e:  # noqa: BLE001 - el agente falla, el comando informa
        import traceback

        from ai_architect import autoreparacion

        progreso.avisar("fase", fase="error", detalle=str(e)[:120])
        averia = autoreparacion.registrar(
            "hacer", frase, str(e), traceback.format_exc()
        )
        return _error(
            f"el agente falló: {e}\n\n{autoreparacion.aviso_de_averia(averia)}"
        )

    usadas = [r.tool_name for r in resultado.tool_results]
    escrituras = [n for n in usadas if n in caja.ESCRIBEN]
    informe = (
        resultado.content or ""
    ).strip() or "Terminé, pero no tengo nada que contar."
    if not si and any(n in caja.ESCRIBEN for n in usadas):
        informe += "\n\n(No modifiqué nada: sin --si solo examino y propongo.)"
    if encoladas:
        informe += (
            f"\n\nDejé {len(encoladas)} cambio(s) en la cola de aprobaciones:\n- "
            + "\n- ".join(encoladas)
            + "\n\nPara aplicarlos: architect aprobar --frase todo (o el id de uno)."
        )

    progreso.avisar(
        "fase",
        fase="permiso" if encoladas else "listo",
        pendientes=len(encoladas),
    )

    respuesta: dict[str, Any] = {
        "success": True,
        "executed": bool(escrituras) and si,
        "command": "hacer",
        "turns": resultado.turns,
        "tools": usadas,
        "pending": encoladas,
        "pending_ids": ids_encolados,
        "written": informe,
        "explanation": informe,
        "panel": {
            "tipo": "texto",
            "titulo": "Bitácora de Architect",
            "cuerpo": _cuerpo_bitacora(resultado.tool_results, informe),
        },
    }
    if decir or cara:
        from ai_architect.commands.pide import _decir_si_toca

        return _decir_si_toca(respuesta, decir, cara)
    return respuesta


def _memoria_segura() -> str:
    try:
        return memoria.para_prompt()
    except Exception:  # noqa: BLE001 - sin memoria se trabaja igual
        return ""


def _cuerpo_bitacora(resultados: list[Any], informe: str) -> str:
    lineas = []
    for r in resultados:
        marca = "✓" if getattr(r, "success", False) else "✗"
        lineas.append(
            f"{marca} {r.tool_name}: {str(r.content)[:160].replace(chr(10), ' ')}"
        )
    return ("\n".join(lineas) + "\n\n" if lineas else "") + informe[:4000]


def _error(mensaje: str) -> dict[str, Any]:
    return {
        "success": False,
        "executed": False,
        "command": "hacer",
        "error": mensaje,
        "explanation": mensaje,
    }
