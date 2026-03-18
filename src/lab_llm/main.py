from __future__ import annotations

import argparse
from pathlib import Path

from lab_llm.fixtures import load_events_from_jsonl
from lab_llm.live import EventBroadcaster, FixtureReplayer, IngestionMonitor, JsonlTailer
from lab_llm.server import run_server
from lab_llm.store import DashboardStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the lab-llm dashboard.")
    parser.add_argument(
        "--fixtures",
        default="fixtures/telemetry/sample_session.jsonl",
        help="Path to JSONL telemetry fixture data.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="HTTP host to bind.")
    parser.add_argument("--port", type=int, default=8001, help="HTTP port to bind.")
    parser.add_argument(
        "--telemetry-jsonl",
        help="Path to a model-runner telemetry JSONL sink to ingest.",
    )
    parser.add_argument(
        "--replay-fixtures",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Replay fixture events over time for live dashboard updates.",
    )
    parser.add_argument(
        "--replay-speed",
        type=float,
        default=20.0,
        help="Speed multiplier for fixture replay timing.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    store = DashboardStore()
    broadcaster = EventBroadcaster()

    if args.telemetry_jsonl:
        monitor = IngestionMonitor(mode="jsonl", source=args.telemetry_jsonl)
        tailer = JsonlTailer(
            args.telemetry_jsonl, store, broadcaster, monitor=monitor, read_existing=True
        )
        tailer.start()
    else:
        monitor = IngestionMonitor(mode="fixture", source=args.fixtures)
        fixture_path = Path(args.fixtures)
        events = load_events_from_jsonl(fixture_path)
        if args.replay_fixtures:
            FixtureReplayer(
                events, store, broadcaster, monitor=monitor, speed=args.replay_speed
            ).start()
        else:
            for event in events:
                store.ingest(event)
                monitor.record_event(event)
    run_server(args.host, args.port, store, broadcaster, monitor)


if __name__ == "__main__":
    main()
