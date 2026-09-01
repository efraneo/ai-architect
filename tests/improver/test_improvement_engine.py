from __future__ import annotations

from pathlib import Path

from ai_architect.improver.improvement_engine import ImprovementEngine


def test_improvement_engine_starts() -> None:
    engine = ImprovementEngine()

    assert isinstance(
        engine,
        ImprovementEngine,
    )


def test_improvement_engine_exposes_version() -> None:
    engine = ImprovementEngine()

    assert isinstance(
        engine.version(),
        str,
    )

    assert engine.version()


def test_improvement_engine_exposes_health() -> None:
    engine = ImprovementEngine()

    result = engine.health()

    assert isinstance(
        result,
        dict,
    )

    assert "analysis" in result
    assert "context" in result
    assert "planner" in result
    assert "provider" in result
    assert "builder" in result
    assert "validator" in result
    assert "writer" in result
    assert "healthy" in result


def test_improvement_engine_exposes_provider_summary() -> None:
    engine = ImprovementEngine()

    result = engine.provider_summary()

    assert isinstance(
        result,
        dict,
    )


def test_improvement_engine_rejects_missing_repository(
    tmp_path: Path,
) -> None:
    engine = ImprovementEngine()

    missing = tmp_path / "does-not-exist"

    result = engine.improve(
        str(missing),
    )

    assert result["success"] is False
    assert result["error"] == "Repository not found."
    assert result["repository"] == str(
        missing.resolve(),
    )


def test_improvement_engine_rejects_file_repository(
    tmp_path: Path,
) -> None:
    engine = ImprovementEngine()

    target = tmp_path / "project.txt"

    target.write_text(
        "test",
        encoding="utf-8",
    )

    result = engine.improve(
        str(target),
    )

    assert result["success"] is False
    assert result["error"] == "Project path is not a directory."
    assert result["repository"] == str(
        target.resolve(),
    )
