from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ai_architect.patch_generator.models import Patch, PatchFile
from ai_architect.patch_generator.patch_loader import PatchLoader
from ai_architect.patch_generator.patch_validator import PatchValidator
from ai_architect.patch_generator.patch_writer import PatchWriter


def build_patch(
    approved: bool = True,
) -> Patch:
    patch = Patch(
        id="ROUNDTRIP-001",
        title="Roundtrip Test Patch",
        description="Validates complete Patch persistence.",
        created_at=datetime(
            2026,
            8,
            24,
            12,
            0,
            0,
        ),
        approved=approved,
    )

    patch.files.extend(
        [
            PatchFile(
                path="ai_architect/example.py",
                action="MODIFY",
                additions=7,
                deletions=3,
            ),
            PatchFile(
                path="ai_architect/new_file.py",
                action="CREATE",
                additions=12,
                deletions=0,
            ),
            PatchFile(
                path="ai_architect/old_file.py",
                action="DELETE",
                additions=0,
                deletions=9,
            ),
        ]
    )

    patch.diff = (
        "diff --git a/ai_architect/example.py "
        "b/ai_architect/example.py\n"
        "--- a/ai_architect/example.py\n"
        "+++ b/ai_architect/example.py\n"
        "@@ -1,3 +1,7 @@\n"
        "-old\n"
        "+new\n"
        "+line1\n"
        "+line2\n"
        "+line3\n"
        "+line4\n"
        "+line5\n"
        "\n"
    )

    return patch


def test_patch_roundtrip_preserves_metadata(
    tmp_path: Path,
) -> None:
    patch = build_patch()

    path = PatchWriter().save(
        patch,
        tmp_path,
    )

    loaded = PatchLoader().load(
        path,
    )

    assert loaded.id == patch.id
    assert loaded.title == patch.title
    assert loaded.description == patch.description
    assert loaded.created_at == patch.created_at
    assert loaded.approved is True


def test_patch_roundtrip_preserves_files(
    tmp_path: Path,
) -> None:
    patch = build_patch()

    path = PatchWriter().save(
        patch,
        tmp_path,
    )

    loaded = PatchLoader().load(
        path,
    )

    assert loaded.total_files == 3

    assert loaded.files[0].path == (
        "ai_architect/example.py"
    )
    assert loaded.files[0].action == "MODIFY"

    assert loaded.files[1].path == (
        "ai_architect/new_file.py"
    )
    assert loaded.files[1].action == "CREATE"

    assert loaded.files[2].path == (
        "ai_architect/old_file.py"
    )
    assert loaded.files[2].action == "DELETE"


def test_patch_roundtrip_preserves_additions_and_deletions(
    tmp_path: Path,
) -> None:
    patch = build_patch()

    path = PatchWriter().save(
        patch,
        tmp_path,
    )

    loaded = PatchLoader().load(
        path,
    )

    assert loaded.files[0].additions == 7
    assert loaded.files[0].deletions == 3

    assert loaded.files[1].additions == 12
    assert loaded.files[1].deletions == 0

    assert loaded.files[2].additions == 0
    assert loaded.files[2].deletions == 9


def test_patch_roundtrip_preserves_diff(
    tmp_path: Path,
) -> None:
    patch = build_patch()

    path = PatchWriter().save(
        patch,
        tmp_path,
    )

    loaded = PatchLoader().load(
        path,
    )

    assert loaded.diff == patch.diff


def test_patch_roundtrip_remains_structurally_valid(
    tmp_path: Path,
) -> None:
    patch = build_patch()

    path = PatchWriter().save(
        patch,
        tmp_path,
    )

    loaded = PatchLoader().load(
        path,
    )

    validator = PatchValidator()

    assert validator.validate_structure(
        loaded,
    ) is True

    assert validator.approved(
        loaded,
    ) is True


def test_patch_roundtrip_preserves_rejection(
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

    validator = PatchValidator()

    assert validator.validate_structure(
        loaded,
    ) is True

    assert validator.approved(
        loaded,
    ) is False


def test_patch_writer_serializes_file_statistics(
    tmp_path: Path,
) -> None:
    patch = build_patch()

    path = PatchWriter().save(
        patch,
        tmp_path,
    )

    text = path.read_text(
        encoding="utf-8",
    )

    assert (
        "MODIFY ai_architect/example.py 7 3"
        in text
    )

    assert (
        "CREATE ai_architect/new_file.py 12 0"
        in text
    )

    assert (
        "DELETE ai_architect/old_file.py 0 9"
        in text
    )


def test_patch_loader_loads_legacy_file_entries(
    tmp_path: Path,
) -> None:
    path = tmp_path / "legacy.patch"

    path.write_text(
        "\n".join(
            [
                "ID: LEGACY-001",
                "TITLE: Legacy Patch",
                "DESCRIPTION: Legacy patch format.",
                "CREATED: 2026-08-24T12:00:00",
                "APPROVED: true",
                "",
                "FILES",
                "--------------------------------",
                "MODIFY ai_architect/example.py",
                "",
                "diff --git a/ai_architect/example.py "
                "b/ai_architect/example.py",
                "--- a/ai_architect/example.py",
                "+++ b/ai_architect/example.py",
                "@@ -1 +1 @@",
                "-old",
                "+new",
            ]
        ),
        encoding="utf-8",
    )

    loaded = PatchLoader().load(
        path,
    )

    assert loaded.id == "LEGACY-001"
    assert loaded.approved is True
    assert loaded.total_files == 1

    assert loaded.files[0].action == "MODIFY"
    assert loaded.files[0].path == (
        "ai_architect/example.py"
    )

    assert loaded.files[0].additions == 0
    assert loaded.files[0].deletions == 0
