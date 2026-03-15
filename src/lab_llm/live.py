from __future__ import annotations

import json
import queue
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable

from lab_llm.fixtures import parse_jsonl_line
from lab_llm.store import DashboardStore
from lab_llm.telemetry import TelemetryEvent


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class EventBroadcaster:
    def __init__(self) -> None:
        self._queues: set[queue.Queue[TelemetryEvent | None]] = set()
        self._lock = threading.Lock()

    def subscribe(self) -> queue.Queue[TelemetryEvent | None]:
        subscriber: queue.Queue[TelemetryEvent | None] = queue.Queue()
        with self._lock:
            self._queues.add(subscriber)
        return subscriber

    def unsubscribe(self, subscriber: queue.Queue[TelemetryEvent | None]) -> None:
        with self._lock:
            self._queues.discard(subscriber)

    def publish(self, event: TelemetryEvent) -> None:
        with self._lock:
            subscribers = list(self._queues)
        for subscriber in subscribers:
            subscriber.put(event)


def format_sse_event(event: TelemetryEvent) -> bytes:
    # Keep canonical IDs in the app-facing live stream; only Prometheus label surfaces
    # should drop high-cardinality identifiers by default.
    body = {
        "schema_version": event.schema_version,
        "event_id": event.event_id,
        "ts": event.ts,
        "session_id": event.session_id,
        "backend_name": event.backend_name,
        "resolved_model_id": event.resolved_model_id,
        "experiment_id": event.experiment_id,
        "payload": event.payload,
    }
    return f"event: {event.event_type}\ndata: {json.dumps(body)}\n\n".encode("utf-8")


class FixtureReplayer:
    def __init__(
        self,
        events: Iterable[TelemetryEvent],
        store: DashboardStore,
        broadcaster: EventBroadcaster,
        *,
        speed: float = 20.0,
    ) -> None:
        self._events = list(events)
        self._store = store
        self._broadcaster = broadcaster
        self._speed = max(speed, 0.1)
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        previous: datetime | None = None
        for event in self._events:
            current = _parse_ts(event.ts)
            if previous is not None:
                delay = max((current - previous).total_seconds() / self._speed, 0.0)
                if delay > 0:
                    time.sleep(delay)
            self._store.ingest(event)
            self._broadcaster.publish(event)
            previous = current


class JsonlTailer:
    def __init__(
        self,
        path: str | Path,
        store: DashboardStore,
        broadcaster: EventBroadcaster,
        *,
        poll_interval: float = 0.5,
        read_existing: bool = True,
    ) -> None:
        self._path = Path(path)
        self._store = store
        self._broadcaster = broadcaster
        self._poll_interval = poll_interval
        self._read_existing = read_existing
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        offset = 0
        if not self._read_existing and self._path.exists():
            offset = self._path.stat().st_size

        while not self._stop.is_set():
            if not self._path.exists():
                time.sleep(self._poll_interval)
                continue

            current_size = self._path.stat().st_size
            if current_size < offset:
                offset = 0

            if current_size == offset:
                time.sleep(self._poll_interval)
                continue

            with self._path.open("r", encoding="utf-8") as handle:
                handle.seek(offset)
                while True:
                    raw_line = handle.readline()
                    if raw_line == "":
                        break
                    line = raw_line.strip()
                    offset = handle.tell()
                    if not line:
                        continue
                    # model-runner JSONL framing is expected to be one event envelope per line.
                    event = parse_jsonl_line(line, str(self._path))
                    self._store.ingest(event)
                    self._broadcaster.publish(event)

            time.sleep(self._poll_interval)
