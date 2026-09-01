"""
=========================================================
Knowledge Graph

Relationship Knowledge Engine
=========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class KnowledgeNode:
    """
    One graph node.
    """

    id: str

    category: str

    label: str

    metadata: dict = field(
        default_factory=dict,
    )


@dataclass(slots=True)
class KnowledgeEdge:
    """
    Directed relation.
    """

    source: str

    target: str

    relation: str

    weight: float = 1.0

    metadata: dict = field(
        default_factory=dict,
    )


class KnowledgeGraph:
    """
    Lightweight in-memory knowledge graph.

    Version 1

        • Nodes

        • Relations

        • Neighbor lookup

    Future

        • Graph queries

        • Neo4j backend

        • RDF export

        • Reasoning
    """

    ###########################################################

    def __init__(self) -> None:

        self._nodes: dict[str, KnowledgeNode] = {}

        self._edges: list[KnowledgeEdge] = []

    ###########################################################

    def add_node(
        self,
        node: KnowledgeNode,
    ) -> None:

        self._nodes[node.id] = node

    ###########################################################

    def add_edge(
        self,
        edge: KnowledgeEdge,
    ) -> None:

        if edge.source not in self._nodes:
            raise ValueError(f"Unknown node: {edge.source}")

        if edge.target not in self._nodes:
            raise ValueError(f"Unknown node: {edge.target}")

        self._edges.append(edge)

    ###########################################################

    def node(
        self,
        node_id: str,
    ) -> KnowledgeNode | None:

        return self._nodes.get(node_id)

    ###########################################################

    def neighbors(
        self,
        node_id: str,
    ) -> list[KnowledgeNode]:

        result = []

        for edge in self._edges:
            if edge.source == node_id:
                node = self.node(edge.target)

                if node is not None:
                    result.append(node)

        return result

    ###########################################################

    def relations(
        self,
        node_id: str,
    ) -> list[KnowledgeEdge]:

        return [
            edge
            for edge in self._edges
            if edge.source == node_id or edge.target == node_id
        ]

    ###########################################################

    def has_node(
        self,
        node_id: str,
    ) -> bool:

        return node_id in self._nodes

    ###########################################################

    def node_count(
        self,
    ) -> int:

        return len(self._nodes)

    ###########################################################

    def edge_count(
        self,
    ) -> int:

        return len(self._edges)

    ###########################################################

    def clear(
        self,
    ) -> None:

        self._nodes.clear()

        self._edges.clear()
