#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from core.intelligence.model_capabilities import refresh_model_capabilities
from core.intelligence.model_profiles import get_active_profile_name, get_profile, available_profiles
from core.intelligence.model_router import TASK_FAST_PLAN, TASK_PLAN, TASK_QUALITY_PLAN, TASK_VISION_PLAN
from core.runtime.capability_registry import build_capability_registry
from core.intelligence.ollama_client import generate_scene_plan
from core.runtime.capability_pool import build_capability_pool
from core.runtime.model_runtime import build_runtime_os_report


@contextmanager
def _temporary_profile(name: str) -> Iterator[None]:
    previous = os.environ.get("AIOX_MODEL_PROFILE")
    os.environ["AIOX_MODEL_PROFILE"] = name
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("AIOX_MODEL_PROFILE", None)
        else:
            os.environ["AIOX_MODEL_PROFILE"] = previous


def _run_planning_benchmark(prompt: str, iterations: int, task_roles: list[str]) -> dict[str, dict]:
    registry = json.loads((ROOT / "assets" / "registry.json").read_text(encoding="utf-8"))
    summaries: dict[str, dict] = {}
    for task_role in task_roles:
        latencies = []
        confidences = []
        successes = 0
        fallback_hits = 0
        for _ in range(iterations):
            plan, metadata = generate_scene_plan(prompt, asset_registry=registry, task_type=task_role, return_metadata=True)
            if plan is not None:
                successes += 1
                confidences.append(plan.confidence)
            if metadata.get("latency_ms") is not None:
                latencies.append(float(metadata["latency_ms"]))
            if metadata.get("fallback_used"):
                fallback_hits += 1
        summaries[task_role] = {
            "iterations": iterations,
            "successes": successes,
            "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else None,
            "avg_confidence": round(statistics.mean(confidences), 4) if confidences else None,
            "fallback_hits": fallback_hits,
        }
    return summaries


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark do runtime local AIOX")
    parser.add_argument("--prompt", default="quero algo com silencio, tensao e resolucao elegante")
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument(
        "--profiles",
        nargs="+",
        default=[get_active_profile_name()],
        choices=sorted(available_profiles().keys()),
    )
    parser.add_argument(
        "--task-roles",
        nargs="+",
        default=[TASK_FAST_PLAN, TASK_PLAN, TASK_QUALITY_PLAN],
        choices=list(build_capability_registry().model_roles),
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--disable-cache", action="store_true")
    args = parser.parse_args(argv)

    if args.disable_cache:
        os.environ["AIOX_LLM_ENABLE_CACHE"] = "0"

    refresh_model_capabilities()
    registry = build_capability_registry()
    results = []
    for profile_name in args.profiles:
        with _temporary_profile(profile_name):
            profile = get_profile(profile_name)
            planning = _run_planning_benchmark(args.prompt, args.iterations, args.task_roles)
            results.append(
                {
                    "profile": profile.name,
                    "provider": profile.provider,
                    "render_preferences": profile.render_preferences,
                    "planning": planning,
                    "targets": [entry["id"] for entry in registry.targets],
                    "runtime_os": build_runtime_os_report(profile.name),
                    "capability_pool": build_capability_pool(),
                }
            )

    if args.json:
        print(json.dumps({"results": results}, indent=2, ensure_ascii=True))
        return 0

    for result in results:
        print(f"\n=== {result['profile']} ===")
        for task_role, summary in result["planning"].items():
            print(
                f"- {task_role}: successes={summary['successes']}/{summary['iterations']} "
                f"latency_ms={summary['avg_latency_ms']} confidence={summary['avg_confidence']} "
                f"fallback_hits={summary['fallback_hits']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
