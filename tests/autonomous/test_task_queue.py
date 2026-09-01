"""Tests for the autonomous task queue."""

from ai_architect.autonomous.task_queue import TaskQueue


def test_task_queue_starts_empty() -> None:
    """A new task queue must be empty."""
    queue = TaskQueue()

    assert queue.empty() is True
    assert queue.size() == 0


def test_task_queue_push_and_pop() -> None:
    """A pushed task must be returned by pop."""
    queue = TaskQueue()

    task = {
        "name": "test",
        "priority": 10,
    }

    queue.push(task)

    assert queue.empty() is False
    assert queue.size() == 1

    result = queue.pop()

    assert result == task
    assert queue.empty() is True
    assert queue.size() == 0


def test_task_queue_pop_empty_returns_none() -> None:
    """Popping an empty queue must return None."""
    queue = TaskQueue()

    assert queue.pop() is None
