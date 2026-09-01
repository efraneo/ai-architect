"""
Agent Manager

Central Multi-Agent Orchestrator
"""

from __future__ import annotations

from typing import Any

from ai_architect.agents.agent_context import AgentContext
from ai_architect.agents.architect_agent import ArchitectAgent
from ai_architect.agents.architecture_agent import ArchitectureAgent
from ai_architect.agents.bug_hunter_agent import BugHunterAgent
from ai_architect.agents.code_reviewer_agent import CodeReviewerAgent
from ai_architect.agents.dependency_agent import DependencyAgent
from ai_architect.agents.devops_agent import DevOpsAgent
from ai_architect.agents.documentation_agent import DocumentationAgent
from ai_architect.agents.git_agent import GitAgent
from ai_architect.agents.license_agent import LicenseAgent
from ai_architect.agents.performance_agent import PerformanceAgent
from ai_architect.agents.project_metrics_agent import ProjectMetricsAgent
from ai_architect.agents.refactor_agent import RefactorAgent
from ai_architect.agents.release_agent import ReleaseAgent
from ai_architect.agents.scope import recorrido_compartido
from ai_architect.agents.security_agent import SecurityAgent
from ai_architect.agents.test_agent import TestAgent
from ai_architect.agents.testing_agent import TestingAgent
from ai_architect.swarm.consensus_engine import ConsensusEngine
from ai_architect.swarm.task_dispatcher import TaskDispatcher


class AgentManager:
    """
    Central orchestrator of QUANT AI Architect.

    Phase 1:
        Static repository inspection

    Phase 2:
        AI analysis

    Phase 3:
        Return unified execution context
    """

    def __init__(self) -> None:
        # Static agents
        self.metrics = ProjectMetricsAgent()
        self.architecture = ArchitectureAgent()
        self.testing = TestingAgent()
        self.security = SecurityAgent()
        self.dependencies = DependencyAgent()
        self.licenses = LicenseAgent()
        self.git = GitAgent()
        self.bugs = BugHunterAgent()
        self.performance = PerformanceAgent()
        self.devops = DevOpsAgent()
        self.release = ReleaseAgent()

        # AI agents
        self.architect = ArchitectAgent()
        self.refactor = RefactorAgent()
        self.reviewer = CodeReviewerAgent()
        self.tests = TestAgent()
        self.documentation = DocumentationAgent()

        # Los cinco de IA esperan al proveedor: en paralelo cuestan lo que
        # uno. Los estáticos NO se despachan así -- se midió y sale peor.
        self.dispatcher = TaskDispatcher()

        self.consensus = ConsensusEngine()

    def inspect(
        self,
        repository: str,
    ) -> dict[str, Any]:
        """Run only the static agents: no LLM, no cost.

        ``execute()`` also runs the five AI agents, which means five provider
        calls. The improvement flow wants the cheap half -- security,
        dependencies, licences, git -- to feed the decision engine without
        making every run five times more expensive.

        One agent failing does not sink the rest: its slot carries the error
        and the others still report.
        """
        estaticos = {
            "metrics": self.metrics,
            "architecture": self.architecture,
            "testing": self.testing,
            "security": self.security,
            "dependencies": self.dependencies,
            "licenses": self.licenses,
            "git": self.git,
            "bugs": self.bugs,
            "performance": self.performance,
            "devops": self.devops,
            "release": self.release,
        }

        salida: dict[str, Any] = {}

        # Once agentes recorrían el árbol por su cuenta: seis recorridos
        # completos del mismo repositorio. Con uno compartido, 1,8x.
        with recorrido_compartido():
            for nombre, agente in estaticos.items():
                try:
                    salida[nombre] = agente.review(repository)
                except Exception as e:  # noqa: BLE001 - un agente no tumba al resto
                    salida[nombre] = {"status": "error", "error": str(e)}

        return salida

    def veredicto(self, inspeccion: dict[str, Any]) -> dict[str, Any]:
        """Once informes reducidos a una respuesta: ¿está el repositorio bien?

        Una lista de hallazgos no es una conclusión. Esto dice cuántos
        agentes corrieron, cuáles se cayeron y cuáles encontraron algo.
        """
        return self.consensus.evaluate(inspeccion)

    @staticmethod
    def findings_de(inspeccion: dict[str, Any]) -> list[str]:
        """Flatten the inspection into the findings list the engine reads.

        Each agent reports in its own shape, so what is collected is the
        common part: the ``findings`` it publishes, and the agents that came
        back in error -- which is a finding in itself.
        """
        encontrados: list[str] = []

        for nombre, datos in inspeccion.items():
            if not isinstance(datos, dict):
                continue

            if datos.get("status") == "error":
                encontrados.append(f"{nombre}: no se pudo revisar")
                continue

            for hallazgo in datos.get("findings") or []:
                if not isinstance(hallazgo, dict):
                    encontrados.append(f"{nombre}: {hallazgo}")
                    continue

                detalle = hallazgo.get("issue") or hallazgo.get("type") or "hallazgo"

                # "security: Password Assignment" on its own is not
                # actionable: without the file nobody can go and look.
                donde = hallazgo.get("file")

                if donde and hallazgo.get("line"):
                    donde = f"{donde}:{hallazgo['line']}"

                encontrados.append(
                    f"{nombre}: {detalle}" + (f" ({donde})" if donde else "")
                )

        return encontrados

    def execute(
        self,
        repository: str,
    ) -> AgentContext:
        context = AgentContext(repository)

        # -------------------------------------------------
        # STATIC ANALYSIS
        # -------------------------------------------------

        context.set(
            "metrics",
            self.metrics.review(repository),
        )

        context.set(
            "architecture",
            self.architecture.review(repository),
        )

        context.set(
            "testing",
            self.testing.review(repository),
        )

        context.set(
            "security",
            self.security.review(repository),
        )

        context.set(
            "dependencies",
            self.dependencies.review(repository),
        )

        context.set(
            "licenses",
            self.licenses.review(repository),
        )

        context.set(
            "git",
            self.git.review(repository),
        )

        context.set(
            "bugs",
            self.bugs.review(repository),
        )

        context.set(
            "performance",
            self.performance.review(repository),
        )

        context.set(
            "devops",
            self.devops.review(repository),
        )

        context.set(
            "release",
            self.release.review(repository),
        )

        # -------------------------------------------------
        # AI ANALYSIS
        # -------------------------------------------------

        # Cinco llamadas al proveedor. En serie se suman; a la vez cuestan
        # lo que la más lenta. Medido con latencia simulada: 5x.
        de_ia = {
            "architect": self.architect,
            "refactor": self.refactor,
            "review": self.reviewer,
            "tests": self.tests,
            "documentation": self.documentation,
        }

        por_agente = {agente: clave for clave, agente in de_ia.items()}

        datos = dict(context.data)  # los cinco leen la misma foto

        informes = self.dispatcher.dispatch(
            list(de_ia.values()),
            lambda agente: agente.run(datos),
            nombre=lambda agente: por_agente[agente],
        )

        for clave, informe in informes.items():
            context.set(clave, informe)

        return context

    def available_agents(self) -> list[str]:
        return [
            self.metrics.name,
            self.architecture.name,
            self.testing.name,
            self.security.name,
            self.dependencies.name,
            self.licenses.name,
            self.git.name,
            self.bugs.name,
            self.performance.name,
            self.devops.name,
            self.release.name,
            self.architect.name,
            self.refactor.name,
            self.reviewer.name,
            self.tests.name,
            self.documentation.name,
        ]

    def health(self) -> dict[str, object]:
        agents = self.available_agents()

        return {
            "agents": len(agents),
            "available": agents,
            "status": "READY",
        }

    def summary(
        self,
        context: AgentContext,
    ) -> dict:
        return context.summary()
