from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ai_architect.patch_generator.models import Patch, PatchFile
from ai_architect.patch_generator.patch_loader import PatchLoader
from ai_architect.patch_generator.patch_writer import PatchWriter


def build_patch(
    approved: bool,
) -> Patch:
    patch = Patch(
        id="test-patch",
        title="Test Patch",
        description="Patch used for approval persistence tests.",
        created_at=datetime.now(),
    )

    patch.diff = (
        "diff --git a/example.py b/example.py\n"
        "--- a/example.py\n"
        "+++ b/example.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    patch.files.append(
        PatchFile(
            path="example.py",
            action="MODIFY",
            additions=1,
            deletions=1,
        )
    )

    patch.approved = approved

    return patch


def test_patch_writer_and_loader_preserve_approval(
    tmp_path: Path,
) -> None:
    patch = build_patch(
        approved=True,
    )

    path = PatchWriter().save(
        patch,
        tmp_path,
    )

    loaded = PatchLoader().load(
        path,
    )

    assert loaded.approved is True
    assert loaded.id == patch.id
    assert loaded.diff == patch.diff
    assert loaded.total_files == 1


def test_patch_writer_and_loader_preserve_rejection(
    tmp_path: Path,
) -> None:
    patch = build_patch(
        approved=False,
    )

    path = PatchWriter().save(
        patch,
        tmp_path,
    )

    loaded = PatchLoader().load(
        path,
    )

    assert loaded.approved is False
