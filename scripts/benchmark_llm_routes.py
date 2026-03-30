#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.intelligence.model_router import TASK_FAST_PLAN, TASK_PLAN, TASK_QUALITY_PLAN
from core.intelligence.ollama_client import generate_scene_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark leve do roteamento LLM local")
    parser.add_argument(
        "--prompt",
        default="quero algo que respire, com evolucao elegante, tensao controlada e resolucao limpa",
    )
    parser.add_argument("--iterations", type=int, default=2)
    parser.add_argument(
        "--task-types",
        nargs="+",
        default=[TASK_FAST_PLAN, TASK_PLAN, TASK_QUALITY_PLAN],
        choices=[TASK_FAST_PLAN, TASK_PLAN, TASK_QUALITY_PLAN],
    )
    parser.add_argument("--disable-cache", action="store_true")
    args = parser.parse_args()

    if args.disable_cache:
        os.environ["AIOX_LLM_ENABLE_CACHE"] = "0"

    registry = json.loads((ROOT / "assets" / "registry.json").read_text(encoding="utf-8"))

    for task_type in args.task_types:
        latencies = []
        confidences = []
        cache_hits = 0
        fallback_hits = 0
        successes = 0

        print(f"\n=== {task_type} ===")
        for idx in range(args.iterations):
            plan, metadata = generate_scene_plan(
                args.prompt,
                asset_registry=registry,
                task_type=task_type,
                return_metadata=True,
            )
            print(json.dumps({"iteration": idx + 1, "metadata": metadata}, ensure_ascii=True))
            if metadata.get("latency_ms") is not None:
                latencies.append(metadata["latency_ms"])
            if metadata.get("from_cache"):
                cache_hits += 1
            if metadata.get("fallback_used"):
                fallback_hits += 1
            if plan is not None:
                successes += 1
                confidences.append(plan.confidence)

        summary = {
            "task_type": task_type,
            "iterations": args.iterations,
            "successes": successes,
            "cache_hits": cache_hits,
            "fallback_hits": fallback_hits,
            "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else None,
            "avg_confidence": round(statistics.mean(confidences), 4) if confidences else None,
        }
        print(json.dumps(summary, ensure_ascii=True, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
