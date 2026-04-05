from __future__ import annotations

import json
import time
import uuid
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from core.runtime.execution_policy import ExecutionPolicy

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_RUN_DIR = ROOT / ".sessions" / "runtime_runs"


@dataclass
class StageMetric:
    started_at: float
    ended_at: float | None = None
    duration_ms: float = 0.0
    status: str = "running"
    details: dict[str, Any] = field(default_factory=dict)


class RunMetricsTracker:
    def __init__(self) -> None:
        self.run_started_at = time.time()
        self._monotonic_start = time.monotonic()
        self.stage_metrics: dict[str, StageMetric] = {}
        self.counters: dict[str, Any] = {}

    def start(self, stage: str) -> None:
        self.stage_metrics[stage] = StageMetric(started_at=time.time())

    def finish(self, stage: str, *, status: str = "ok", details: dict[str, Any] | None = None) -> dict[str, Any]:
        metric = self.stage_metrics.setdefault(stage, StageMetric(started_at=time.time()))
        metric.ended_at = time.time()
        metric.duration_ms = max(0.0, (metric.ended_at - metric.started_at) * 1000.0)
        metric.status = status
        if details:
            metric.details.update(details)
        return self.stage_dict(stage)

    def set_counter(self, key: str, value: Any) -> None:
        self.counters[key] = value

    def increment(self, key: str, value: int = 1) -> None:
        current = int(self.counters.get(key, 0) or 0)
        self.counters[key] = current + value

    def stage_dict(self, stage: str) -> dict[str, Any]:
        metric = self.stage_metrics.get(stage)
        if not metric:
            return {}
        return {
            "started_at": metric.started_at,
            "ended_at": metric.ended_at,
            "duration_ms": round(metric.duration_ms, 2),
            "status": metric.status,
            "details": deepcopy(metric.details),
        }

    def to_dict(self) -> dict[str, Any]:
        plan_duration = sum(
            self.stage_metrics.get(stage, StageMetric(0.0)).duration_ms
            for stage in ("interpret", "plan", "simulate")
        )
        preview_duration = self.stage_metrics.get("preview", StageMetric(0.0)).duration_ms
        render_duration = self.stage_metrics.get("render", StageMetric(0.0)).duration_ms
        judge_duration = self.stage_metrics.get("quality", StageMetric(0.0)).duration_ms
        persist_duration = self.stage_metrics.get("persist", StageMetric(0.0)).duration_ms
        total_duration_ms = max(0.0, (time.monotonic() - self._monotonic_start) * 1000.0)
        return {
            "planning_duration_ms": round(plan_duration, 2),
            "preview_duration_ms": round(preview_duration, 2),
            "render_duration_ms": round(render_duration, 2),
            "judge_duration_ms": round(judge_duration, 2),
            "persist_duration_ms": round(persist_duration, 2),
            "total_run_duration_ms": round(total_duration_ms, 2),
            "preview_iterations_used": int(self.counters.get("preview_iterations_used", 0) or 0),
            "error_count": int(self.counters.get("error_count", 0) or 0),
            "stages": {stage: self.stage_dict(stage) for stage in sorted(self.stage_metrics)},
        }


@dataclass(frozen=True)
class GovernedRunSummary:
    run_id: str
    session_id: str
    created_at: float
    updated_at: float
    source: str
    runtime_profile: str
    execution_mode: str
    policy: dict[str, Any]
    input_reference: dict[str, Any]
    style_pack: str
    targets: list[str]
    preview_loop_summary: dict[str, Any]
    judge_summary: dict[str, Any]
    benchmark_summary: dict[str, Any]
    final_status: str
    metrics: dict[str, Any]
    errors: list[str] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def ensure_runtime_governance_dirs() -> Path:
    DEFAULT_RUN_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_RUN_DIR


def create_governed_run_id(prefix: str = "run") -> str:
    return f"{prefix}_{int(time.time())}_{uuid.uuid4().hex[:8]}"


def save_governed_run(summary: GovernedRunSummary | dict[str, Any], directory: Path | None = None) -> Path:
    target_dir = directory or ensure_runtime_governance_dirs()
    payload = summary.to_dict() if isinstance(summary, GovernedRunSummary) else deepcopy(summary)
    run_id = str(payload.get("run_id") or create_governed_run_id()).strip()
    payload["run_id"] = run_id
    path = target_dir / f"{run_id}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return path


def load_governed_run(run_id: str, directory: Path | None = None) -> dict[str, Any]:
    target_dir = directory or ensure_runtime_governance_dirs()
    path = Path(run_id)
    if not path.exists():
        path = target_dir / f"{run_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def input_reference_from_seed(seed: dict[str, Any] | None) -> dict[str, Any]:
    seed = seed or {}
    creative_seed = seed.get("creative_seed", {}) if isinstance(seed.get("creative_seed", {}), dict) else {}
    title = str(creative_seed.get("title") or seed.get("title") or "").strip()
    prompt = str(seed.get("prompt") or creative_seed.get("thesis") or "").strip()
    return {
        "title": title,
        "prompt": prompt,
        "briefing_keys": sorted(seed.keys()) if isinstance(seed, dict) else [],
    }


def build_governed_run_summary(
    *,
    run_id: str,
    session_id: str,
    source: str,
    runtime_profile: str,
    execution_mode: str,
    policy: ExecutionPolicy,
    seed: dict[str, Any] | None = None,
    artifact_plan: dict[str, Any] | None = None,
    preview_loop_report: dict[str, Any] | None = None,
    quality_report: dict[str, Any] | None = None,
    benchmark_summary: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    final_status: str = "unknown",
    errors: list[str] | None = None,
    artifacts: dict[str, Any] | None = None,
) -> GovernedRunSummary:
    artifact_plan = artifact_plan or {}
    preview_loop_report = preview_loop_report or {}
    quality_report = quality_report or {}
    benchmark_summary = benchmark_summary or {}
    metrics = metrics or {}
    targets = [
        str(target.get("id", "")).strip()
        for target in artifact_plan.get("targets", [])
        if isinstance(target, dict) and str(target.get("id", "")).strip()
    ]
    preview_iterations = preview_loop_report.get("iterations", []) if isinstance(preview_loop_report.get("iterations", []), list) else []
    preview_summary = {
        "enabled": bool(preview_loop_report.get("enabled")),
        "accepted": bool(preview_loop_report.get("accepted")),
        "stopped_reason": str(preview_loop_report.get("stopped_reason") or ""),
        "iterations": len(preview_iterations),
    }
    judge_summary = {
        "quality_pass": bool(quality_report.get("quality_pass")),
        "premium_ok": bool(quality_report.get("premium_ok")),
        "brand_ok": bool(quality_report.get("brand_ok")),
        "vision_ok": bool(quality_report.get("vision_ok")) if "vision_ok" in quality_report else None,
        "final_quality_summary": str(quality_report.get("final_quality_summary") or ""),
        "target_count": len((quality_report.get("target_reports") or {}).keys()) if isinstance(quality_report.get("target_reports"), dict) else 0,
    }
    now = time.time()
    return GovernedRunSummary(
        run_id=run_id,
        session_id=session_id,
        created_at=now,
        updated_at=now,
        source=source,
        runtime_profile=runtime_profile,
        execution_mode=execution_mode,
        policy=policy.to_dict(),
        input_reference=input_reference_from_seed(seed),
        style_pack=str(artifact_plan.get("style_pack") or ""),
        targets=targets,
        preview_loop_summary=preview_summary,
        judge_summary=judge_summary,
        benchmark_summary=deepcopy(benchmark_summary),
        final_status=final_status,
        metrics=deepcopy(metrics),
        errors=list(errors or []),
        artifacts=deepcopy(artifacts or {}),
    )
