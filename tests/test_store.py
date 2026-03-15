from pathlib import Path

from lab_llm.fixtures import load_events_from_jsonl
from lab_llm.store import DashboardStore


def test_store_builds_read_models_from_fixture() -> None:
    fixture_path = Path("fixtures/telemetry/sample_session.jsonl")
    events = load_events_from_jsonl(fixture_path)

    store = DashboardStore()
    for event in events:
        store.ingest(event)

    sessions = store.list_sessions()
    assert len(sessions) == 1
    assert sessions[0]["session_id"] == "sess_001"
    assert sessions[0]["status"] == "finished"

    detail = store.get_session_detail("sess_001")
    assert detail is not None
    assert detail["load_report"]["engine_name"] == "transformers"
    assert len(detail["runtime_history"]) == 2
    assert detail["recent_turns"][0]["completion_tokens"] == 109
    assert detail["inspect"]["generation_truth"]["sent"]["temperature"] == 0.7
