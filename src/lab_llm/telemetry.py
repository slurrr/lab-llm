from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TelemetryEvent:
    schema_version: str
    event_type: str
    event_id: str
    ts: str
    session_id: str
    payload: dict[str, Any]
    experiment_id: str | None = None
    backend_name: str | None = None
    resolved_model_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TelemetryEvent":
        required = [
            "schema_version",
            "event_type",
            "event_id",
            "ts",
            "session_id",
            "payload",
        ]
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"missing telemetry event field(s): {', '.join(sorted(missing))}")
        payload = data["payload"]
        if not isinstance(payload, dict):
            raise ValueError("telemetry event payload must be an object")

        return cls(
            schema_version=str(data["schema_version"]),
            event_type=str(data["event_type"]),
            event_id=str(data["event_id"]),
            ts=str(data["ts"]),
            session_id=str(data["session_id"]),
            payload=payload,
            experiment_id=_optional_str(data.get("experiment_id")),
            backend_name=_optional_str(data.get("backend_name")),
            resolved_model_id=_optional_str(data.get("resolved_model_id")),
        )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
