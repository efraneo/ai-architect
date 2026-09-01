"""
=========================================================
Markdown ChangeLog Writer
=========================================================
"""

from __future__ import annotations

from pathlib import Path

from .models import (
    ChangeLogEntry,
)


class ChangeLogWriter:
    def write(
        self,
        entry: ChangeLogEntry,
        file: str | Path,
    ) -> None:

        file = Path(file)

        file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        lines = []

        lines.append("# ChangeLog")

        lines.append("")

        lines.append(f"## {entry.version}")

        lines.append("")

        lines.append(f"Author: {entry.author}")

        lines.append(f"Date: {entry.created_at}")

        lines.append("")

        for item in entry.changes:
            lines.append(f"- [{item.change_type}] {item.file}")

            lines.append(f"  {item.summary}")

            lines.append("")

        file.write_text(
            "\n".join(lines),
            encoding="utf-8",
        )
