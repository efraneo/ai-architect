"""
=========================================================
Pipeline
=========================================================
"""

from __future__ import annotations


class Pipeline:
    def __init__(
        self,
        context,
    ):

        self.context = context

    def run(self):

        analysis = self.context.agent.analyze()

        plan = self.context.agent.plan()

        tests = self.context.agent.run_tests()

        return {
            "analysis": analysis,
            "plan": plan,
            "tests": tests,
        }
