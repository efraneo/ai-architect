from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ai_architect.execution.execution_engine import ExecutionEngine
from ai_architect.patch_generator.models import Patch, PatchFile
from ai_architect.patch_generator.patch_loader import PatchLoader
from ai_architect.patch_generator.patch_writer import PatchWriter


def build_patch(
    approved: bool,
) -> Patch:
    patch = Patch(
        id="execution-approval-test",
        title="Execution Approval Test",
        description="Valid patch used for execution approval tests.",
        created_at=datetime.now(),
    )

    patch.files.append(
        PatchFile(
            path="example.py",
            action="MODIFY",
            additions=1,
            deletions=1,
        )
    )

    patch.diff = (
        "diff --git a/example.py b/example.py\n"
        "--- a/example.py\n"
        "+++ b/example.py\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n"
    )

    patch.approved = approved

    return patch


def test_loaded_unapproved_patch_is_rejected(
    tmp_path: Path,
) -> None:
    patch = build_patch(
        approved=False,
    )

    patch_path = PatchWriter().save(
        patch,
        tmp_path,
    )

    loaded = PatchLoader().load(
        patch_path,
    )

    result = ExecutionEngine().execute(
        tmp_path,
        loaded,
    )

    assert result["success"] is False
    assert result["approved"] is False
    assert result["message"] == "Patch validation failed."


def test_loaded_approved_patch_passes_validation(
    tmp_path: Path,
) -> None:
    patch = build_patch(
        approved=True,
    )

    patch_path = PatchWriter().save(
        patch,
        tmp_path,
    )

    loaded = PatchLoader().load(
        patch_path,
    )

    assert loaded.approved is True
    assert (
        ExecutionEngine().validate(
            loaded,
        )
        is True
    )
