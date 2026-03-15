from pathlib import Path

from lab_llm.fixtures import load_events_from_jsonl
from lab_llm.live import EventBroadcaster, format_sse_event
from lab_llm.server import resolve_api_payload
from lab_llm.store import DashboardStore


def test_api_resolution_serves_fixture_backed_session() -> None:
    store = DashboardStore()
    for event in load_events_from_jsonl(Path("fixtures/telemetry/sample_session.jsonl")):
        store.ingest(event)

    status, sessions = resolve_api_payload(store, "/api/sessions")
    assert int(status) == 200
    assert sessions["sessions"][0]["session_id"] == "sess_001"

    status, detail = resolve_api_payload(store, "/api/sessions/sess_001")
    assert int(status) == 200
    assert detail["session"]["backend_name"] == "hf"
    assert detail["load_report"]["context_length"] == 32768
    assert len(detail["runtime_history"]) == 2


def test_sse_event_format_contains_event_name_and_payload() -> None:
    event = load_events_from_jsonl(Path("fixtures/telemetry/sample_session.jsonl"))[0]
    payload = format_sse_event(event).decode("utf-8")
    assert "event: session_started" in payload
    assert '"session_id": "sess_001"' in payload


def test_broadcaster_delivers_published_events() -> None:
    event = load_events_from_jsonl(Path("fixtures/telemetry/sample_session.jsonl"))[0]
    broadcaster = EventBroadcaster()
    subscriber = broadcaster.subscribe()
    try:
        broadcaster.publish(event)
        delivered = subscriber.get(timeout=0.1)
    finally:
        broadcaster.unsubscribe(subscriber)
    assert delivered.event_id == event.event_id
