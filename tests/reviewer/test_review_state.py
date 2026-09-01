from ai_architect.reviewer.models import (
    ReviewIssue,
    ReviewReport,
    Severity,
)
from ai_architect.reviewer.review_state import ReviewStateMixin


class ReviewStateHarness(ReviewStateMixin):
    def __init__(self):
        self.reviewed_files = 0
        self.last_report = None
        self.loader = object()
        self.reviewer = object()
        self.formatter = object()


def test_initial_state():
    state = ReviewStateHarness()

    assert state.reviewed() == 0
    assert state.issues() == 0
    assert state.empty()
    assert not state.approved()


def test_reset():
    state = ReviewStateHarness()

    state.reviewed_files = 3
    state.last_report = ReviewReport(score=90.0)

    state.reset()

    assert state.reviewed() == 0
    assert state.last_report is None
    assert state.empty()


def test_summary_without_report():
    state = ReviewStateHarness()

    assert state.summary() == {
        "reviewed": 0,
        "score": 0.0,
        "approved": False,
        "total_issues": 0,
    }


def test_statistics_counts_severity():
    state = ReviewStateHarness()

    report = ReviewReport(
        issues=[
            ReviewIssue(
                file="a.py",
                line=1,
                severity=Severity.ERROR,
                rule="TEST",
                message="error",
            ),
            ReviewIssue(
                file="b.py",
                line=2,
                severity=Severity.WARNING,
                rule="TEST",
                message="warning",
            ),
            ReviewIssue(
                file="c.py",
                line=3,
                severity=Severity.INFO,
                rule="TEST",
                message="info",
            ),
        ],
        score=85.0,
    )

    state.reviewed_files = 3
    state.last_report = report

    statistics = state.statistics()

    assert statistics["reviewed"] == 3
    assert statistics["score"] == 85.0
    assert statistics["total"] == 3
    assert statistics["critical"] == 0
    assert statistics["errors"] == 1
    assert statistics["warnings"] == 1
    assert statistics["info"] == 1
    assert not statistics["approved"]


def test_approved_report():
    state = ReviewStateHarness()

    state.reviewed_files = 1
    state.last_report = ReviewReport(
        issues=[],
        score=100.0,
    )

    assert state.approved()
    assert state.health()["healthy"]


def test_error_report_is_unhealthy():
    state = ReviewStateHarness()

    state.reviewed_files = 1
    state.last_report = ReviewReport(
        issues=[
            ReviewIssue(
                file="a.py",
                line=1,
                severity=Severity.ERROR,
                rule="TEST",
                message="error",
            ),
        ],
        score=95.0,
    )

    assert not state.approved()
    assert not state.health()["healthy"]


def test_configuration():
    state = ReviewStateHarness()

    configuration = state.configuration()

    assert configuration["python_only"]
    assert configuration["export_json"]
    assert configuration["export_markdown"]
    assert configuration["approval_from_report"]


def test_diagnostics():
    state = ReviewStateHarness()

    diagnostics = state.diagnostics()

    assert diagnostics["engine"] == "ReviewStateHarness"
    assert diagnostics["ready"]
    assert diagnostics["reviewed"] == 0
    assert not diagnostics["has_report"]
