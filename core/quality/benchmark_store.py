from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
BENCHMARK_RUNS_DIR = ROOT / "core" / "memory" / "benchmark_runs"


def benchmark_runs_dir() -> Path:
    BENCHMARK_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    return BENCHMARK_RUNS_DIR


def create_run_id(prefix: str = "bench") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}_{stamp}"


def save_benchmark_run(report: dict[str, Any], run_id: str | None = None) -> Path:
    payload = dict(report)
    resolved_run_id = str(run_id or payload.get("run_id") or create_run_id()).strip()
    payload["run_id"] = resolved_run_id
    target = benchmark_runs_dir() / f"{resolved_run_id}.json"
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return target


def load_benchmark_run(run_ref: str) -> dict[str, Any]:
    raw = Path(run_ref)
    if raw.exists():
        return json.loads(raw.read_text(encoding="utf-8"))

    candidate = benchmark_runs_dir() / f"{run_ref}.json"
    if candidate.exists():
        return json.loads(candidate.read_text(encoding="utf-8"))

    raise FileNotFoundError(f"Benchmark run not found: {run_ref}")
