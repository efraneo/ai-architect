from pathlib import Path

from ai_architect.improver.engine_facade import ImprovementEngineFacadeMixin
from ai_architect.improver.improvement_engine import ImprovementEngine


def test_improvement_engine_keeps_facade_api() -> None:
    engine = ImprovementEngine()

    assert isinstance(engine, ImprovementEngineFacadeMixin)
    assert isinstance(engine.version(), str)
    assert "healthy" in engine.health()


def test_improvement_engine_core_stays_under_size_budget() -> None:
    path = Path(__file__).parents[2] / "ai_architect" / "improver" / "improvement_engine.py"
    assert len(path.read_text(encoding="utf-8").splitlines()) < 600
