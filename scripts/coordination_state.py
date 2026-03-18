#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_PATH = Path("docs/coordination/state.json")
HEADING_RE = re.compile(r"^## (.+)$", re.MULTILINE)
GAP_ID_RE = re.compile(r"\bGAP-\d+\b")
VERIFIED_SESSION_RE = re.compile(r"Verified session id:\s*\n\s*-\s*`([^`]+)`")


def default_state() -> dict[str, Any]:
    return {
        "selected_gap_ids": [],
        "previous_selected_gap_ids": [],
        "attempt_counts": {},
        "blocked_counts": {},
        "addressed_counts": {},
        "last_attempted_gap_ids": [],
        "last_blocked_gap_ids": [],
        "last_addressed_gap_ids": [],
        "last_response_addressed_gap_ids": [],
        "last_response_path": None,
        "last_reconciled_at": None,
        "previous_verified_session_id": None,
        "last_verified_session_id": None,
        "last_audited_session_id": None,
        "last_audit_detail_hash": None,
        "last_session_selection_source": None,
        "last_loop_stop_reason": None,
    }


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return default_state()
    state = default_state()
    state.update(json.loads(path.read_text(encoding="utf-8")))
    return state


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_slice_gap_ids(text: str) -> list[str]:
    seen: list[str] = []
    for gap_id in GAP_ID_RE.findall(text):
        if gap_id not in seen:
            seen.append(gap_id)
    return seen


def parse_sections(text: str) -> dict[str, str]:
    matches = list(HEADING_RE.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1).strip().lower()] = text[start:end].strip()
    return sections


def ids_from_sections(sections: dict[str, str], names: tuple[str, ...]) -> list[str]:
    seen: list[str] = []
    for name in names:
        body = sections.get(name, "")
        for gap_id in GAP_ID_RE.findall(body):
            if gap_id not in seen:
                seen.append(gap_id)
    return seen


def extract_verified_session_id(text: str) -> str | None:
    match = VERIFIED_SESSION_RE.search(text)
    return match.group(1) if match else None


def record_selection(state_path: Path, slice_path: Path) -> None:
    state = load_state(state_path)
    gap_ids = parse_slice_gap_ids(slice_path.read_text(encoding="utf-8"))
    attempt_counts = defaultdict(int, state.get("attempt_counts", {}))
    for gap_id in gap_ids:
        attempt_counts[gap_id] += 1
    state["previous_selected_gap_ids"] = state.get("selected_gap_ids", [])
    state["selected_gap_ids"] = gap_ids
    state["last_attempted_gap_ids"] = gap_ids
    state["attempt_counts"] = dict(attempt_counts)
    state["last_reconciled_at"] = now_iso()
    save_state(state_path, state)


def record_response(state_path: Path, response_path: Path) -> None:
    state = load_state(state_path)
    text = response_path.read_text(encoding="utf-8")
    sections = parse_sections(text)
    addressed = ids_from_sections(sections, ("addressed gaps",))
    attempted = ids_from_sections(
        sections,
        (
            "addressed gaps",
            "gaps attempted but not closed",
            "attempted gaps",
            "remaining blockers",
        ),
    )
    blocked = ids_from_sections(sections, ("gaps blocked", "remaining blockers"))

    blocked_counts = defaultdict(int, state.get("blocked_counts", {}))
    addressed_counts = defaultdict(int, state.get("addressed_counts", {}))
    for gap_id in blocked:
        blocked_counts[gap_id] += 1
    for gap_id in addressed:
        addressed_counts[gap_id] += 1

    state["last_attempted_gap_ids"] = attempted
    state["last_blocked_gap_ids"] = blocked
    state["last_addressed_gap_ids"] = addressed
    state["last_response_addressed_gap_ids"] = addressed
    state["blocked_counts"] = dict(blocked_counts)
    state["addressed_counts"] = dict(addressed_counts)
    state["last_response_path"] = str(response_path)
    state["previous_verified_session_id"] = state.get("last_verified_session_id")
    state["last_verified_session_id"] = extract_verified_session_id(text)
    state["last_reconciled_at"] = now_iso()
    save_state(state_path, state)


def record_audit(state_path: Path, meta_path: Path) -> None:
    state = load_state(state_path)
    meta: dict[str, str] = {}
    for line in meta_path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            meta[key] = value

    detail_hash = None
    detail_path = meta.get("detail_path")
    if detail_path and Path(detail_path).exists():
        detail_hash = hashlib.sha256(Path(detail_path).read_bytes()).hexdigest()

    state["last_audited_session_id"] = meta.get("session_id")
    state["last_audit_detail_hash"] = detail_hash
    state["last_session_selection_source"] = meta.get("session_selection_source")
    state["last_reconciled_at"] = now_iso()
    save_state(state_path, state)


def check_loop_stop(state_path: Path) -> None:
    state = load_state(state_path)
    selected = state.get("selected_gap_ids", [])
    previous = state.get("previous_selected_gap_ids", [])
    addressed = state.get("last_response_addressed_gap_ids", [])
    previous_verified = state.get("previous_verified_session_id")
    verified = state.get("last_verified_session_id")
    audited = state.get("last_audited_session_id")

    reason: str | None = None
    if addressed and not verified:
        reason = "missing-verified-session-id"
    elif addressed and previous_verified and verified == previous_verified:
        reason = f"verified-session-not-fresh:{verified}"
    elif verified and audited and verified != audited:
        reason = f"audit-session-mismatch:{audited}:expected:{verified}"
    elif selected and previous and selected == previous and not addressed:
        reason = "no-progress-same-slice-reselected"

    state["last_loop_stop_reason"] = reason
    save_state(state_path, state)
    if reason:
        print(reason)
        raise SystemExit(10)


def main() -> None:
    parser = argparse.ArgumentParser(description="Maintain coordination loop state.")
    parser.add_argument("--state", default=str(STATE_PATH), help="Path to the state JSON file.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    selection_parser = subparsers.add_parser("record-selection", help="Record a selected gap slice.")
    selection_parser.add_argument("--slice", default="docs/coordination/current_gap_slice.md")

    response_parser = subparsers.add_parser("record-response", help="Record an upstream response.")
    response_parser.add_argument("--response", default="docs/coordination/inbox/response.md")

    audit_parser = subparsers.add_parser("record-audit", help="Record the latest audit metadata.")
    audit_parser.add_argument("--meta", required=True)

    subparsers.add_parser("check-loop-stop", help="Exit non-zero if the loop should stop.")

    args = parser.parse_args()
    state_path = Path(args.state)

    if args.command == "record-selection":
        record_selection(state_path, Path(args.slice))
    elif args.command == "record-response":
        record_response(state_path, Path(args.response))
    elif args.command == "record-audit":
        record_audit(state_path, Path(args.meta))
    elif args.command == "check-loop-stop":
        check_loop_stop(state_path)
    else:
        raise SystemExit(f"unknown command: {args.command}")


if __name__ == "__main__":
    main()
