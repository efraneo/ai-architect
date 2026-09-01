from __future__ import annotations

from ai_architect.autonomous.execution_worker import ExecutionWorker


def test_execution_worker_executes_callback_successfully() -> None:
    worker = ExecutionWorker()

    task = {
        "callback": lambda: "completed",
    }

    result = worker.execute(task)

    assert result["success"] is True
    assert result["result"] == "completed"


def test_execution_worker_captures_callback_failure() -> None:
    worker = ExecutionWorker()

    def failing_callback() -> None:
        raise RuntimeError("expected failure")

    task = {
        "callback": failing_callback,
    }

    result = worker.execute(task)

    assert result["success"] is False
    assert "traceback" in result

    traceback_value = result["traceback"]

    assert isinstance(traceback_value, str)
    assert "expected failure" in traceback_value
