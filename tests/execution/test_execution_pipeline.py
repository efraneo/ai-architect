from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

from ai_architect.execution.execution_pipeline import ExecutionPipeline
from ai_architect.patch_generator.models import Patch, PatchFile


def build_patch(diff: str, total_files: int = 1) -> Patch:
    patch = Patch(
        id="test-patch",
        title="Test Patch",
        description="Patch used by execution pipeline tests.",
        created_at=datetime.now(),
    )

    patch.diff = diff

    for index in range(total_files):
        patch.files.append(
            PatchFile(
                path=f"file_{index}.txt",
                action="modify",
            )
        )

    return patch


def initialize_git_repository(repository: Path) -> None:
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


def test_execution_pipeline_starts_empty() -> None:
    pipeline = ExecutionPipeline()

    assert pipeline.executed() == 0
    assert pipeline.failed() == 0
    assert pipeline.total() == 0
    assert pipeline.empty() is True
    assert pipeline.success() is False


def test_execution_pipeline_rejects_missing_repository(tmp_path: Path) -> None:
    pipeline = ExecutionPipeline()

    patch = build_patch(
        "diff --git a/file.txt b/file.txt\n"
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    result = pipeline.dry_run(
        tmp_path / "missing",
        patch,
    )

    assert result["success"] is False
    assert result["dry_run"] is True
    assert result["approved"] is False
    assert "does not exist" in result["message"]


def test_execution_pipeline_rejects_non_git_repository(tmp_path: Path) -> None:
    repository = tmp_path / "project"
    repository.mkdir()

    target = repository / "file.txt"
    target.write_text(
        "old\n",
        encoding="utf-8",
    )

    pipeline = ExecutionPipeline()

    patch = build_patch(
        "diff --git a/file.txt b/file.txt\n"
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    result = pipeline.dry_run(
        repository,
        patch,
    )

    assert result["success"] is False
    assert result["approved"] is False
    assert "Git repository" in result["message"]


def test_execution_pipeline_dry_run_does_not_modify_repository(
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

    patch = build_patch(
        "diff --git a/file.txt b/file.txt\n"
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    pipeline = ExecutionPipeline()

    result = pipeline.dry_run(
        repository,
        patch,
    )

    assert result["success"] is True
    assert result["approved"] is True
    assert result["dry_run"] is True
    assert result["files"] == 1
    assert target.read_text(encoding="utf-8") == "old\n"


def test_execution_pipeline_applies_valid_patch(
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

    patch = build_patch(
        "diff --git a/file.txt b/file.txt\n"
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    pipeline = ExecutionPipeline()

    result = pipeline.execute(
        repository,
        patch,
    )

    assert result["success"] is True
    assert result["executed"] == 1
    assert result["failed"] == 0
    assert result["total"] == 1
    assert target.read_text(encoding="utf-8") == "new\n"
    assert pipeline.success() is True


def test_execution_pipeline_rejects_invalid_patch(
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

    patch = build_patch(
        "diff --git a/file.txt b/file.txt\n"
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1 +1 @@\n"
        "-this-does-not-exist\n"
        "+new\n"
    )

    pipeline = ExecutionPipeline()

    result = pipeline.execute(
        repository,
        patch,
    )

    assert result["success"] is False
    assert result["executed"] == 0
    assert result["failed"] == 1
    assert result["total"] == 1
    assert target.read_text(encoding="utf-8") == "old\n"


def test_execution_pipeline_rolls_back_applied_patch(
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

    patch = build_patch(
        "diff --git a/file.txt b/file.txt\n"
        "--- a/file.txt\n"
        "+++ b/file.txt\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    pipeline = ExecutionPipeline()

    execution = pipeline.execute(
        repository,
        patch,
    )

    assert execution["success"] is True
    assert target.read_text(encoding="utf-8") == "new\n"

    rollback = pipeline.rollback(
        repository,
        patch,
    )

    assert rollback["success"] is True
    assert rollback["rolled_back"] == 1
    assert target.read_text(encoding="utf-8") == "old\n"


def test_execution_pipeline_verify_git_repository(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "project"
    repository.mkdir()

    pipeline = ExecutionPipeline()

    assert pipeline.verify(repository) is False

    initialize_git_repository(repository)

    assert pipeline.verify(repository) is True


def test_execution_pipeline_reports_capabilities() -> None:
    pipeline = ExecutionPipeline()

    assert pipeline.supports_rollback() is True
    assert pipeline.supports_verification() is True
    assert pipeline.supports_atomic_write() is False


def test_execution_pipeline_reports_configuration() -> None:
    pipeline = ExecutionPipeline()

    configuration = pipeline.configuration()

    assert configuration["rollback"] is True
    assert configuration["verification"] is True
    assert configuration["git_apply"] is True
    assert configuration["preflight_check"] is True


def test_execution_pipeline_reset_clears_state() -> None:
    pipeline = ExecutionPipeline()

    pipeline.executed_files = 3
    pipeline.failed_files = 2
    pipeline.last_result = {
        "success": False,
    }

    pipeline.reset()

    assert pipeline.executed() == 0
    assert pipeline.failed() == 0
    assert pipeline.total() == 0
    assert pipeline.last_result == {}
