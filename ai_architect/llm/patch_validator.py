"""
=========================================================
Patch Validator

Validates AI-generated source code before applying it.
=========================================================
"""

from __future__ import annotations

import ast
from pathlib import Path


class PatchValidator:
    """
    Performs lightweight validation of AI generated code
    before it is accepted by the Smart Editor.
    """

    def __init__(self) -> None:

        self.min_size = 20

    def validate(
        self,
        filename: str | Path,
    ) -> bool:

        path = Path(filename)

        if not path.exists():
            return False

        try:
            source = path.read_text(
                encoding="utf-8",
            )

        except Exception:
            return False

        if not self._basic_validation(source):
            return False

        if not self._syntax_validation(source):
            return False

        return True

    def validate_source(
        self,
        source: str,
    ) -> tuple[bool, list[str]]:

        issues: list[str] = []

        if not self._basic_validation(source):
            issues.append("Generated source is empty.")

        if not self._syntax_validation(source):
            issues.append("Generated source contains syntax errors.")

        return (
            len(issues) == 0,
            issues,
        )

    def _basic_validation(
        self,
        source: str,
    ) -> bool:

        if source is None:
            return False

        if not source.strip():
            return False

        if len(source.strip()) < self.min_size:
            return False

        return True

    @staticmethod
    def _syntax_validation(
        source: str,
    ) -> bool:

        try:
            ast.parse(source)

            return True

        except SyntaxError:
            return False

        except Exception:
            return False

    @staticmethod
    def file_changed(
        original: str,
        modified: str,
    ) -> bool:

        return original != modified

    @staticmethod
    def contains_merge_markers(
        source: str,
    ) -> bool:

        markers = (
            "<<<<<<<",
            "=======",
            ">>>>>>>",
        )

        return any(marker in source for marker in markers)
