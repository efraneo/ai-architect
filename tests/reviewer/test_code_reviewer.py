from pathlib import Path

from ai_architect.reviewer.code_reviewer import CodeReviewer
from ai_architect.reviewer.models import Severity


def test_code_reviewer_empty_file(tmp_path: Path) -> None:
    target = tmp_path / "empty.py"
    target.write_text("", encoding="utf-8")

    reviewer = CodeReviewer()

    report = reviewer.review(target)

    assert report.total_issues == 1

    issue = report.issues[0]

    assert issue.file == str(target)
    assert issue.severity == Severity.INFO
    assert issue.rule == "EMPTY_FILE"
    assert issue.line == 0
    assert report.score == 95.0


def test_code_reviewer_accepts_normal_file(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"

    target.write_text(
        "def hello() -> str:\n"
        '    return "hello"\n',
        encoding="utf-8",
    )

    reviewer = CodeReviewer()

    report = reviewer.review(target)

    assert report.total_issues == 0
    assert report.score == 100.0
    assert report.approved is True


def test_code_reviewer_detects_large_file(tmp_path: Path) -> None:
    target = tmp_path / "large.py"

    target.write_text(
        "\n".join(
            "x = 1"
            for _ in range(601)
        ),
        encoding="utf-8",
    )

    reviewer = CodeReviewer()

    report = reviewer.review(target)

    assert any(
        issue.rule == "MAX_FILE_LINES"
        and issue.severity == Severity.CRITICAL
        for issue in report.issues
    )

    assert report.approved is False


def test_code_reviewer_detects_complexity_warning(
    tmp_path: Path,
) -> None:
    target = tmp_path / "complex.py"

    target.write_text(
        "def complex_function(value):\n"
        "    if value > 0:\n"
        "        if value > 1:\n"
        "            if value > 2:\n"
        "                if value > 3:\n"
        "                    if value > 4:\n"
        "                        if value > 5:\n"
        "                            if value > 6:\n"
        "                                return value\n"
        "    return 0\n",
        encoding="utf-8",
    )

    reviewer = CodeReviewer()

    report = reviewer.review(target)

    assert report.score <= 100.0
    assert isinstance(report.approved, bool)


def test_code_reviewer_returns_report(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"

    target.write_text(
        "value = 42\n",
        encoding="utf-8",
    )

    reviewer = CodeReviewer()

    report = reviewer.review(target)

    assert report is not None
    assert hasattr(report, "issues")
    assert hasattr(report, "score")
    assert hasattr(report, "approved")
