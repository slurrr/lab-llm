from __future__ import annotations

import json
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from lab_llm.fixtures import parse_jsonl_line
from lab_llm.store import DashboardStore
from lab_llm.telemetry import TelemetryEvent


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass
class IngestionStatus:
    mode: str
    source: str
    connected: bool = False
    last_event_ts: str | None = None
    last_event_id: str | None = None
    parse_error_count: int = 0
    last_error: str | None = None


class IngestionMonitor:
    def __init__(self, *, mode: str, source: str) -> None:
        self._status = IngestionStatus(mode=mode, source=source)
        self._lock = threading.Lock()

    def mark_connected(self, connected: bool) -> None:
        with self._lock:
            self._status.connected = connected

    def record_event(self, event: TelemetryEvent) -> None:
        with self._lock:
            self._status.connected = True
            self._status.last_event_ts = event.ts
            self._status.last_event_id = event.event_id
            self._status.last_error = None

    def record_error(self, message: str) -> None:
        with self._lock:
            self._status.last_error = message
            self._status.parse_error_count += 1

    def snapshot(self) -> dict[str, str | int | bool | None]:
        with self._lock:
            return {
                "mode": self._status.mode,
                "source": self._status.source,
                "connected": self._status.connected,
                "last_event_ts": self._status.last_event_ts,
                "last_event_id": self._status.last_event_id,
                "parse_error_count": self._status.parse_error_count,
                "last_error": self._status.last_error,
            }


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
        monitor: IngestionMonitor | None = None,
        *,
        speed: float = 20.0,
    ) -> None:
        self._events = list(events)
        self._store = store
        self._broadcaster = broadcaster
        self._monitor = monitor
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
            if self._monitor is not None:
                self._monitor.record_event(event)
            previous = current


class JsonlTailer:
    def __init__(
        self,
        path: str | Path,
        store: DashboardStore,
        broadcaster: EventBroadcaster,
        monitor: IngestionMonitor | None = None,
        *,
        poll_interval: float = 0.5,
        read_existing: bool = True,
    ) -> None:
        self._path = Path(path)
        self._store = store
        self._broadcaster = broadcaster
        self._monitor = monitor
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
                if self._monitor is not None:
                    self._monitor.mark_connected(False)
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
                    try:
                        event = parse_jsonl_line(line, str(self._path))
                    except ValueError as exc:
                        if self._monitor is not None:
                            self._monitor.record_error(str(exc))
                        continue
                    self._store.ingest(event)
                    self._broadcaster.publish(event)
                    if self._monitor is not None:
                        self._monitor.record_event(event)

            time.sleep(self._poll_interval)
