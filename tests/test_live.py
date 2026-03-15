from __future__ import annotations

import json
import time
from pathlib import Path

from lab_llm.live import EventBroadcaster, JsonlTailer
from lab_llm.store import DashboardStore


def test_jsonl_tailer_ingests_existing_and_appended_events(tmp_path: Path) -> None:
    sink = tmp_path / "telemetry.jsonl"
    first = {
        "schema_version": "v1",
        "event_type": "session_started",
        "event_id": "evt_a",
        "ts": "2026-03-15T18:30:00.000Z",
        "session_id": "sess_live",
        "backend_name": "hf",
        "resolved_model_id": "Model-A",
        "payload": {
            "session_id": "sess_live",
            "started_at": "2026-03-15T18:30:00.000Z",
            "ended_at": None,
            "status": "running",
            "backend_name": "hf",
            "transport_name": "inproc",
            "resolved_model_id": "Model-A",
            "config_path": "models/Model-A/hf/config/default.toml",
            "profile_name": "default",
        },
    }
    second = {
        "schema_version": "v1",
        "event_type": "turn_finished",
        "event_id": "evt_b",
        "ts": "2026-03-15T18:30:01.000Z",
        "session_id": "sess_live",
        "payload": {
            "session_id": "sess_live",
            "turn_id": 1,
            "started_at": "2026-03-15T18:30:00.100Z",
            "ended_at": "2026-03-15T18:30:01.000Z",
            "streaming_enabled": True,
            "completion_tokens": 42,
        },
    }
    sink.write_text(json.dumps(first) + "\n", encoding="utf-8")

    store = DashboardStore()
    broadcaster = EventBroadcaster()
    subscriber = broadcaster.subscribe()
    tailer = JsonlTailer(sink, store, broadcaster, poll_interval=0.05)
    tailer.start()
    try:
        time.sleep(0.15)
        with sink.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(second) + "\n")
        delivered = subscriber.get(timeout=1)
        assert delivered.event_id == "evt_a"
        delivered = subscriber.get(timeout=1)
        assert delivered.event_id == "evt_b"
        detail = store.get_session_detail("sess_live")
        assert detail is not None
        assert detail["recent_turns"][0]["completion_tokens"] == 42
    finally:
        tailer.stop()
        broadcaster.unsubscribe(subscriber)
