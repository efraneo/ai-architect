"""Tests for the analyze command."""

from pathlib import Path

from ai_architect.commands.analyze import run


def test_analyze_repository(tmp_path: Path) -> None:
    """Analyze must process a small Python repository."""
    source = tmp_path / "example.py"

    source.write_text(
        """
class Example:
    def hello(self) -> str:
        return "hello"
""".strip(),
        encoding="utf-8",
    )

    result = run(str(tmp_path))

    assert result["success"] is True
    assert result["repository"] == str(tmp_path.resolve())

    summary = result["summary"]

    assert summary["total_files"] == 1
    assert summary["python_files"] == 1
    assert summary["total_classes"] == 1
    assert summary["total_functions"] == 1
