from ai_architect.reviewer.models import (
    ReviewIssue,
    ReviewReport,
    Severity,
)


def test_review_issue_preserves_metadata() -> None:
    issue = ReviewIssue(
        file="example.py",
        line=10,
        severity=Severity.WARNING,
        rule="COMPLEXITY",
        message="High complexity",
    )

    assert issue.file == "example.py"
    assert issue.line == 10
    assert issue.severity == Severity.WARNING
    assert issue.rule == "COMPLEXITY"
    assert issue.message == "High complexity"


def test_review_report_starts_clean() -> None:
    report = ReviewReport()

    assert report.issues == []
    assert report.score == 100.0
    assert report.total_issues == 0
    assert report.approved is True


def test_review_report_adds_issue() -> None:
    report = ReviewReport()

    report.add(
        ReviewIssue(
            file="example.py",
            line=1,
            severity=Severity.WARNING,
            rule="TEST",
            message="Test issue",
        )
    )

    assert report.total_issues == 1
    assert report.approved is True


def test_review_report_rejects_error() -> None:
    report = ReviewReport()

    report.add(
        ReviewIssue(
            file="example.py",
            line=1,
            severity=Severity.ERROR,
            rule="TEST_ERROR",
            message="Error",
        )
    )

    assert report.total_issues == 1
    assert report.approved is False


def test_review_report_rejects_critical() -> None:
    report = ReviewReport()

    report.add(
        ReviewIssue(
            file="example.py",
            line=1,
            severity=Severity.CRITICAL,
            rule="TEST_CRITICAL",
            message="Critical issue",
        )
    )

    assert report.approved is False


def test_warning_does_not_reject_report() -> None:
    report = ReviewReport()

    report.add(
        ReviewIssue(
            file="example.py",
            line=1,
            severity=Severity.WARNING,
            rule="TEST_WARNING",
            message="Warning",
        )
    )

    assert report.approved is True
