from __future__ import annotations

import json
from pathlib import Path

from lab_llm.telemetry import TelemetryEvent


def load_events_from_jsonl(path: str | Path) -> list[TelemetryEvent]:
    fixture_path = Path(path)
    events: list[TelemetryEvent] = []
    for line_number, raw_line in enumerate(fixture_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"invalid JSON on line {line_number} in {fixture_path}"
            ) from exc
        events.append(TelemetryEvent.from_dict(payload))
    return events


def parse_jsonl_line(line: str, source: str = "<stream>") -> TelemetryEvent:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {source}") from exc
    return TelemetryEvent.from_dict(payload)
