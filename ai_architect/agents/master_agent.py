"""
=========================================================
Master Agent

Coordina todos los agentes especializados.
=========================================================
"""

from __future__ import annotations

from ai_architect.agents.backend_agent import BackendAgent
from ai_architect.agents.code_quality_agent import CodeQualityAgent
from ai_architect.agents.devops_agent import DevOpsAgent
from ai_architect.agents.documentation_agent import DocumentationAgent
from ai_architect.agents.project_manager_agent import ProjectManagerAgent
from ai_architect.agents.security_agent import SecurityAgent


class MasterAgent:
    def __init__(self):

        self.manager = ProjectManagerAgent()

        self.backend = BackendAgent()

        self.quality = CodeQualityAgent()

        self.security = SecurityAgent()

        self.devops = DevOpsAgent()

        self.documentation = DocumentationAgent()

    def execute(
        self,
        project: str,
    ) -> dict:

        roadmap = self.manager.plan(project)

        backend = self.backend.review(project)

        quality = self.quality.review(project)

        security = self.security.review(project)

        infrastructure = self.devops.review(project)

        docs = self.documentation.review(project)

        return {
            "roadmap": roadmap,
            "backend": backend,
            "quality": quality,
            "security": security,
            "devops": infrastructure,
            "documentation": docs,
        }
