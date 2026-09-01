"""
=========================================================
Pipeline Builder
=========================================================
"""

from __future__ import annotations

from .workflow import Workflow


class PipelineBuilder:
    def build_default_pipeline(
        self,
    ) -> Workflow:

        workflow = Workflow("Default Pipeline")

        return workflow

    def build_release_pipeline(
        self,
    ) -> Workflow:

        workflow = Workflow("Release Pipeline")

        return workflow

    def build_hotfix_pipeline(
        self,
    ) -> Workflow:

        workflow = Workflow("Hotfix Pipeline")

        return workflow
