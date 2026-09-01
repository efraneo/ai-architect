from pathlib import Path

from ai_architect.reviewer.code_reviewer import CodeReviewer
from ai_architect.reviewer.models import (
    ReviewIssue,
    ReviewReport,
    Severity,
)
from ai_architect.reviewer.review_engine import ReviewEngine
from ai_architect.reviewer.review_report import ReviewReportFormatter


def test_reviewer_components_exist() -> None:
    assert ReviewEngine is not None
    assert CodeReviewer is not None
    assert ReviewIssue is not None
    assert ReviewReport is not None
    assert Severity is not None
    assert ReviewReportFormatter is not None


def test_review_engine_exposes_public_components() -> None:
    engine = ReviewEngine()

    assert hasattr(engine, "loader")
    assert hasattr(engine, "reviewer")
    assert hasattr(engine, "formatter")


def test_review_engine_exposes_review_helpers() -> None:
    engine = ReviewEngine()

    assert callable(engine.review)
    assert callable(engine.statistics)
    assert callable(engine.to_dict)
    assert callable(engine.issues_by_severity)


def test_review_engine_core_size_is_reasonable() -> None:
    path = Path(__file__).parents[2] / "ai_architect" / "reviewer" / "review_engine.py"

    assert path.exists()
    assert (
        len(
            path.read_text(
                encoding="utf-8",
            ).splitlines()
        )
        < 400
    )


def test_review_report_formatter_formats_report() -> None:
    formatter = ReviewReportFormatter()

    report = ReviewReport()

    output = formatter.format(report)

    assert isinstance(output, str)
    assert "AI ARCHITECT REVIEW REPORT" in output
    assert "Score" in output
    assert "Issues" in output
    assert "Approved" in output
