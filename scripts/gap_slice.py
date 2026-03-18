#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Gap:
    gap_id: str
    title: str
    body: str
    upstream_owner: str
    status: str
    current_behavior: str
    telemetry_gap: str
    dashboard_gap: str


GAP_RE = re.compile(r"^### (GAP-\d+): (.+)$", re.MULTILINE)
GAP_ID_RE = re.compile(r"\bGAP-\d+\b")
FIELD_RE = re.compile(r"^- `([^`]+)`: (.+)$", re.MULTILINE)


def parse_gaps(text: str) -> list[Gap]:
    matches = list(GAP_RE.finditer(text))
    gaps: list[Gap] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        fields = {field: normalize(value) for field, value in FIELD_RE.findall(body)}
        gaps.append(
            Gap(
                gap_id=match.group(1),
                title=match.group(2),
                body=body,
                upstream_owner=fields.get("Upstream owner", ""),
                status=fields.get("Status", ""),
                current_behavior=fields.get("Current behavior", ""),
                telemetry_gap=fields.get("Telemetry gap", ""),
                dashboard_gap=fields.get("Dashboard gap", ""),
            )
        )
    return gaps


def normalize(value: str) -> str:
    return value.strip().strip("`").strip()


def render_slice(gaps: list[Gap], count: int, focus_ids: list[str]) -> str:
    eligible = [
        gap
        for gap in gaps
        if gap.status in {"open", "partial"} and gap.upstream_owner in {"model-runner", "shared"}
    ]
    focused = [gap for gap in eligible if gap.gap_id in focus_ids]
    unfocused = [gap for gap in eligible if gap.gap_id not in focus_ids]
    selected = sorted(focused, key=priority_key)[:count]
    if len(selected) < count:
        selected.extend(sorted(unfocused, key=priority_key)[: count - len(selected)])

    lines = [
        "# Current Gap Slice",
        "",
        "This file is generated from `docs/gap_ledger.md`.",
        "It is the current upstream-facing work slice for `model-runner`.",
        "",
        "## Focus",
    ]

    if focus_ids:
        lines.extend(
            [
                "- Focus mode is active.",
                f"- Focused gap ids: {', '.join(f'`{gap_id}`' for gap_id in focus_ids)}",
                "- Eligible focused gaps are selected before the normal priority ranking.",
            ]
        )
    else:
        lines.extend(
            [
                "- No explicit focus ids.",
                "- Normal priority ranking is in effect.",
            ]
        )

    lines.extend(
        [
        "",
        "## Working rules",
        "- Fix these gaps in upstream telemetry truth or semantics before adding unrelated dashboard-facing changes.",
        "- If a gap cannot be fully closed, document the remaining limitation in the response file.",
        "- Preserve canonical event truth; do not normalize requested config into runtime fact.",
        "",
        f"## Selected gaps ({len(selected)})",
        ]
    )

    if not selected:
        lines.append("- No eligible upstream gaps found.")
        return "\n".join(lines) + "\n"

    for gap in selected:
        lines.extend(
            [
                "",
                f"### {gap.gap_id}: {gap.title}",
                gap.body,
            ]
        )

    lines.extend(
        [
            "",
            "## Expected response",
            "Write the upstream response in `docs/downstream/lab_llm/response.md` in `model-runner`.",
            "Include:",
            "- which gaps were addressed",
            "- which gaps were attempted but not closed",
            "- which gaps are blocked",
            "- what changed in telemetry/schema/emission",
            "- the exact verification run that exercised the telemetry change",
            "- any new fixture or sink evidence paths",
        ]
    )
    return "\n".join(lines) + "\n"


def priority_key(gap: Gap) -> tuple[int, int, int, int, int, int, str]:
    state = load_state()
    owner_score = 0 if gap.upstream_owner == "model-runner" else 1

    evidence_score = 0
    evidence_text = " ".join([gap.current_behavior, gap.telemetry_gap]).lower()
    if any(token in evidence_text for token in ["screenshot", "raw runtime", "raw data", "audited"]):
        evidence_score = -1

    truth_score = 1
    truth_text = " ".join([gap.title, gap.telemetry_gap, gap.current_behavior]).lower()
    if any(
        token in truth_text
        for token in [
            "model",
            "path",
            "source",
            "telemetry",
            "runtime truth",
            "configuration",
            "throughput",
            "tok/s",
            "gpu",
            "latency",
            "request",
        ]
    ):
        truth_score = 0

    blocked_score = state.get("blocked_counts", {}).get(gap.gap_id, 0)
    addressed_score = state.get("addressed_counts", {}).get(gap.gap_id, 0)
    recent_attempt_score = 0
    if gap.gap_id in state.get("last_attempted_gap_ids", []):
        recent_attempt_score += 2
    recent_attempt_score += min(state.get("attempt_counts", {}).get(gap.gap_id, 0), 3)

    return (
        owner_score,
        blocked_score,
        addressed_score,
        evidence_score,
        truth_score,
        recent_attempt_score,
        gap.gap_id,
    )


def load_state() -> dict[str, object]:
    path = Path("docs/coordination/state.json")
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_focus_ids(path: Path) -> list[str]:
    if not path.exists():
        return []

    seen: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = GAP_ID_RE.search(line)
        if not match:
            continue
        gap_id = match.group(0)
        if gap_id not in seen:
            seen.append(gap_id)
    return seen


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the current upstream gap slice.")
    parser.add_argument(
        "--gap-ledger",
        default="docs/gap_ledger.md",
        help="Path to the gap ledger markdown file.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Maximum number of upstream gaps to include.",
    )
    parser.add_argument(
        "--output",
        default="docs/coordination/current_gap_slice.md",
        help="Output markdown path.",
    )
    parser.add_argument(
        "--focus",
        default="docs/coordination/focus.txt",
        help="Optional focus file listing gap ids to prioritize.",
    )
    args = parser.parse_args()

    text = Path(args.gap_ledger).read_text(encoding="utf-8")
    focus_ids = load_focus_ids(Path(args.focus))
    rendered = render_slice(parse_gaps(text), args.count, focus_ids)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
