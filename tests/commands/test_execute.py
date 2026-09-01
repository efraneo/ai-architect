from __future__ import annotations

from pathlib import Path

from ai_architect.commands import execute


def test_execute_rejects_missing_repository(tmp_path: Path) -> None:
    patch = tmp_path / "change.patch"

    result = execute.run(
        project=str(tmp_path / "missing-project"),
        patch=str(patch),
    )

    assert result["success"] is False
    assert result["error"] == "Repository not found."


def test_execute_rejects_missing_patch(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    result = execute.run(
        project=str(project),
        patch=str(tmp_path / "missing.patch"),
    )

    assert result["success"] is False
    assert result["error"] == "Patch file not found."


def test_execute_rejects_patch_directory(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    patch_directory = tmp_path / "patch"
    patch_directory.mkdir()

    result = execute.run(
        project=str(project),
        patch=str(patch_directory),
    )

    assert result["success"] is False
    assert result["error"] == "Patch path is not a file."


def test_execute_exposes_command_metadata() -> None:
    assert execute.COMMAND["name"] == "execute"
    assert "patch" in execute.COMMAND["help"].lower()


def test_execute_supports_dry_run_helper(tmp_path: Path) -> None:
    result = execute.dry_run(
        project=str(tmp_path / "missing-project"),
        patch=str(tmp_path / "missing.patch"),
    )

    assert result["success"] is False
    assert result["error"] == "Repository not found."
