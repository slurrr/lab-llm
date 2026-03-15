from __future__ import annotations

from copy import deepcopy
from threading import Lock
from typing import Any

from lab_llm.telemetry import TelemetryEvent


class DashboardStore:
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def ingest(self, event: TelemetryEvent) -> None:
        with self._lock:
            session = self._sessions.setdefault(
                event.session_id,
                {
                    "session": {
                        "session_id": event.session_id,
                        "status": "running",
                        "backend_name": event.backend_name,
                        "resolved_model_id": event.resolved_model_id,
                        "started_at": None,
                        "ended_at": None,
                        "last_event_at": event.ts,
                        "has_errors": False,
                    },
                    "load_report": None,
                    "latest_runtime": None,
                    "runtime_history": [],
                    "recent_turns": [],
                    "recent_logs": [],
                    "inspect": {
                        "load_truth": None,
                        "generation_truth": None,
                        "backend_extensions": {},
                    },
                    "errors": [],
                },
            )

            session["session"]["last_event_at"] = event.ts
            if event.backend_name and not session["session"].get("backend_name"):
                session["session"]["backend_name"] = event.backend_name
            if event.resolved_model_id and not session["session"].get("resolved_model_id"):
                session["session"]["resolved_model_id"] = event.resolved_model_id

            handlers = {
                "session_started": self._handle_session_started,
                "load_reported": self._handle_load_reported,
                "turn_finished": self._handle_turn_finished,
                "runtime_sample": self._handle_runtime_sample,
                "log_recorded": self._handle_log_recorded,
                "error_reported": self._handle_error_reported,
                "session_finished": self._handle_session_finished,
            }
            handler = handlers.get(event.event_type)
            if handler is not None:
                handler(session, event)

    def list_sessions(self) -> list[dict[str, Any]]:
        with self._lock:
            items = [deepcopy(session["session"]) for session in self._sessions.values()]
        items.sort(key=lambda item: item["last_event_at"] or "", reverse=True)
        return items

    def get_session_detail(self, session_id: str) -> dict[str, Any] | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            return {
                "session": deepcopy(session["session"]),
                "load_report": deepcopy(session["load_report"]),
                "latest_runtime": deepcopy(session["latest_runtime"]),
                "runtime_history": deepcopy(session["runtime_history"]),
                "recent_turns": deepcopy(session["recent_turns"]),
                "recent_logs": deepcopy(session["recent_logs"]),
                "inspect": deepcopy(session["inspect"]),
            }

    def get_session_turns(self, session_id: str) -> list[dict[str, Any]] | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            return deepcopy(session["recent_turns"])

    def get_session_logs(self, session_id: str) -> list[dict[str, Any]] | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            return deepcopy(session["recent_logs"])

    def get_session_inspect(self, session_id: str) -> dict[str, Any] | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            return deepcopy(session["inspect"])

    def _handle_session_started(self, session: dict[str, Any], event: TelemetryEvent) -> None:
        payload = event.payload
        session_state = session["session"]
        session_state.update(
            {
                "session_id": payload.get("session_id", event.session_id),
                "status": payload.get("status", "running"),
                "backend_name": payload.get("backend_name", session_state.get("backend_name")),
                "resolved_model_id": payload.get(
                    "resolved_model_id", session_state.get("resolved_model_id")
                ),
                "started_at": payload.get("started_at", event.ts),
                "ended_at": payload.get("ended_at"),
            }
        )

    def _handle_load_reported(self, session: dict[str, Any], event: TelemetryEvent) -> None:
        session["load_report"] = deepcopy(event.payload)
        session["inspect"]["load_truth"] = deepcopy(event.payload)
        extension = event.payload.get("extension")
        if isinstance(extension, dict):
            session["inspect"]["backend_extensions"]["load_report"] = deepcopy(extension)

    def _handle_turn_finished(self, session: dict[str, Any], event: TelemetryEvent) -> None:
        payload = deepcopy(event.payload)
        session["recent_turns"].append(payload)
        session["recent_turns"].sort(key=lambda item: item.get("turn_id", 0), reverse=True)
        session["recent_turns"] = session["recent_turns"][:20]
        session["inspect"]["generation_truth"] = deepcopy(payload.get("knobs"))
        extension = payload.get("extension")
        if isinstance(extension, dict):
            session["inspect"]["backend_extensions"]["turn_finished"] = deepcopy(extension)

    def _handle_runtime_sample(self, session: dict[str, Any], event: TelemetryEvent) -> None:
        payload = deepcopy(event.payload)
        session["latest_runtime"] = payload
        session["runtime_history"].append(payload)
        session["runtime_history"] = session["runtime_history"][-180:]
        extension = event.payload.get("extension")
        if isinstance(extension, dict):
            session["inspect"]["backend_extensions"]["runtime_sample"] = deepcopy(extension)

    def _handle_log_recorded(self, session: dict[str, Any], event: TelemetryEvent) -> None:
        session["recent_logs"].append(deepcopy(event.payload))
        session["recent_logs"] = session["recent_logs"][-200:]

    def _handle_error_reported(self, session: dict[str, Any], event: TelemetryEvent) -> None:
        session["errors"].append(deepcopy(event.payload))
        session["session"]["has_errors"] = True
        session["session"]["status"] = "error"

    def _handle_session_finished(self, session: dict[str, Any], event: TelemetryEvent) -> None:
        payload = event.payload
        session["session"]["status"] = payload.get("status", "finished")
        session["session"]["ended_at"] = payload.get("ended_at", event.ts)
