"""
Project Development Loop
"""

from __future__ import annotations

from ai_architect.autonomous.autonomous_engine import (
    AutonomousEngine,
)
from ai_architect.decision_engine.decision_engine import (
    DecisionEngine,
)
from ai_architect.knowledge.knowledge_engine import (
    KnowledgeEngine,
)
from ai_architect.memory.memory_engine import (
    MemoryEngine,
)
from ai_architect.memory.models import (
    ExperienceOutcome,
)
from ai_architect.swarm.swarm_manager import (
    SwarmManager,
)


class ProjectLoop:
    def __init__(self):
        self.knowledge = KnowledgeEngine()

        self.swarm = SwarmManager()

        self.decision = DecisionEngine()

        self.memory = MemoryEngine()

        self.execution = AutonomousEngine()

    def cycle(
        self,
        project: str,
        agents: list,
        tasks: list,
    ):
        knowledge = self.knowledge.build(
            project,
        )

        reports = self.swarm.execute(
            project,
            agents,
        )

        decision = self.decision.decide(
            metrics={
                "duplicates": 0,
                "oversized_files": 0,
                "complexity": 0,
                "security_findings": 0,
            },
            findings=[],
            task={
                "touches_core": False,
            },
            tests_ok=True,
        )

        results = self.execution.execute(
            tasks,
        )

        self.memory.record(
            repository=project,
            filename="",
            instruction="project development cycle",
            provider="project_loop",
            outcome=ExperienceOutcome.SUCCESS,
            confidence=float(
                decision["confidence"],
            ),
            metadata={
                "decision": decision,
                "execution_results": results,
            },
        )

        return {
            "knowledge": knowledge,
            "reports": reports,
            "decision": decision,
            "execution": results,
        }
