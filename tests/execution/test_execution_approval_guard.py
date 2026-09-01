from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ai_architect.execution.execution_engine import ExecutionEngine
from ai_architect.patch_generator.models import Patch, PatchFile


def build_unapproved_patch() -> Patch:
    patch = Patch(
        id="approval-guard-test",
        title="Approval Guard Test",
        description="Patch used to verify execution approval boundaries.",
        created_at=datetime.now(),
    )

    patch.approved = False

    patch.files.append(
        PatchFile(
            path="file.txt",
            action="MODIFY",
            additions=1,
            deletions=1,
        )
    )

    patch.diff = (
        "diff --git a/file.txt b/file.txt\n"
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    return patch


def initialize_git_repository(repository: Path) -> None:
    import subprocess

    subprocess.run(
        ["git", "init"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )


def commit_repository(repository: Path) -> None:
    import subprocess

    subprocess.run(
        ["git", "add", "."],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )

    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )


def test_execute_rejects_unapproved_patch(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()

    target = repository / "file.txt"
    target.write_text(
        "old\n",
        encoding="utf-8",
    )

    initialize_git_repository(repository)
    commit_repository(repository)

    engine = ExecutionEngine()

    patch = build_unapproved_patch()

    result = engine.execute(
        repository,
        patch,
    )

    assert result["success"] is False
    assert result["approved"] is False
    assert target.read_text(
        encoding="utf-8",
    ) == "old\n"


def test_execute_pipeline_does_not_bypass_approval(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()

    target = repository / "file.txt"
    target.write_text(
        "old\n",
        encoding="utf-8",
    )

    initialize_git_repository(repository)
    commit_repository(repository)

    engine = ExecutionEngine()

    patch = build_unapproved_patch()

    result = engine.execute_pipeline(
        repository,
        patch,
    )

    assert result["success"] is False
    assert target.read_text(
        encoding="utf-8",
    ) == "old\n"


def test_execute_rejects_approved_but_structurally_invalid_patch(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()

    target = repository / "file.txt"
    target.write_text("old\n", encoding="utf-8")

    initialize_git_repository(repository)
    commit_repository(repository)

    engine = ExecutionEngine()
    patch = build_unapproved_patch()
    patch.approved = True
    patch.diff = ""

    result = engine.execute(repository, patch)

    assert result["success"] is False
    assert result["approved"] is False
    assert result["message"] == "Patch validation failed."
    assert target.read_text(encoding="utf-8") == "old\n"
