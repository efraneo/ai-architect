from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ai_architect.execution.execution_engine import ExecutionEngine
from ai_architect.patch_generator.models import Patch, PatchFile


def build_patch(
    approved: bool = True,
) -> Patch:
    patch = Patch(
        id="engine-test",
        title="Engine Test Patch",
        description="Patch used by execution engine tests.",
        created_at=datetime.now(),
    )

    patch.approved = approved

    patch.files.append(
        PatchFile(
            path="file.txt",
            action="modify",
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


def test_execution_engine_starts_ready() -> None:
    engine = ExecutionEngine()

    assert engine.ready() is True
    assert engine.supports_dry_run() is True
    assert engine.supports_patch_validation() is True


def test_execution_engine_rejects_unapproved_patch(
    tmp_path: Path,
) -> None:
    engine = ExecutionEngine()

    patch = build_patch(
        approved=False,
    )

    result = engine.execute(
        tmp_path,
        patch,
    )

    assert result["success"] is False
    assert result["approved"] is False
    assert result["message"] == "Patch validation failed."


def test_execution_engine_dry_run_rejects_unapproved_patch(
    tmp_path: Path,
) -> None:
    engine = ExecutionEngine()

    patch = build_patch(
        approved=False,
    )

    result = engine.dry_run(
        tmp_path,
        patch,
    )

    assert result["success"] is False
    assert result["approved"] is False
    assert result["dry_run"] is True
    assert result["files"] == 1
    assert result["message"] == "Patch validation failed."


def test_execution_engine_exposes_patch_summary() -> None:
    engine = ExecutionEngine()

    patch = build_patch()

    summary = engine.patch_summary(
        patch,
    )

    assert summary["id"] == "engine-test"
    assert summary["title"] == "Engine Test Patch"
    assert summary["files"] == 1
    assert summary["approved"] is True


def test_execution_engine_exposes_pipeline_metadata() -> None:
    engine = ExecutionEngine()

    configuration = engine.configuration()
    statistics = engine.statistics()
    health = engine.health()
    diagnostics = engine.diagnostics()

    assert configuration["validator"] == "PatchValidator"
    assert configuration["pipeline"] == "ExecutionPipeline"

    assert statistics["validator"] == "PatchValidator"
    assert statistics["pipeline"] == "ExecutionPipeline"

    assert health["validator"] is True
    assert health["healthy"] is True

    assert diagnostics["engine"] == "ExecutionEngine"
    assert diagnostics["pipeline"] == "ExecutionPipeline"
    assert diagnostics["validator"] == "PatchValidator"


def test_execution_engine_patch_helpers() -> None:
    engine = ExecutionEngine()

    patch = build_patch()

    assert engine.validate(patch) is True
    assert engine.patch_valid(patch) is True
    assert engine.patch_count(patch) == 1
    assert len(engine.patch_files(patch)) == 1


def test_execution_engine_reset_recreates_components() -> None:
    engine = ExecutionEngine()

    original_pipeline = engine.pipeline
    original_validator = engine.validator

    engine.reset()

    assert engine.pipeline is not original_pipeline
    assert engine.validator is not original_validator


def test_execution_engine_string_representation() -> None:
    engine = ExecutionEngine()

    assert "Execution Engine" in str(engine)
    assert "ExecutionEngine" in repr(engine)
