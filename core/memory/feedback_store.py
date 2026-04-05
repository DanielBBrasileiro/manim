from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent


def save_training_pair(
    prompt: str,
    completion: dict[str, Any],
    approved: bool,
    metadata: dict[str, Any] | None = None,
    path: str | None = None,
) -> bool:
    if not approved or not prompt or not completion:
        return False

    target = Path(path) if path else ROOT / "core" / "memory" / "training_pairs.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "prompt": prompt,
        "completion": json.dumps(completion, ensure_ascii=True),
    }
    if metadata:
        row["metadata"] = metadata
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    return True


def save_decision_record(
    brief: dict[str, Any] | None,
    creative_plan: dict[str, Any] | None,
    artifact_plan: dict[str, Any] | None,
    chosen_variant: str,
    exported_targets: list[dict[str, Any]] | None,
    approved: bool,
    review_notes: list[str] | None = None,
    variants: list[dict[str, Any]] | None = None,
    runtime_profile: str | None = None,
    review_session_id: str | None = None,
    benchmark_metrics: dict[str, Any] | None = None,
    quality_report: dict[str, Any] | None = None,
    path: str | None = None,
) -> bool:
    if not approved:
        return False

    target = Path(path) if path else ROOT / "core" / "memory" / "decision_records.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "brief": brief or {},
        "creative_plan": creative_plan or {},
        "artifact_plan": artifact_plan or {},
        "variants": variants or [],
        "chosen_variant": chosen_variant,
        "exported_targets": exported_targets or [],
        "review_notes": review_notes or [],
        "runtime_profile": runtime_profile,
        "review_session_id": review_session_id,
        "benchmark_metrics": benchmark_metrics or {},
        "quality_report": quality_report or {},
    }
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=True) + "\n")
    return True
