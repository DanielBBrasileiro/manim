#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from core.compiler.creative_compiler import compile_seed
from core.runtime.variant_ranker import rank_variants


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ranqueia variantes do artifact plan")
    parser.add_argument("briefing")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--heuristic", action="store_true", help="Pula o rankeamento via LLM e usa apenas heuristica local")
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        help="Override do timeout do variant ranker via LLM",
    )
    args = parser.parse_args(argv)

    with open(args.briefing, "r", encoding="utf-8") as handle:
        brief = yaml.safe_load(handle) or {}

    if args.heuristic:
        os.environ["AIOX_VARIANT_RANKER_DISABLE_LLM"] = "1"
    if args.timeout_seconds is not None:
        os.environ["AIOX_VARIANT_RANKER_TIMEOUT_SECONDS"] = str(max(1.0, float(args.timeout_seconds)))

    result = compile_seed(brief)
    artifact_plan = result.get("artifact_plan", {})
    ranking = rank_variants(artifact_plan)

    if args.json:
        print(json.dumps(ranking, indent=2, ensure_ascii=True))
        return 0

    print(f"Chosen variant: {ranking.get('chosen_variant')}")
    print(f"Reason: {ranking.get('chosen_variant_reason')}")
    for variant_id, payload in (ranking.get("variant_scores") or {}).items():
        print(f"- {variant_id}: {payload}")
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
