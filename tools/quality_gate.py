"""Lightweight repository quality checks using only the Python standard library."""

from __future__ import annotations

import ast
import compileall
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

DEFAULT_EXCLUDES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}


@dataclass(frozen=True)
class Issue:
    path: Path
    line: int
    message: str

    def __str__(self) -> str:
        location = f"{self.path}:{self.line}" if self.line else str(self.path)
        return f"{location}: {self.message}"


def iter_python_files(root: Path, excludes: set[str]) -> Iterable[Path]:
    """Yield Python files below *root*, skipping common generated/cache folders."""
    for path in sorted(root.rglob("*.py")):
        if any(part in excludes for part in path.parts):
            continue
        yield path


def check_source_text(path: Path, max_line_length: int) -> list[Issue]:
    """Run cheap text checks that keep diffs reviewable and consistent."""
    issues: list[Issue] = []

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [Issue(path, 0, f"file is not valid UTF-8: {exc}")]

    if text and not text.endswith("\n"):
        issues.append(Issue(path, 0, "missing trailing newline"))

    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.rstrip(" \t") != line:
            issues.append(Issue(path, line_number, "trailing whitespace"))

        if "\t" in line[: len(line) - len(line.lstrip())]:
            issues.append(Issue(path, line_number, "tab indentation"))

        if (
            len(line) > max_line_length
            and "http://" not in line
            and "https://" not in line
        ):
            issues.append(
                Issue(
                    path,
                    line_number,
                    f"line too long ({len(line)} > {max_line_length})",
                )
            )

    return issues


def check_ast(path: Path) -> list[Issue]:
    """Validate source and flag mutable defaults in function signatures."""
    try:
        tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
        )
    except SyntaxError as exc:
        return [Issue(path, exc.lineno or 0, f"syntax error: {exc.msg}")]

    issues: list[Issue] = []
    mutable_nodes = (ast.Dict, ast.List, ast.Set)

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        defaults = list(node.args.defaults) + [
            default for default in node.args.kw_defaults if default is not None
        ]

        for default in defaults:
            if isinstance(default, mutable_nodes):
                issues.append(
                    Issue(
                        path,
                        getattr(
                            default,
                            "lineno",
                            getattr(node, "lineno", 0),
                        ),
                        f"mutable default argument in {node.name!r}",
                    )
                )

    return issues


def run(root: Path, max_line_length: int, excludes: set[str]) -> int:
    """Run all quality checks and return a process-style status code."""
    issues: list[Issue] = []
    files = list(iter_python_files(root, excludes))

    if not compileall.compile_dir(root, quiet=1, force=False):
        issues.append(Issue(root, 0, "bytecode compilation failed"))

    for path in files:
        issues.extend(check_source_text(path, max_line_length))
        issues.extend(check_ast(path))

    if issues:
        for issue in issues:
            print(issue)
        return 1

    return 0
