from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

from ai_architect.execution.execution_engine import ExecutionEngine
from ai_architect.patch_generator.models import Patch, PatchFile


def initialize_git_repository(repository: Path) -> None:
    subprocess.run(
        ["git", "init"], cwd=repository, check=True,
        capture_output=True, text=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repository,
        check=True, capture_output=True, text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repository,
        check=True, capture_output=True, text=True,
    )


def commit_repository(repository: Path) -> None:
    subprocess.run(
        ["git", "add", "."], cwd=repository, check=True,
        capture_output=True, text=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"], cwd=repository,
        check=True, capture_output=True, text=True,
    )


def build_patch(*, approved: bool = True) -> Patch:
    patch = Patch(
        id="lifecycle-test",
        title="Lifecycle Test Patch",
        description="Patch used to verify the complete execution lifecycle.",
        created_at=datetime.now(),
    )
    patch.approved = approved
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


def make_repository(tmp_path: Path) -> tuple[Path, Path]:
    repository = tmp_path / "project"
    repository.mkdir()
    target = repository / "file.txt"
    target.write_text("old\n", encoding="utf-8")
    initialize_git_repository(repository)
    commit_repository(repository)
    return repository, target


def test_approved_patch_dry_run_does_not_modify_then_execute_does(
    tmp_path: Path,
) -> None:
    repository, target = make_repository(tmp_path)
    engine = ExecutionEngine()
    patch = build_patch(approved=True)

    dry_run = engine.dry_run(repository, patch)

    assert dry_run["success"] is True
    assert dry_run["approved"] is True
    assert dry_run["dry_run"] is True
    assert target.read_text(encoding="utf-8") == "old\n"

    execution = engine.execute(repository, patch)

    assert execution["success"] is True
    assert execution["approved"] is True
    assert execution["repository"] == str(repository.resolve())
    assert execution["result"]["success"] is True
    assert target.read_text(encoding="utf-8") == "new\n"


def test_execute_pipeline_preserves_approval_boundary(
    tmp_path: Path,
) -> None:
    repository, target = make_repository(tmp_path)
    engine = ExecutionEngine()
    patch = build_patch(approved=True)

    result = engine.execute_pipeline(repository, patch)

    assert result["success"] is True
    assert result["approved"] is True
    assert result["result"]["success"] is True
    assert target.read_text(encoding="utf-8") == "new\n"


def test_approved_patch_with_invalid_diff_never_reaches_execution(
    tmp_path: Path,
) -> None:
    repository, target = make_repository(tmp_path)
    engine = ExecutionEngine()
    patch = build_patch(approved=True)
    patch.diff = ""

    result = engine.execute(repository, patch)

    assert result["success"] is False
    assert result["approved"] is False
    assert result["message"] == "Patch validation failed."
    assert target.read_text(encoding="utf-8") == "old\n"


def test_rollback_completes_full_lifecycle(
    tmp_path: Path,
) -> None:
    repository, target = make_repository(tmp_path)
    engine = ExecutionEngine()
    patch = build_patch(approved=True)

    execution = engine.execute(repository, patch)
    assert execution["success"] is True
    assert target.read_text(encoding="utf-8") == "new\n"

    rollback = engine.rollback(repository, patch)

    assert rollback["success"] is True
    assert rollback["rolled_back"] == 1
    assert target.read_text(encoding="utf-8") == "old\n"


def test_engine_reset_clears_pipeline_state(
    tmp_path: Path,
) -> None:
    repository, target = make_repository(tmp_path)
    engine = ExecutionEngine()
    patch = build_patch(approved=True)

    result = engine.execute(repository, patch)
    assert result["success"] is True
    assert target.read_text(encoding="utf-8") == "new\n"
    assert engine.pipeline.executed() == 1

    engine.reset()

    assert engine.pipeline.executed() == 0
    assert engine.pipeline.failed() == 0
    assert engine.pipeline.last_result == {}
