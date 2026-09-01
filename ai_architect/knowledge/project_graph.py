"""
=========================================================
Project Graph
=========================================================
"""

from __future__ import annotations

from collections import defaultdict


class ProjectGraph:
    def __init__(self) -> None:

        self._graph: dict[str, set[str]] = defaultdict(set)

    def add_node(
        self,
        node: str,
    ) -> None:

        self._graph.setdefault(
            node,
            set(),
        )

    def add_edge(
        self,
        source: str,
        target: str,
    ) -> None:

        self.add_node(source)

        self.add_node(target)

        self._graph[source].add(target)

    def neighbors(
        self,
        node: str,
    ) -> list[str]:

        return sorted(
            self._graph.get(
                node,
                set(),
            )
        )

    def nodes(self) -> list[str]:

        return sorted(self._graph.keys())

    def clear(self) -> None:

        self._graph.clear()

    @property
    def total_nodes(self) -> int:

        return len(self._graph)

    @property
    def total_edges(self) -> int:

        return sum(len(edges) for edges in self._graph.values())
