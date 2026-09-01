from pathlib import Path

from ai_architect.execution.execution_pipeline import ExecutionPipeline
from ai_architect.execution.pipeline_state import ExecutionPipelineStateMixin


def test_execution_pipeline_keeps_public_state_api() -> None:
    pipeline = ExecutionPipeline()

    assert isinstance(pipeline, ExecutionPipelineStateMixin)
    assert pipeline.executed() == 0
    assert pipeline.failed() == 0
    assert pipeline.total() == 0
    assert pipeline.empty() is True
    assert pipeline.configuration()["git_apply"] is True


def test_execution_pipeline_core_stays_under_size_budget() -> None:
    path = Path(ExecutionPipeline.__module__.replace(".", "/") + ".py")
    # Resolve from repository root rather than relying on cwd.
    path = Path(__file__).parents[2] / "ai_architect" / "execution" / "execution_pipeline.py"
    assert len(path.read_text(encoding="utf-8").splitlines()) < 600
