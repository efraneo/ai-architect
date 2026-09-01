"""
=========================================================
Swarm Manager

Coordina todos los agentes del AI Architect.
=========================================================
"""

from __future__ import annotations

from .agent_communication import AgentCommunication
from .consensus_engine import ConsensusEngine
from .task_dispatcher import TaskDispatcher


class SwarmManager:
    def __init__(self):

        self.dispatcher = TaskDispatcher()

        self.communication = AgentCommunication()

        self.consensus = ConsensusEngine()

    def execute(
        self,
        project: str,
        agents: list,
    ) -> dict:

        reports = self.dispatcher.dispatch(
            project,
            agents,
        )

        self.communication.broadcast(reports)

        decision = self.consensus.evaluate(reports)

        return {
            "reports": reports,
            "decision": decision,
        }
