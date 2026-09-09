"""La biblioteca como herramientas de Architect.

Cientos de habilidades y decenas de especialistas no caben en la caja como
una herramienta cada uno. Entran por cuatro puertas:

- ``buscar_habilidad(tema)``: qué hay para un tema (habilidades, especialistas,
  reglas, recetas), con nombre y descripción.
- ``usar_habilidad(nombre)``: el contenido de una habilidad, para seguirlo.
- ``anexo_habilidad(nombre, archivo)``: un archivo de apoyo de la habilidad.
- ``especialista(nombre, tarea)``: delega la tarea a un especialista, que la
  hace con sus propias herramientas (solo lectura del repositorio) y devuelve
  su informe. Architect sigue siendo quien reparte y concluye.
"""

from __future__ import annotations

from typing import Any

from ai_architect.agente.herramientas_base import BaseTool, ToolSpec
from ai_architect.agente.tipos import ToolResult

MAX_TURNOS_ESPECIALISTA = 12
MAX_CARACTERES = 14000


class BuscarHabilidadTool(BaseTool):
    tool_id = "buscar_habilidad"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="buscar_habilidad",
            description=(
                "Busca en la biblioteca de Architect (cientos de habilidades, decenas de "
                "especialistas, reglas por lenguaje y recetas) lo que sirva para un tema: "
                "«seguridad django», «pruebas e2e», «rendimiento react». Devuelve nombres y "
                "descripciones; luego usa usar_habilidad o especialista."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "tema": {"type": "string"},
                    "tipo": {
                        "type": "string",
                        "enum": [
                            "",
                            "habilidades",
                            "especialistas",
                            "reglas",
                            "recetas",
                        ],
                    },
                },
                "required": ["tema"],
            },
            category="biblioteca",
        )

    def execute(self, **params: Any) -> ToolResult:
        from ai_architect import biblioteca

        if not biblioteca.instalada():
            return ToolResult(
                tool_name=self.tool_id,
                content="La biblioteca no está instalada: ordena biblioteca.instalar.",
                success=False,
            )

        tema = str(params.get("tema", ""))
        encontrados = biblioteca.buscar(tema, str(params.get("tipo", "") or ""), 10)

        if not encontrados:
            return ToolResult(
                tool_name=self.tool_id,
                content=f"Nada en la biblioteca para «{tema}».",
                success=True,
            )

        lineas = [
            f"- [{e['tipo']}] {e['nombre']}: {e.get('descripcion', '')[:160]}"
            for e in encontrados
        ]

        return ToolResult(
            tool_name=self.tool_id, content="\n".join(lineas), success=True
        )


class UsarHabilidadTool(BaseTool):
    tool_id = "usar_habilidad"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="usar_habilidad",
            description=(
                "Trae el contenido de una habilidad de la biblioteca (pasos, listas de "
                "comprobación, patrones) para seguirlo en la tarea actual. Nombre exacto, "
                "como lo devolvió buscar_habilidad."
            ),
            parameters={
                "type": "object",
                "properties": {"nombre": {"type": "string"}},
                "required": ["nombre"],
            },
            category="biblioteca",
        )

    def execute(self, **params: Any) -> ToolResult:
        from ai_architect import biblioteca

        nombre = str(params.get("nombre", ""))
        h = biblioteca.habilidad(nombre)

        if h is None:
            parecidos = ", ".join(
                e["nombre"] for e in biblioteca.buscar(nombre, "habilidades", 5)
            )

            return ToolResult(
                tool_name=self.tool_id,
                content=f"No hay una habilidad «{nombre}»."
                + (f" Parecidas: {parecidos}" if parecidos else ""),
                success=False,
            )

        texto = f"# Habilidad {h['nombre']}\n\n{h['contenido']}"

        if h["anexos"]:
            texto += "\n\nAnexos (anexo_habilidad): " + ", ".join(h["anexos"][:15])

        return ToolResult(
            tool_name=self.tool_id, content=texto[:MAX_CARACTERES], success=True
        )


class AnexoHabilidadTool(BaseTool):
    tool_id = "anexo_habilidad"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="anexo_habilidad",
            description="Un archivo de apoyo de una habilidad (referencias, ejemplos, plantillas).",
            parameters={
                "type": "object",
                "properties": {
                    "nombre": {"type": "string"},
                    "archivo": {"type": "string"},
                },
                "required": ["nombre", "archivo"],
            },
            category="biblioteca",
        )

    def execute(self, **params: Any) -> ToolResult:
        from ai_architect import biblioteca

        texto = biblioteca.anexo(
            str(params.get("nombre", "")), str(params.get("archivo", ""))
        )

        if not texto:
            return ToolResult(
                tool_name=self.tool_id, content="No existe ese anexo.", success=False
            )

        return ToolResult(
            tool_name=self.tool_id, content=texto[:MAX_CARACTERES], success=True
        )


class EspecialistaTool(BaseTool):
    """Delega en un especialista de la biblioteca: un agente con su guion y sus
    herramientas de lectura sobre el repositorio."""

    tool_id = "especialista"

    def __init__(self, project: str, motor: Any = None, bus: Any = None) -> None:
        self._project = project
        self._motor = motor
        self._bus = bus

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="especialista",
            description=(
                "Delega una tarea a un especialista de la biblioteca (security-reviewer, "
                "python-reviewer, performance-optimizer, planner, tdd-guide, silent-failure-hunter, "
                "database-reviewer…; búscalos con buscar_habilidad tipo=especialistas). Él lee el "
                "repositorio con sus herramientas y devuelve su informe; tú decides qué hacer con él."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "nombre": {"type": "string"},
                    "tarea": {"type": "string"},
                },
                "required": ["nombre", "tarea"],
            },
            category="biblioteca",
            timeout_seconds=600,
        )

    def execute(self, **params: Any) -> ToolResult:
        from ai_architect import biblioteca

        nombre = str(params.get("nombre", ""))
        tarea = str(params.get("tarea", ""))
        persona = biblioteca.especialista(nombre)

        if persona is None:
            parecidos = ", ".join(
                e["nombre"] for e in biblioteca.buscar(nombre, "especialistas", 5)
            )

            return ToolResult(
                tool_name=self.tool_id,
                content=f"No hay un especialista «{nombre}»."
                + (f" Parecidos: {parecidos}" if parecidos else ""),
                success=False,
            )

        try:
            informe = consultar_especialista(
                persona, tarea, self._project, self._motor, self._bus
            )

        except Exception as e:  # noqa: BLE001 - el especialista falló; se cuenta
            return ToolResult(
                tool_name=self.tool_id,
                content=f"{persona['nombre']} falló: {e}",
                success=False,
            )

        return ToolResult(
            tool_name=self.tool_id,
            content=f"Informe de {persona['nombre']}:\n\n{informe}"[:MAX_CARACTERES],
            success=True,
        )


def guion_de(persona: dict[str, Any], project: str) -> str:
    """El guion del especialista, con lo que necesita saber de aquí."""
    return (
        f"Eres {persona['nombre']}, un especialista al servicio de Architect. "
        f"Trabajas sobre el repositorio {project} con herramientas de lectura "
        "(leer archivos, buscar, git status/diff/log, comandos de consola que no cambian nada). "
        "No modificas archivos: informas. Responde en español, concreto, con rutas y líneas.\n\n"
        + str(persona["guion"])
    )


def consultar_especialista(
    persona: dict[str, Any],
    tarea: str,
    project: str,
    motor: Any = None,
    bus: Any = None,
) -> str:
    """Un agente aparte con el guion del especialista y herramientas de solo lectura."""
    from pathlib import Path

    from ai_architect.agente.agente_base import AgentContext
    from ai_architect.agente.orquestador import OrchestratorAgent

    if motor is None:
        from ai_architect.agente.motor import MotorArquitecto

        motor = MotorArquitecto()

    herramientas = herramientas_de_lectura(Path(project))
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
        max_turns=MAX_TURNOS_ESPECIALISTA,
        mode=modo,
        system_prompt=guion_de(persona, project),
        parallel_tools=False,
        interactive=False,
    )
    resultado = agente.run(tarea, AgentContext(metadata={"repositorio": project}))

    return str(resultado.content or "").strip() or "(sin informe)"


def herramientas_de_lectura(raiz: Any) -> list[BaseTool]:
    """La caja de un especialista: leer, buscar y git, nada que escriba."""
    from ai_architect.agente import caja

    todas = caja.herramientas_para(raiz, con_skills=False, con_mcp=False)

    return [
        h
        for h in todas
        if h.spec.name not in caja.ESCRIBEN
        and not h.spec.name.startswith(("agente_", "instalar"))
        and h.spec.name not in ("equipo", "ordenar", "consultar", "especialista")
    ]


def herramientas_de_biblioteca(
    project: str, motor: Any = None, bus: Any = None
) -> list[BaseTool]:
    return [
        BuscarHabilidadTool(),
        UsarHabilidadTool(),
        AnexoHabilidadTool(),
        EspecialistaTool(project, motor, bus),
    ]


def resumen_para_guion() -> str:
    """Una línea para el guion: cuánto hay en la biblioteca."""
    from ai_architect import biblioteca

    if not biblioteca.instalada():
        return ""

    c = biblioteca.cuenta()

    return (
        f"Tienes una BIBLIOTECA con {c.get('habilidades', 0)} habilidades, "
        f"{c.get('especialistas', 0)} especialistas, {c.get('reglas', 0)} reglas y "
        f"{c.get('recetas', 0)} recetas: búscalas con `buscar_habilidad`, sigue una con "
        "`usar_habilidad` y delega en un `especialista` cuando el tema lo pida (seguridad, "
        "rendimiento, pruebas, un lenguaje concreto)."
    )
