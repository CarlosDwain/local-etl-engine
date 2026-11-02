"""ProgressReporter that publishes events for a polling UI."""

from queue import Queue


class QueueReporter:
    def __init__(self, events: Queue[tuple[str, float]]) -> None:
        self._events = events

    def update(self, step: str, fraction: float) -> None:
        self._events.put((step, fraction))
