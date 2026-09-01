"""
=========================================================
Development Engine

Main autonomous loop
=========================================================
"""

from __future__ import annotations

from ai_architect.agents.master_agent import (
    MasterAgent,
)

from .improvement_cycle import (
    ImprovementCycle,
)
from .project_loop import (
    ProjectLoop,
)


class DevelopmentEngine:
    def __init__(self):

        self.master = MasterAgent()

        self.cycle = ImprovementCycle()

        self.loop = ProjectLoop()

    def execute(
        self,
        project: str,
    ):

        reports = self.master.execute(project)

        tasks = self.cycle.create_tasks(reports)

        agents = [
            self.master.backend,
            self.master.quality,
            self.master.security,
            self.master.devops,
            self.master.documentation,
        ]

        return self.loop.cycle(
            project,
            agents,
            tasks,
        )
