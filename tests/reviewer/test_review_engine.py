from pathlib import Path

from ai_architect.reviewer.models import Severity
from ai_architect.reviewer.review_engine import ReviewEngine


def test_review_engine_reviews_python_files(
    tmp_path: Path,
) -> None:
    source = tmp_path / "sample.py"

    source.write_text(
        "def hello() -> str:\n"
        '    return "hello"\n',
        encoding="utf-8",
    )

    engine = ReviewEngine()

    report = engine.review(tmp_path)

    assert report is not None
    assert report.total_issues == 0
    assert report.score == 100.0
    assert report.approved is True


def test_review_engine_ignores_non_python_files(
    tmp_path: Path,
) -> None:
    python_file = tmp_path / "sample.py"
    text_file = tmp_path / "README.md"

    python_file.write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    text_file.write_text(
        "Documentation\n",
        encoding="utf-8",
    )

    engine = ReviewEngine()

    report = engine.review(tmp_path)

    assert report.total_issues == 0
    assert report.score == 100.0


def test_review_engine_detects_large_file(
    tmp_path: Path,
) -> None:
    source = tmp_path / "large.py"

    source.write_text(
        "\n".join(
            "value = 1"
            for _ in range(601)
        ),
        encoding="utf-8",
    )

    engine = ReviewEngine()

    report = engine.review(tmp_path)

    assert report.total_issues >= 1

    assert any(
        issue.severity == Severity.CRITICAL
        and issue.rule == "MAX_FILE_LINES"
        for issue in report.issues
    )

    assert report.approved is False


def test_review_engine_exports_json(
    tmp_path: Path,
) -> None:
    source = tmp_path / "sample.py"

    source.write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    engine = ReviewEngine()

    engine.review(tmp_path)

    target = tmp_path / ".ai_architect" / "review.json"

    assert target.exists()

    content = target.read_text(
        encoding="utf-8",
    )

    assert '"score"' in content
    assert '"approved"' in content
    assert '"total_issues"' in content


def test_review_engine_exports_markdown(
    tmp_path: Path,
) -> None:
    source = tmp_path / "sample.py"

    source.write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    engine = ReviewEngine()

    engine.review(tmp_path)

    target = tmp_path / ".ai_architect" / "review.md"

    assert target.exists()

    content = target.read_text(
        encoding="utf-8",
    )

    assert "# QUANT AI Architect Review" in content
    assert "## Summary" in content
    assert "## Issues" in content


def test_review_engine_statistics(
    tmp_path: Path,
) -> None:
    source = tmp_path / "sample.py"

    source.write_text(
        "\n".join(
            "value = 1"
            for _ in range(601)
        ),
        encoding="utf-8",
    )

    engine = ReviewEngine()

    report = engine.review(tmp_path)

    statistics = engine.statistics(report)

    assert statistics["total"] == report.total_issues
    assert statistics["critical"] >= 1
    assert statistics["score"] == report.score
    assert statistics["approved"] is False


def test_review_engine_to_dict(
    tmp_path: Path,
) -> None:
    source = tmp_path / "sample.py"

    source.write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    engine = ReviewEngine()

    report = engine.review(tmp_path)

    data = engine.to_dict(report)

    assert isinstance(data, dict)
    assert "issues" in data
    assert "score" in data
    assert "approved" in data
    assert "total_issues" in data
    assert "statistics" in data


def test_review_engine_issues_by_severity(
    tmp_path: Path,
) -> None:
    source = tmp_path / "large.py"

    source.write_text(
        "\n".join(
            "value = 1"
            for _ in range(601)
        ),
        encoding="utf-8",
    )

    engine = ReviewEngine()

    report = engine.review(tmp_path)

    critical = engine.issues_by_severity(
        report,
        Severity.CRITICAL,
    )

    assert critical
    assert all(
        issue.severity == Severity.CRITICAL
        for issue in critical
    )
