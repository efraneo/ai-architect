"""
=========================================================
Context Builder
=========================================================
"""

from __future__ import annotations

from pathlib import Path


class ContextBuilder:
    def file_context(
        self,
        file: str | Path,
    ) -> str:

        return Path(file).read_text(encoding="utf-8")

    def project_context(
        self,
        files: list[str],
    ) -> str:

        context = []

        for file in files:
            context.append(f"# FILE: {file}")

            context.append("")

            context.append(Path(file).read_text(encoding="utf-8"))

            context.append("\n")

        return "\n".join(context)

    def summary(
        self,
        analysis: dict,
    ) -> str:

        lines = []

        for key, value in analysis.items():
            lines.append(f"{key}: {value}")

        return "\n".join(lines)
