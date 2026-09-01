"""
Repository Context.

Builds the context sent to the LLM.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any


class RepositoryContext:
    """
    Construye el contexto que recibirá el LLM.

    El objetivo es entregar únicamente la información
    necesaria para modificar un archivo sin enviar todo
    el repositorio.
    """

    def __init__(self) -> None:
        self.max_file_size = 20_000

    def build(
        self,
        repository: str | Path,
        files: Iterable[str],
    ) -> dict[str, Any]:
        root = Path(repository).resolve()

        context: dict[str, Any] = {
            "repository": str(root),
            "files": [],
        }

        context_files: list[dict[str, str]] = context["files"]

        for relative in files:
            target = root / relative

            if not target.exists():
                continue

            context_files.append(
                {
                    "path": relative,
                    "source": self._read_file(target),
                }
            )

        return context

    def build_prompt(
        self,
        repository: str | Path,
        files: Iterable[str],
    ) -> str:
        """
        Convierte el contexto en texto para el prompt.
        """

        context = self.build(
            repository,
            files,
        )

        sections: list[str] = []

        context_files: list[dict[str, str]] = context["files"]

        for item in context_files:
            sections.append(
                "\n".join(
                    [
                        "=" * 70,
                        f"FILE: {item['path']}",
                        "=" * 70,
                        item["source"],
                    ]
                )
            )

        return "\n\n".join(sections)

    def _read_file(
        self,
        path: Path,
    ) -> str:
        source = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        if len(source) <= self.max_file_size:
            return source

        return source[: self.max_file_size] + "\n\n# ... FILE TRUNCATED ..."
