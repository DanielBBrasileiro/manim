#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from core.runtime.artifact_parity_audit import run_artifact_parity_audit


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit de paridade entre artifact_plan e outputs")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = run_artifact_parity_audit()
    if args.json:
        print(json.dumps({"ok": result.ok, "errors": list(result.errors), "warnings": list(result.warnings), "stats": result.stats}, indent=2, ensure_ascii=True))
        return 0

    print(result.to_markdown())
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
