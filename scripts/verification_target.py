#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from coordination_config import DEFAULTS_PATH

GAP_ID_RE = re.compile(r"\bGAP-\d+\b")


def read_config(path: Path) -> dict[str, str | int]:
    import tomllib

    return tomllib.loads(path.read_text(encoding="utf-8"))


def infer_from_jsonl_path(path: Path) -> tuple[str, str, str]:
    parts = path.parts
    backend = "unknown"
    model_name = path.stem
    model_path = str(path)
    if "models" in parts:
        index = parts.index("models")
        if index + 1 < len(parts):
            model_name = parts[index + 1]
            model_path = str(Path(*parts[: index + 2]))
        if index + 2 < len(parts):
            backend = parts[index + 2]
    return model_name, backend, model_path


def infer_backend_override(slice_text: str, fallback: str) -> str:
    lowered = slice_text.lower()
    for backend in ("vllm", "sglang", "trtllm", "llama.cpp", "hf"):
        if backend in lowered:
            return backend
    return fallback


def render_target(model_name: str, backend: str, model_path: str, telemetry_jsonl: str) -> str:
    return "\n".join(
        [
            "# Telemetry Verification Target",
            "",
            "Use this as the default verification target in `model-runner` when a gap slice changes telemetry behavior.",
            "",
            "## Default target",
            f"- `Model label`: `{model_name}`",
            f"- `Backend`: `{backend}`",
            f"- `Model path`: `{model_path}`",
            f"- `Telemetry sink`: `{telemetry_jsonl}`",
            "",
            "## Verification rule",
            "- If you changed telemetry schema, emission semantics, backend adapters, load/runtime/turn fields, or sink wiring, run a real model load plus at least one short generation before claiming success.",
            "- If the change affects model identity, startup, load-time truth, or runtime semantics, do not verify against a stale already-running process.",
            "- If the runnable path depends on a build/install step, rebuild from the latest source before starting the fresh verification run.",
            "- Capture a new session id from the fresh run; do not reuse a session produced before the code change.",
            "- Prefer the backend above unless the selected gaps are explicitly about a different backend and you can justify a closer target.",
            "- Record the exact fresh-code step, exact run command, backend, model, session id, and evidence path in `response.md`.",
            "- If no existing script cleanly supports the target, choose the narrowest existing runner/dev command that emits telemetry to the sink and explain the compromise.",
        ]
    ) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a telemetry verification target note.")
    parser.add_argument("--config", default=str(DEFAULTS_PATH), help="Path to the TOML defaults file.")
    parser.add_argument("--slice", default="docs/coordination/current_gap_slice.md", help="Current gap slice path.")
    parser.add_argument("--output", default="docs/coordination/verification_target.md", help="Output markdown path.")
    args = parser.parse_args()

    config = read_config(Path(args.config))
    telemetry_jsonl = str(config["telemetry_jsonl"])
    slice_text = Path(args.slice).read_text(encoding="utf-8") if Path(args.slice).exists() else ""
    model_name, backend, model_path = infer_from_jsonl_path(Path(telemetry_jsonl))
    backend = infer_backend_override(slice_text, backend)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_target(model_name=model_name, backend=backend, model_path=model_path, telemetry_jsonl=telemetry_jsonl),
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
