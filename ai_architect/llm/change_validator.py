"""
=========================================================
Change Validator

Quality Gate for AI Generated Code
=========================================================
"""

from __future__ import annotations

import ast
from pathlib import Path


class ChangeValidator:
    """
    Performs structural validation over generated code.

    This validator is intentionally lightweight.
    More advanced validation (ruff, mypy, pytest,
    coverage, architecture rules, etc.) will be
    integrated in later pipeline stages.
    """

    def __init__(self) -> None:

        self.max_file_size = 250_000

    def validate(
        self,
        filename: str | Path,
    ) -> tuple[bool, list[str]]:

        path = Path(filename)

        issues: list[str] = []

        if not path.exists():
            return False, [f"{path} does not exist."]

        source = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        issues.extend(self.validate_source(source))

        return (
            len(issues) == 0,
            issues,
        )

    def validate_source(
        self,
        source: str,
    ) -> list[str]:

        issues: list[str] = []

        if not source.strip():
            issues.append("Empty source code.")

            return issues

        if len(source) > self.max_file_size:
            issues.append("File exceeds maximum supported size.")

        try:
            tree = ast.parse(source)

        except SyntaxError as exc:
            issues.append(f"SyntaxError: {exc}")

            return issues

        imports = 0

        functions = 0

        classes = 0

        for node in ast.walk(tree):
            if isinstance(
                node,
                (
                    ast.Import,
                    ast.ImportFrom,
                ),
            ):
                imports += 1

            elif isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            ):
                functions += 1

            elif isinstance(
                node,
                ast.ClassDef,
            ):
                classes += 1

        if imports == 0:
            issues.append("No imports detected.")

        if functions == 0 and classes == 0:
            issues.append("No classes or functions detected.")

        if "<<<<<<<" in source:
            issues.append("Git conflict marker detected.")

        if ">>>>>>>" in source:
            issues.append("Git conflict marker detected.")

        if "\t" in source:
            issues.append("Tab indentation detected.")

        return issues

    def compare(
        self,
        original: str,
        modified: str,
    ) -> dict:

        return {
            "changed": original != modified,
            "original_lines": len(original.splitlines()),
            "modified_lines": len(modified.splitlines()),
        }
