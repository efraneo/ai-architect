from pathlib import Path

from ai_architect.reviewer.models import ReviewReport
from ai_architect.reviewer.reviewer import Reviewer


def test_reviewer_initializes() -> None:
    reviewer = Reviewer()

    assert reviewer.engine is not None
    assert reviewer.approval is not None
    assert reviewer.ready() is True


def test_reviewer_review_returns_report(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()

    source = repository / "example.py"
    source.write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    reviewer = Reviewer()

    report = reviewer.review(repository)

    assert isinstance(report, ReviewReport)
    assert reviewer.engine.reviewed_files == 1


def test_reviewer_evaluates_clean_report(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()

    source = repository / "example.py"
    source.write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    reviewer = Reviewer()

    report = reviewer.review_and_evaluate(
        repository,
        "patch-001",
    )

    assert isinstance(report, ReviewReport)
    assert reviewer.approved() is True
    assert reviewer.has_decision() is True

    summary = reviewer.summary()

    assert summary["approval"]["patch_id"] == "patch-001"
    assert summary["approval"]["approved"] is True


def test_reviewer_rejects_report_with_error(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()

    source = repository / "example.py"

    source.write_text(
        "\n".join(
            f"value_{index} = {index}"
            for index in range(601)
        ),
        encoding="utf-8",
    )

    reviewer = Reviewer()

    report = reviewer.review_and_evaluate(
        repository,
        "patch-002",
    )

    assert isinstance(report, ReviewReport)
    assert reviewer.approved() is False
    assert reviewer.has_decision() is True


def test_reviewer_reset_clears_state(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()

    source = repository / "example.py"
    source.write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    reviewer = Reviewer()

    reviewer.review_and_evaluate(
        repository,
        "patch-003",
    )

    assert reviewer.has_decision() is True

    reviewer.reset()

    assert reviewer.approved() is False
    assert reviewer.has_decision() is False
    assert reviewer.engine.reviewed_files == 0


def test_reviewer_configuration_is_explicit() -> None:
    reviewer = Reviewer()

    configuration = reviewer.configuration()

    assert configuration["approval_mutates_patch"] is False


def test_reviewer_health_is_available() -> None:
    reviewer = Reviewer()

    health = reviewer.health()

    assert "review" in health
    assert "approval" in health
    assert "healthy" in health


def test_reviewer_diagnostics_are_available() -> None:
    reviewer = Reviewer()

    diagnostics = reviewer.diagnostics()

    assert diagnostics["engine"] == "Reviewer"
    assert diagnostics["ready"] is True
    assert "review" in diagnostics
    assert "approval" in diagnostics


def test_reviewer_version_is_available() -> None:
    reviewer = Reviewer()

    assert reviewer.version() == "1.0"
