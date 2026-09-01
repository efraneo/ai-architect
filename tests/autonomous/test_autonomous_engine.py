from __future__ import annotations

from ai_architect.autonomous.autonomous_engine import AutonomousEngine


def test_autonomous_engine_executes_tasks() -> None:
    engine = AutonomousEngine()

    tasks = [
        {
            "priority": 10,
            "risk": 1,
            "callback": lambda: "first",
        },
        {
            "priority": 5,
            "risk": 1,
            "callback": lambda: "second",
        },
    ]

    result = engine.execute(tasks)

    assert "results" in result
    assert "monitor" in result

    results = result["results"]

    assert isinstance(results, list)
    assert len(results) == 2

    assert results[0]["success"] is True
    assert results[0]["result"] == "first"

    assert results[1]["success"] is True
    assert results[1]["result"] == "second"


def test_autonomous_engine_processes_failed_task() -> None:
    engine = AutonomousEngine()

    def failing_callback() -> None:
        raise RuntimeError("autonomous failure")

    tasks = [
        {
            "priority": 10,
            "risk": 1,
            "callback": failing_callback,
        },
    ]

    result = engine.execute(tasks)

    results = result["results"]

    assert isinstance(results, list)
    assert len(results) == 1

    assert results[0]["success"] is False
    assert "traceback" in results[0]
    assert "autonomous failure" in results[0]["traceback"]


def test_autonomous_engine_handles_empty_task_list() -> None:
    engine = AutonomousEngine()

    result = engine.execute([])

    assert result["results"] == []

    monitor = result["monitor"]

    assert isinstance(monitor, dict)
    assert monitor["executions"] == 0
    assert monitor["events"] == []
