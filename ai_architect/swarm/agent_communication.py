"""
=========================================================
Agent Communication
=========================================================
"""

from __future__ import annotations


class AgentCommunication:
    def __init__(self):

        self.messages = []

    def broadcast(
        self,
        reports: dict,
    ):

        self.messages.clear()

        for agent, report in reports.items():
            self.messages.append(
                {
                    "from": agent,
                    "report": report,
                }
            )

    def history(self):

        return self.messages

    def clear(self):

        self.messages.clear()
