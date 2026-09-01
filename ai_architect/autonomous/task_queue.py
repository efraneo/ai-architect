"""
Task Queue.
"""

from __future__ import annotations

from queue import Queue


class TaskQueue:
    def __init__(self) -> None:
        self._queue: Queue[dict[str, object]] = Queue()

    def push(
        self,
        task: dict[str, object],
    ) -> None:
        self._queue.put(task)

    def pop(
        self,
    ) -> dict[str, object] | None:
        if self._queue.empty():
            return None

        return self._queue.get()

    def empty(
        self,
    ) -> bool:
        return self._queue.empty()

    def size(
        self,
    ) -> int:
        return self._queue.qsize()
