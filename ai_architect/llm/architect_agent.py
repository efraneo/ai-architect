"""
=========================================================
Architect Agent

Senior AI Engineer
=========================================================
"""

from __future__ import annotations

from .patch_agent import PatchAgent
from .planner_agent import PlannerAgent
from .refactor_agent import RefactorAgent
from .reviewer_agent import ReviewerAgent
from .test_agent import TestAgent


class ArchitectAgent:
    def __init__(self):

        self.planner = PlannerAgent()

        self.reviewer = ReviewerAgent()

        self.refactor = RefactorAgent()

        self.patch = PatchAgent()

        self.tests = TestAgent()

    def execute(
        self,
        file: str,
        analysis: dict,
    ) -> dict:

        review = self.reviewer.review_file(file)

        plan = self.planner.create_plan(analysis)

        refactor = self.refactor.refactor_file(file)

        patch = self.patch.generate_patch(file)

        tests = self.tests.generate_tests(refactor)

        return {
            "review": review,
            "plan": plan,
            "refactor": refactor,
            "patch": patch,
            "tests": tests,
        }
