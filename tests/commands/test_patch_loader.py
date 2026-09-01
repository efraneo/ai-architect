from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from ai_architect.patch_generator.patch_loader import PatchLoader


def test_patch_loader_loads_patch(tmp_path: Path) -> None:
    patch_file = tmp_path / "sample.patch"

    patch_file.write_text(
        "\n".join(
            [
                "ID: test-001",
                "TITLE: Test Patch",
                "DESCRIPTION: Test patch description",
                f"CREATED: {datetime.now().isoformat()}",
                "",
                "FILES",
                "-----",
                "MODIFY ai_architect/example.py",
                "",
                "diff --git a/ai_architect/example.py b/ai_architect/example.py",
                "--- a/ai_architect/example.py",
                "+++ b/ai_architect/example.py",
                "@@ -1 +1 @@",
                "-old",
                "+new",
            ]
        ),
        encoding="utf-8",
    )

    loader = PatchLoader()

    patch = loader.load(patch_file)

    assert patch.id == "test-001"
    assert patch.title == "Test Patch"
    assert patch.description == "Test patch description"
    assert patch.total_files == 1
    assert "diff --git" in patch.diff


def test_patch_loader_exists(tmp_path: Path) -> None:
    patch_file = tmp_path / "sample.patch"

    patch_file.write_text(
        "test",
        encoding="utf-8",
    )

    loader = PatchLoader()

    assert loader.exists(patch_file)
    assert not loader.exists(tmp_path / "missing.patch")


def test_patch_loader_load_if_exists_returns_none(
    tmp_path: Path,
) -> None:
    loader = PatchLoader()

    result = loader.load_if_exists(
        tmp_path / "missing.patch",
    )

    assert result is None


def test_patch_loader_metadata(tmp_path: Path) -> None:
    patch_file = tmp_path / "sample.patch"

    patch_file.write_text(
        "\n".join(
            [
                "ID: test-002",
                "TITLE: Metadata Patch",
                "DESCRIPTION: Metadata test",
                f"CREATED: {datetime.now().isoformat()}",
                "",
                "FILES",
                "-----",
                "CREATE example.py",
                "",
                "diff --git a/example.py b/example.py",
                "new file mode 100644",
                "--- /dev/null",
                "+++ b/example.py",
                "@@ -0,0 +1 @@",
                "+print('hello')",
            ]
        ),
        encoding="utf-8",
    )

    loader = PatchLoader()

    metadata = loader.metadata(patch_file)

    assert metadata["id"] == "test-002"
    assert metadata["title"] == "Metadata Patch"
    assert metadata["description"] == "Metadata test"
    assert metadata["files"] == 1
    assert "created" in metadata
    assert "approved" in metadata


def test_patch_loader_missing_created_metadata_raises(
    tmp_path: Path,
) -> None:
    patch_file = tmp_path / "invalid.patch"

    patch_file.write_text(
        "\n".join(
            [
                "ID: invalid",
                "TITLE: Invalid",
                "DESCRIPTION: Missing created",
            ]
        ),
        encoding="utf-8",
    )

    loader = PatchLoader()

    with pytest.raises(ValueError, match="CREATED"):
        loader.load(patch_file)
