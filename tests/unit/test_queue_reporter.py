from queue import Queue

from etl.interfaces.cli.queue_reporter import QueueReporter


def test_queue_reporter_publishes_progress_event() -> None:
    events: Queue[tuple[str, float]] = Queue()

    QueueReporter(events).update("ingest", 0.25)

    assert events.get_nowait() == ("ingest", 0.25)
