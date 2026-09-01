"""
=========================================================
Knowledge Updater
=========================================================
"""

from __future__ import annotations

from ai_architect.knowledge.knowledge_engine import (
    KnowledgeEngine,
)


class KnowledgeUpdater:
    def __init__(self):

        self.engine = KnowledgeEngine()

    def update(
        self,
        project: str,
    ):

        return self.engine.build(project)
