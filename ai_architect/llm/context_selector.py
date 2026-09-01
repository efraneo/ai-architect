"""
=========================================================
Context Selector

Intelligent Repository Context Selection
=========================================================
"""

from __future__ import annotations

from pathlib import Path


class ContextSelector:
    """
    Selects the minimum repository context required
    for the LLM to perform a modification.
    """

    SUPPORTED_EXTENSIONS = {
        ".py",
        ".md",
        ".toml",
        ".yaml",
        ".yml",
        ".json",
    }

    def __init__(self) -> None:

        self.max_context_files = 8

    def select(
        self,
        repository: str | Path,
        target: str,
    ) -> list[str]:

        repository = Path(repository)

        target_path = repository / target

        if not target_path.exists():
            return [target]

        selected: list[str] = [target]

        parent = target_path.parent

        for file in sorted(parent.iterdir()):
            if len(selected) >= self.max_context_files:
                break

            if not file.is_file():
                continue

            if file == target_path:
                continue

            if file.suffix not in self.SUPPORTED_EXTENSIONS:
                continue

            selected.append(str(file.relative_to(repository)))

        return selected

    def expand_with_parents(
        self,
        repository: str | Path,
        files: list[str],
    ) -> list[str]:

        repository = Path(repository)

        result: list[str] = []

        seen = set()

        for file in files:
            if file not in seen:
                result.append(file)

                seen.add(file)

            parent = (repository / file).parent

            init = parent / "__init__.py"

            if init.exists():
                relative = str(init.relative_to(repository))

                if relative not in seen:
                    result.append(relative)

                    seen.add(relative)

        return result

    def build(
        self,
        repository: str | Path,
        target: str,
    ) -> list[str]:

        files = self.select(
            repository,
            target,
        )

        return self.expand_with_parents(
            repository,
            files,
        )
