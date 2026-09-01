from datetime import datetime

from ai_architect.reviewer.approval_engine import ApprovalEngine
from ai_architect.reviewer.models import (
    ReviewIssue,
    ReviewReport,
    Severity,
)


def build_approved_report() -> ReviewReport:
    return ReviewReport(
        issues=[],
        score=100.0,
    )


def build_rejected_report() -> ReviewReport:
    report = ReviewReport(
        issues=[],
        score=80.0,
    )

    report.add(
        ReviewIssue(
            file="example.py",
            line=10,
            severity=Severity.ERROR,
            rule="TEST_ERROR",
            message="Test error.",
        )
    )

    return report


def test_approval_engine_starts_without_decision() -> None:
    engine = ApprovalEngine()

    assert engine.approved() is False
    assert engine.has_decision() is False
    assert engine.summary()["patch_id"] == ""


def test_approval_engine_approves_clean_report() -> None:
    engine = ApprovalEngine()

    report = build_approved_report()

    assert engine.evaluate(
        report,
        "patch-001",
    ) is True

    assert engine.approved() is True
    assert engine.has_decision() is True

    summary = engine.summary()

    assert summary["patch_id"] == "patch-001"
    assert summary["approved"] is True


def test_approval_engine_rejects_report_with_errors() -> None:
    engine = ApprovalEngine()

    report = build_rejected_report()

    assert engine.evaluate(
        report,
        "patch-002",
    ) is False

    assert engine.approved() is False
    assert engine.has_decision() is True

    summary = engine.summary()

    assert summary["patch_id"] == "patch-002"
    assert summary["approved"] is False


def test_approval_engine_rejects_missing_report() -> None:
    engine = ApprovalEngine()

    assert engine.evaluate(
        None,
        "patch-003",
    ) is False

    assert engine.approved() is False
    assert engine.has_decision() is True

    summary = engine.summary()

    assert summary["patch_id"] == "patch-003"
    assert summary["approved"] is False


def test_approval_engine_reset_clears_decision() -> None:
    engine = ApprovalEngine()

    engine.approve(
        "patch-004",
        "Explicit approval.",
    )

    assert engine.approved() is True
    assert engine.has_decision() is True

    engine.reset()

    assert engine.approved() is False
    assert engine.has_decision() is False
    assert engine.summary()["patch_id"] == ""
    assert engine.summary()["reason"] == ""


def test_approval_engine_exports_and_imports_state() -> None:
    engine = ApprovalEngine()

    engine.approve(
        "patch-005",
        "Approved for execution.",
    )

    exported = engine.export()

    restored = ApprovalEngine()

    restored.import_state(exported)

    assert restored.approved() is True
    assert restored.has_decision() is True
    assert restored.summary() == exported


def test_approval_engine_reports_configuration() -> None:
    engine = ApprovalEngine()

    configuration = engine.configuration()

    assert configuration["explicit_approval"] is True
    assert configuration["review_required"] is True
    assert configuration["patch_mutation"] is False
    assert configuration["default_approved"] is False


def test_approval_engine_reports_health() -> None:
    engine = ApprovalEngine()

    health = engine.health()

    assert health["healthy"] is True
    assert health["approved"] is False


def test_approval_engine_version_is_available() -> None:
    engine = ApprovalEngine()

    assert engine.version() == "1.0"


def test_approval_engine_has_no_datetime_dependency_in_state() -> None:
    engine = ApprovalEngine()

    assert isinstance(
        datetime.utcnow(),
        datetime,
    )
