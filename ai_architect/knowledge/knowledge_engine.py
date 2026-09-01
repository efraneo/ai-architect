"""
=========================================================
Knowledge Engine
=========================================================
"""

from __future__ import annotations

from .architecture_graph import ArchitectureGraph
from .dependency_graph import DependencyGraph
from .embeddings import Embeddings
from .file_graph import FileGraph
from .project_memory import ProjectMemory
from .semantic_search import SemanticSearch


class KnowledgeEngine:
    def __init__(self):

        self.memory = ProjectMemory()

        self.files = FileGraph()

        self.dependencies = DependencyGraph()

        self.architecture = ArchitectureGraph()

        self.semantic = SemanticSearch()

        self.embeddings = Embeddings()

    def build(
        self,
        project: str,
    ):

        knowledge = {
            "files": self.files.build(project),
            "dependencies": self.dependencies.build(project),
            "architecture": self.architecture.build(project),
        }

        self.memory.save(knowledge)

        return knowledge

    def related_files(
        self,
        project: str,
        query: str,
    ) -> list[str]:

        return self.semantic.search(
            project,
            query,
        )
