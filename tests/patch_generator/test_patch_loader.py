from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from ai_architect.patch_generator.patch_loader import PatchLoader


def build_patch_file(
    path: Path,
    *,
    patch_id: str = "PATCH-001",
    title: str = "Test Patch",
    description: str = "Patch used by tests.",
    created: str = "2026-08-14T00:00:00",
) -> Path:
    path.write_text(
        "\n".join(
            [
                f"ID: {patch_id}",
                f"TITLE: {title}",
                f"DESCRIPTION: {description}",
                f"CREATED: {created}",
                "",
                "FILES",
                "-----",
                "MODIFY ai_architect/example.py",
                "CREATE ai_architect/new_file.py",
                "",
                "diff --git a/ai_architect/example.py b/ai_architect/example.py",
                "index 1111111..2222222 100644",
                "--- a/ai_architect/example.py",
                "+++ b/ai_architect/example.py",
                "@@ -1 +1 @@",
                "-old",
                "+new",
            ]
        ),
        encoding="utf-8",
    )

    return path


def test_patch_loader_loads_patch_metadata_and_files(tmp_path: Path) -> None:
    patch_path = build_patch_file(tmp_path / "test.patch")

    patch = PatchLoader().load(patch_path)

    assert patch.id == "PATCH-001"
    assert patch.title == "Test Patch"
    assert patch.description == "Patch used by tests."
    assert patch.created_at == datetime.fromisoformat("2026-08-14T00:00:00")

    assert patch.total_files == 2
    assert len(patch.files) == 2

    assert patch.files[0].path == "ai_architect/example.py"
    assert patch.files[0].action == "MODIFY"

    assert patch.files[1].path == "ai_architect/new_file.py"
    assert patch.files[1].action == "CREATE"


def test_patch_loader_preserves_git_diff(tmp_path: Path) -> None:
    patch_path = build_patch_file(tmp_path / "test.patch")

    patch = PatchLoader().load(patch_path)

    assert "diff --git a/ai_architect/example.py" in patch.diff
    assert "--- a/ai_architect/example.py" in patch.diff
    assert "+++ b/ai_architect/example.py" in patch.diff
    assert "-old" in patch.diff
    assert "+new" in patch.diff


def test_patch_loader_load_if_exists_returns_patch(tmp_path: Path) -> None:
    patch_path = build_patch_file(tmp_path / "test.patch")

    patch = PatchLoader().load_if_exists(patch_path)

    assert patch is not None
    assert patch.id == "PATCH-001"


def test_patch_loader_load_if_exists_returns_none_for_missing_file(
    tmp_path: Path,
) -> None:
    patch = PatchLoader().load_if_exists(
        tmp_path / "missing.patch",
    )

    assert patch is None


def test_patch_loader_exists(tmp_path: Path) -> None:
    patch_path = build_patch_file(tmp_path / "test.patch")

    loader = PatchLoader()

    assert loader.exists(patch_path) is True
    assert loader.exists(tmp_path / "missing.patch") is False


def test_patch_loader_rejects_missing_created_metadata(
    tmp_path: Path,
) -> None:
    patch_path = tmp_path / "invalid.patch"

    patch_path.write_text(
        "\n".join(
            [
                "ID: PATCH-001",
                "TITLE: Invalid Patch",
                "DESCRIPTION: Missing created metadata.",
                "",
                "FILES",
                "-----",
                "MODIFY example.py",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Patch is missing CREATED metadata.",
    ):
        PatchLoader().load(patch_path)


def test_patch_loader_rejects_missing_file() -> None:
    loader = PatchLoader()

    with pytest.raises(FileNotFoundError):
        loader.load("this-file-does-not-exist.patch")


def test_patch_loader_metadata_returns_summary(
    tmp_path: Path,
) -> None:
    patch_path = build_patch_file(tmp_path / "test.patch")

    metadata = PatchLoader().metadata(patch_path)

    assert metadata["id"] == "PATCH-001"
    assert metadata["title"] == "Test Patch"
    assert metadata["description"] == "Patch used by tests."
    assert metadata["files"] == 2
    assert metadata["approved"] is False


def test_patch_loader_summary_matches_metadata(
    tmp_path: Path,
) -> None:
    patch_path = build_patch_file(tmp_path / "test.patch")

    loader = PatchLoader()

    assert loader.summary(patch_path) == loader.metadata(patch_path)


def test_patch_loader_call_is_equivalent_to_load(
    tmp_path: Path,
) -> None:
    patch_path = build_patch_file(tmp_path / "test.patch")

    loader = PatchLoader()

    loaded = loader.load(patch_path)
    called = loader(patch_path)

    assert called.id == loaded.id
    assert called.title == loaded.title
    assert called.description == loaded.description
    assert called.created_at == loaded.created_at
    assert called.diff == loaded.diff
