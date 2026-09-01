from __future__ import annotations

from ai_architect.autonomous.execution_monitor import ExecutionMonitor


def test_execution_monitor_starts_empty() -> None:
    monitor = ExecutionMonitor()

    report = monitor.report()

    assert report["executions"] == 0
    assert report["events"] == []


def test_execution_monitor_registers_event() -> None:
    monitor = ExecutionMonitor()

    event = {
        "success": True,
        "result": "completed",
    }

    monitor.register(event)

    report = monitor.report()

    assert report["executions"] == 1

    events = report["events"]

    assert isinstance(events, list)
    assert len(events) == 1

    registered_event = events[0]

    assert isinstance(registered_event, dict)
    assert registered_event["success"] is True
    assert registered_event["result"] == "completed"
    assert "timestamp" in registered_event
