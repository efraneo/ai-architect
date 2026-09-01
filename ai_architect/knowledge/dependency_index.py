"""
=========================================================
Dependency Index
=========================================================
"""

from __future__ import annotations

from collections import defaultdict


class DependencyIndex:
    def __init__(self):

        self._imports = defaultdict(set)

    def add_import(
        self,
        source: str,
        imported: str,
    ) -> None:

        self._imports[source].add(imported)

    def dependencies(
        self,
        source: str,
    ) -> list[str]:

        return sorted(
            self._imports.get(
                source,
                set(),
            )
        )

    def reverse_dependencies(
        self,
        target: str,
    ) -> list[str]:

        result = []

        for source, imports in self._imports.items():
            if target in imports:
                result.append(source)

        return sorted(result)

    def clear(self):

        self._imports.clear()

    @property
    def total_modules(self):

        return len(self._imports)
