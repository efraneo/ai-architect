"""
=========================================================
Agent Registry
=========================================================
"""

from __future__ import annotations


class AgentRegistry:
    def __init__(self):

        self._agents = {}

    def register(
        self,
        agent,
    ):

        self._agents[agent.name] = agent

    def get(
        self,
        name: str,
    ):

        return self._agents.get(name)

    def all(self):

        return list(self._agents.values())

    def execute_all(
        self,
        project: str,
    ):

        reports = {}

        for agent in self.all():
            reports[agent.name] = agent.review(project)

        return reports
