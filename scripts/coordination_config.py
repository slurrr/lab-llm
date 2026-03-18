#!/usr/bin/env python3
from __future__ import annotations

import argparse
import tomllib
from pathlib import Path

DEFAULTS_PATH = Path("docs/coordination.defaults.toml")
EXAMPLE_DEFAULTS_PATH = Path("docs/coordination.defaults.example.toml")


def resolve_default_config_path() -> Path:
    if DEFAULTS_PATH.exists():
        return DEFAULTS_PATH
    return EXAMPLE_DEFAULTS_PATH


def main() -> None:
    parser = argparse.ArgumentParser(description="Read a coordination config value.")
    parser.add_argument("key", help="Top-level TOML key to print.")
    parser.add_argument(
        "--config",
        default=str(resolve_default_config_path()),
        help="Path to the TOML config file.",
    )
    args = parser.parse_args()

    data = tomllib.loads(Path(args.config).read_text(encoding="utf-8"))
    value = data.get(args.key)
    if value is None:
        raise SystemExit(f"missing config key: {args.key}")
    print(value)


if __name__ == "__main__":
    main()
