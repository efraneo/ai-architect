from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from ai_architect.commands import execute
from ai_architect.patch_generator.models import Patch, PatchFile
from ai_architect.patch_generator.patch_writer import PatchWriter


def init_git(repository: Path) -> None:
    subprocess.run(["git", "init"], cwd=repository, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repository, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "AI Architect Test"], cwd=repository, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "."], cwd=repository, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repository, check=True, capture_output=True, text=True)


def make_patch(*, approved: bool) -> Patch:
    patch = Patch(
        id="integration-flow",
        title="Integration flow patch",
        description="End-to-end execution boundary test.",
        created_at=datetime.now(),
        approved=approved,
    )
    patch.files.append(
        PatchFile(path="app.txt", action="MODIFY", additions=1, deletions=1)
    )
    patch.diff = (
        "diff --git a/app.txt b/app.txt\n"
        "--- a/app.txt\n"
        "+++ b/app.txt\n"
        "@@ -1 +1 @@\n"
        "-before\n"
        "+after\n"
    )
    return patch


def test_persisted_approved_patch_dry_run_then_execute_and_rollback(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    target = repository / "app.txt"
    target.write_text("before\n", encoding="utf-8")
    init_git(repository)

    patch_path = PatchWriter().save(make_patch(approved=True), tmp_path / "patches")

    dry = execute.dry_run(str(repository), str(patch_path))
    assert dry["success"] is True
    assert dry["approved"] is True
    assert dry["dry_run"] is True
    assert target.read_text(encoding="utf-8") == "before\n"

    applied = execute.run(str(repository), str(patch_path))
    assert applied["success"] is True
    assert applied["approved"] is True
    assert target.read_text(encoding="utf-8") == "after\n"

    from ai_architect.execution.execution_engine import ExecutionEngine

    rollback = ExecutionEngine().rollback(repository, make_patch(approved=True))
    assert rollback["success"] is True
    assert target.read_text(encoding="utf-8") == "before\n"


def test_cli_rejects_persisted_unapproved_patch_without_modifying_repository(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    target = repository / "app.txt"
    target.write_text("before\n", encoding="utf-8")
    init_git(repository)

    patch_path = PatchWriter().save(make_patch(approved=False), tmp_path / "patches")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_architect",
            "execute",
            str(repository),
            "--patch",
            str(patch_path),
            "--json",
        ],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["success"] is False
    assert payload["approved"] is False
    assert target.read_text(encoding="utf-8") == "before\n"
