"""Tests for the autonomous task scheduler."""

from ai_architect.autonomous.task_scheduler import TaskScheduler


def test_scheduler_orders_tasks_by_priority_and_risk() -> None:
    """Higher priority and risk tasks must be scheduled first."""
    scheduler = TaskScheduler()

    tasks = [
        {
            "name": "low",
            "priority": 1,
            "risk": 1,
        },
        {
            "name": "high",
            "priority": 10,
            "risk": 1,
        },
        {
            "name": "medium",
            "priority": 5,
            "risk": 2,
        },
    ]

    result = scheduler.schedule(tasks)

    assert [task["name"] for task in result] == [
        "high",
        "medium",
        "low",
    ]


def test_scheduler_uses_risk_as_secondary_order() -> None:
    """Risk must break ties when priorities are equal."""
    scheduler = TaskScheduler()

    tasks = [
        {
            "name": "low-risk",
            "priority": 10,
            "risk": 1,
        },
        {
            "name": "high-risk",
            "priority": 10,
            "risk": 10,
        },
    ]

    result = scheduler.schedule(tasks)

    assert [task["name"] for task in result] == [
        "high-risk",
        "low-risk",
    ]


def test_scheduler_does_not_modify_original_list() -> None:
    """Scheduling must leave the input list unchanged."""
    scheduler = TaskScheduler()

    tasks = [
        {
            "name": "first",
            "priority": 1,
            "risk": 1,
        },
        {
            "name": "second",
            "priority": 10,
            "risk": 1,
        },
    ]

    original = list(tasks)

    scheduler.schedule(tasks)

    assert tasks == original
