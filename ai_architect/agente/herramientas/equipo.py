"""El equipo de agentes como herramientas de Architect.

Architect es quien orquesta: recibe la orden, decide a qué agente mandar cada
parte, cruza lo que le devuelven y concluye. Cada agente hace su tarea con
sus propias herramientas (ruff, mypy, git, gh, pip, osv…) sin modelo; el
modelo solo dirige. Una herramienta por agente, y una más que los corre a
todos."""

from __future__ import annotations

import json
from typing import Any

from ai_architect.agente.herramientas_base import BaseTool, ToolSpec
from ai_architect.agente.tipos import ToolResult

# clave → (atributo en AgentManager, qué hace)
EQUIPO: dict[str, tuple[str, str]] = {
    "seguridad": ("security", "secretos en el código y en el historial de git"),
    "dependencias": (
        "dependencies",
        "versiones, paquetes desactualizados y vulnerabilidades (osv.dev)",
    ),
    "errores": ("bugs", "bugs latentes: ruff (F, B) y patrones peligrosos"),
    "rendimiento": ("performance", "patrones lentos en el código"),
    "git": (
        "git",
        "estado del repositorio, commits sin subir, conflictos, cambios de hoy",
    ),
    "devops": (
        "devops",
        "Docker, CI, empaquetado y el último resultado de GitHub Actions",
    ),
    "publicacion": ("release", "changelog, versión y si está listo para publicar"),
    "licencias": ("licenses", "licencias del proyecto y de sus paquetes"),
    "metricas": ("metrics", "tamaño, lenguajes, líneas y archivos grandes"),
    "arquitectura": ("architecture", "estructura y módulos del proyecto"),
    "pruebas": ("testing", "cuántas pruebas hay y cómo se corren"),
    "calidad": ("calidad", "black, ruff, mypy, docstrings y README al día"),
    "voz": ("voz", "oído, voces, ventana, canales, Word y averías pendientes"),
    "empaquetado": ("empaquetado", "versión, spec, instalador y etiqueta"),
}


def _resumen(clave: str, informe: dict[str, Any]) -> str:
    """Los hallazgos y los datos clave de un agente, en texto para el modelo."""
    if informe.get("status") == "error":
        return f"{clave}: no pudo revisar ({informe.get('error')})"

    hallazgos = informe.get("findings") or []
    lineas = [f"{clave}: {len(hallazgos)} hallazgo(s)"]

    for h in hallazgos[:20]:
        if isinstance(h, dict):
            sitio = h.get("file") or ""

            if sitio and h.get("line"):
                sitio = f"{sitio}:{h['line']}"

            lineas.append(
                f"- [{h.get('type', '?')}] {h.get('issue', '')}"
                + (f" ({sitio})" if sitio else "")
            )
        else:
            lineas.append(f"- {h}")

    datos = {
        k: v
        for k, v in informe.items()
        if k not in ("findings", "agent", "status") and not isinstance(v, (list, dict))
    }

    if datos:
        lineas.append(
            "datos: " + json.dumps(datos, ensure_ascii=False, default=str)[:600]
        )

    return "\n".join(lineas)


class AgenteTool(BaseTool):
    """Un agente del equipo, como herramienta de solo lectura."""

    def __init__(self, clave: str, project: str) -> None:
        self._clave = clave
        self._project = project
        self.tool_id = f"agente_{clave}"

    @property
    def spec(self) -> ToolSpec:
        _, que = EQUIPO[self._clave]

        return ToolSpec(
            name=f"agente_{self._clave}",
            description=f"Agente de {self._clave}: {que}. Devuelve sus hallazgos reales sobre el repositorio.",
            parameters={"type": "object", "properties": {}},
            category="equipo",
            timeout_seconds=300,
        )

    def execute(self, **params: Any) -> ToolResult:
        from ai_architect.agents.agent_manager import AgentManager

        atributo, _ = EQUIPO[self._clave]

        try:
            agente = getattr(AgentManager(), atributo)
            informe = agente.review(self._project)

        except Exception as e:  # noqa: BLE001 - se cuenta, no se esconde
            return ToolResult(
                tool_name=self.tool_id,
                content=f"{self._clave}: falló: {e}",
                success=False,
            )

        return ToolResult(
            tool_name=self.tool_id, content=_resumen(self._clave, informe), success=True
        )


class EquipoTool(BaseTool):
    """Todos los agentes estáticos de una vez, con el veredicto."""

    tool_id = "equipo"

    def __init__(self, project: str) -> None:
        self._project = project

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="equipo",
            description=(
                "Corre a todo el equipo de agentes sobre el repositorio y devuelve el veredicto "
                "y los hallazgos de cada uno. Úsalo para una revisión completa; para un tema "
                "concreto llama al agente_<tema>."
            ),
            parameters={"type": "object", "properties": {}},
            category="equipo",
            timeout_seconds=600,
        )

    def execute(self, **params: Any) -> ToolResult:
        from ai_architect.agents.agent_manager import AgentManager

        try:
            gestor = AgentManager()
            inspeccion = gestor.inspect(self._project)
            veredicto = gestor.veredicto(inspeccion)
            inspeccion["voz"] = gestor.voz.review(self._project)

        except Exception as e:  # noqa: BLE001
            return ToolResult(
                tool_name="equipo", content=f"el equipo falló: {e}", success=False
            )

        por_clave = {atributo: clave for clave, (atributo, _) in EQUIPO.items()}
        partes = [
            "veredicto: " + json.dumps(veredicto, ensure_ascii=False, default=str)[:400]
        ]

        for atributo, informe in inspeccion.items():
            partes.append(_resumen(por_clave.get(atributo, atributo), informe))

        return ToolResult(
            tool_name="equipo", content="\n\n".join(partes)[:12000], success=True
        )


def herramientas_del_equipo(project: str) -> list[BaseTool]:
    return [EquipoTool(project), *(AgenteTool(clave, project) for clave in EQUIPO)]
