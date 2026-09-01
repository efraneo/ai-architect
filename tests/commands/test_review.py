"""Tests for the review command."""

from pathlib import Path

from ai_architect.commands.review import run


def test_review_repository(tmp_path: Path) -> None:
    """Review must return a structured repository report."""
    source = tmp_path / "example.py"

    source.write_text(
        """
def hello() -> str:
    return "hello"
""".strip(),
        encoding="utf-8",
    )

    result = run(str(tmp_path))

    assert result["success"] is True
    assert result["repository"] == str(tmp_path.resolve())

    assert "approved" in result
    assert "score" in result
    assert "total_issues" in result
    assert "statistics" in result
    assert "issues" in result

    assert isinstance(result["issues"], list)
