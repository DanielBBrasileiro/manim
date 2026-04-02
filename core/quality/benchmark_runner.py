from __future__ import annotations

import copy
from datetime import datetime, timezone
from pathlib import Path
import time
from typing import Any

import yaml

from core.compiler.creative_compiler import compile_seed
from core.compiler.render_manifest import build_artifact_plan, build_render_manifest
from core.quality.benchmark_report import aggregate_benchmark_run, render_benchmark_markdown
from core.quality.benchmark_store import create_run_id, save_benchmark_run
from core.quality.golden_set import load_golden_set
from core.quality.preview_loop import run_preview_iteration_loop
from core.quality.quality_runtime import run_quality_pipeline
from core.runtime.execution_policy import resolve_execution_policy
from core.runtime.run_governance import build_governed_run_summary, save_governed_run

ROOT = Path(__file__).resolve().parent.parent.parent
STYLE_PACK_DIR = ROOT / "contracts" / "style_packs"
STILL_DIMENSIONS = [
    "hierarchy_strength",
    "typographic_craft",
    "spatial_intelligence",
    "poster_impact",
    "brand_discipline",
    "material_finish",
    "emotional_coherence",
    "originality",
]
MOTION_DIMENSIONS = [
    "motion_coherence",
    "temporal_rhythm",
    "typographic_craft",
    "spatial_intelligence",
    "transition_quality",
    "emotional_arc",
    "brand_discipline",
    "silence_quality",
]


def run_benchmark_suite(
    golden_set_ref: str | None = None,
    *,
    case_ids: list[str] | None = None,
    include_final: bool = False,
    persist: bool = True,
    lightweight: bool = True,
) -> dict[str, Any]:
    started = time.monotonic()
    golden_set = load_golden_set(golden_set_ref)
    requested_ids = {str(case_id).strip() for case_id in (case_ids or []) if str(case_id).strip()}
    selected_cases = [
        case
        for case in golden_set.get("cases", [])
        if not requested_ids or str(case.get("case_id", "")).strip() in requested_ids
    ]

    run_report: dict[str, Any] = {
        "run_id": create_run_id(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "golden_set_id": golden_set.get("id"),
        "golden_set_path": golden_set.get("path"),
        "mode": "lightweight",
        "execution_mode": resolve_execution_policy("benchmark").mode,
        "include_final": include_final,
        "cases": [],
    }

    for case in selected_cases:
        run_report["cases"].append(run_benchmark_case(case, include_final=include_final, lightweight=lightweight))

    run_report["aggregate"] = aggregate_benchmark_run(run_report)
    run_report["metrics"] = {
        "total_run_duration_ms": round((time.monotonic() - started) * 1000.0, 2),
        "preview_iterations_used": sum(
            int(case.get("preview_iterations_used", 0) or 0)
            for case in run_report.get("cases", [])
        ),
    }
    run_report["report_markdown"] = render_benchmark_markdown(run_report)
    if persist:
        path = save_benchmark_run(run_report, run_id=run_report["run_id"])
        run_report["storage_path"] = str(path)
        policy = resolve_execution_policy("benchmark")
        governed_summary = build_governed_run_summary(
            run_id=run_report["run_id"],
            session_id=run_report["run_id"],
            source="benchmark_runner",
            runtime_profile="benchmark",
            execution_mode=policy.mode,
            policy=policy,
            seed={"prompt": golden_set.get("title"), "golden_set_id": golden_set.get("id")},
            artifact_plan={
                "style_pack": "",
                "targets": [
                    {"id": str(case.get("target", "")).strip()}
                    for case in run_report.get("cases", [])
                    if str(case.get("target", "")).strip()
                ],
            },
            preview_loop_report={
                "enabled": True,
                "iterations": [
                    {"case_id": case.get("case_id"), "iterations": case.get("preview_iterations_used", 0)}
                    for case in run_report.get("cases", [])
                ],
                "accepted": False,
                "stopped_reason": "benchmark_complete",
            },
            quality_report={},
            benchmark_summary={
                "golden_set_id": golden_set.get("id"),
                "case_count": len(run_report.get("cases", [])),
                "aggregate": run_report.get("aggregate", {}),
            },
            metrics=run_report.get("metrics", {}),
            final_status="benchmark_complete",
            errors=[],
            artifacts={"benchmark_report_path": str(path)},
        )
        governed_path = save_governed_run(governed_summary)
        run_report["governed_run_id"] = run_report["run_id"]
        run_report["governed_run_path"] = str(governed_path)
    return run_report


def run_benchmark_case(case: dict[str, Any], *, include_final: bool = False, lightweight: bool = True) -> dict[str, Any]:
    seed = _load_case_seed(case)
    compilation = _compile_case_seed(seed, lightweight=lightweight)
    plan = copy.deepcopy(compilation.get("creative_plan") or {})
    artifact_plan = copy.deepcopy(compilation.get("artifact_plan") or {})
    render_manifest = copy.deepcopy(compilation.get("render_manifest") or {})
    target_id = str(case.get("target") or artifact_plan.get("primary_target_id") or "").strip()

    artifact_plan, render_manifest, plan = _restrict_to_target(plan, artifact_plan, render_manifest, target_id)
    artifact_plan, render_manifest, plan = _apply_style_pack(case, plan, artifact_plan, render_manifest)

    preview_loop = run_preview_iteration_loop(
        plan,
        artifact_plan,
        render_manifest,
        context={
            "archetype": plan.get("archetype"),
            "benchmark_case_id": case.get("case_id"),
            "style_pack": artifact_plan.get("style_pack"),
        },
    )
    iterations = preview_loop.get("iterations", []) if isinstance(preview_loop.get("iterations", []), list) else []
    last_iteration = iterations[-1] if iterations else {}
    first_iteration = iterations[0] if iterations else {}
    preview_report = last_iteration.get("preview_judge", {}) if isinstance(last_iteration.get("preview_judge", {}), dict) else {}
    preview_score = float(preview_report.get("score", 0.0) or 0.0)
    preview_initial_score = float(
        (first_iteration.get("preview_judge", {}) if isinstance(first_iteration.get("preview_judge", {}), dict) else {}).get("score", preview_score) or preview_score
    )
    final_artifact_plan = preview_loop.get("artifact_plan", artifact_plan)
    final_plan = preview_loop.get("plan", plan)
    final_manifest = preview_loop.get("render_manifest", render_manifest)

    preview_dimensions = _estimate_preview_dimensions(
        preview_report,
        artifact_class=str(case.get("artifact_class") or "still").strip().lower(),
    )
    result: dict[str, Any] = {
        "case_id": str(case.get("case_id", "")).strip(),
        "target": target_id,
        "artifact_class": str(case.get("artifact_class") or "still").strip().lower(),
        "style_pack": str(final_artifact_plan.get("style_pack") or case.get("style_pack") or "").strip(),
        "judge_profile": _target_value(final_artifact_plan, target_id, "judge_profile"),
        "briefing": str(case.get("briefing") or "").strip(),
        "expected_quality_focus": list(case.get("expected_quality_focus", []) or []),
        "preview_score": round(preview_score, 1),
        "preview_initial_score": round(preview_initial_score, 1),
        "preview_improvement_delta": round(preview_score - preview_initial_score, 1),
        "preview_iterations_used": len(iterations),
        "preview_accepted": bool(preview_loop.get("accepted")),
        "preview_stopped_reason": str(preview_loop.get("stopped_reason") or ""),
        "preview_hard_veto": bool(preview_report.get("hard_veto")),
        "hard_veto": bool(preview_report.get("hard_veto")),
        "preview_issue_count": len(preview_report.get("issues", []) or []),
        "preview_summary": preview_report.get("summary", {}),
        "dimension_scores": preview_dimensions,
        "weak_dimensions": _weak_dimensions(preview_dimensions),
        "final_score": None,
        "final_passed": None,
        "final_premium": None,
        "quality_band": "preview_only",
        "preview_loop_report": {
            "accepted": preview_loop.get("accepted"),
            "stopped_reason": preview_loop.get("stopped_reason"),
            "iterations": len(iterations),
        },
    }

    final_output_path = str(case.get("final_output_path") or "").strip()
    if include_final and final_output_path:
        target_report, quality_report = _run_final_quality(
            final_plan,
            final_artifact_plan,
            final_manifest,
            target_id=target_id,
            output_path=final_output_path,
        )
        final_score = _extract_final_score(target_report)
        final_dimensions = _extract_final_dimensions(target_report)
        result.update(
            {
                "final_score": final_score,
                "final_passed": bool((target_report.get("visual_judge_fast") or {}).get("passed")) if isinstance(target_report, dict) else None,
                "final_premium": bool(target_report.get("status") == "premium_pass") if isinstance(target_report, dict) else None,
                "hard_veto": bool(target_report.get("brand_veto")) if isinstance(target_report, dict) else result["hard_veto"],
                "quality_band": "premium" if target_report.get("status") == "premium_pass" else ("accepted" if target_report.get("status") in {"brand_only_pass", "fallback_pass", "fallback_acceptable"} else "final_reviewed"),
                "dimension_scores": final_dimensions or result["dimension_scores"],
                "weak_dimensions": _weak_dimensions(final_dimensions or result["dimension_scores"]),
                "final_quality_report": quality_report,
            }
        )
    return result


def _compile_case_seed(seed: dict[str, Any], *, lightweight: bool = True) -> dict[str, Any]:
    if not lightweight:
        return compile_seed(seed)

    brief = seed.get("creative_seed", seed) if isinstance(seed, dict) else {}
    output_targets = brief.get("output_targets", []) if isinstance(brief.get("output_targets", []), list) else []
    plan: dict[str, Any] = {
        "archetype": str(brief.get("transformation") or brief.get("archetype") or "emergence").strip(),
        "duration": float(brief.get("duration_sec") or brief.get("duration") or 12.0),
        "aesthetic_family": str(brief.get("aesthetic_family") or "cinematic_minimal").strip(),
        "text_beats": list(brief.get("text_beats", []) or []),
        "emotional_target": str(brief.get("emotional_target") or "").strip(),
        "visual_metaphor": str(brief.get("visual_metaphor") or "").strip(),
        "resolve_word": str(brief.get("resolve_word") or "AIOX").strip(),
        "output_targets": output_targets,
        "pacing_profile": {
            "mode": str(brief.get("pacing") or "cinematic").strip(),
            "motion_grammar": str(brief.get("motion_grammar") or "").strip(),
            "stagger_profile": "restrained",
            "transitions": ["crossfade", "cut"],
            "motion_sequences": [],
        },
    }
    artifact_plan = build_artifact_plan(plan, seed)
    plan["artifact_plan"] = artifact_plan
    render_manifest = build_render_manifest(plan, seed)
    plan["render_manifest"] = render_manifest
    return {
        "creative_plan": plan,
        "artifact_plan": artifact_plan,
        "render_manifest": render_manifest,
        "output_signature": {},
    }


def _load_case_seed(case: dict[str, Any]) -> dict[str, Any]:
    briefing_ref = str(case.get("briefing") or "").strip()
    if briefing_ref:
        path = ROOT / briefing_ref if not Path(briefing_ref).is_absolute() else Path(briefing_ref)
        if not path.exists():
            raise FileNotFoundError(f"Benchmark briefing not found: {path}")
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    intent = str(case.get("intent") or "").strip()
    if intent:
        return {"prompt": intent}
    raise ValueError(f"Benchmark case {case.get('case_id')} missing briefing or intent")


def _load_style_pack(style_pack_id: str) -> dict[str, Any]:
    path = STYLE_PACK_DIR / f"{style_pack_id}.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _restrict_to_target(
    plan: dict[str, Any],
    artifact_plan: dict[str, Any],
    render_manifest: dict[str, Any],
    target_id: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    filtered_targets = [
        target
        for target in artifact_plan.get("targets", [])
        if isinstance(target, dict) and str(target.get("id", "")).strip() == target_id
    ]
    if not filtered_targets:
        return artifact_plan, render_manifest, plan

    primary_target = copy.deepcopy(filtered_targets[0])
    artifact_plan["targets"] = copy.deepcopy(filtered_targets)
    artifact_plan["primary_target"] = primary_target
    artifact_plan["primary_target_id"] = target_id
    artifact_plan["requested_targets"] = [target_id]
    artifact_plan["premium_targets"] = [item for item in artifact_plan.get("premium_targets", []) if str(item).strip() == target_id]
    if isinstance(artifact_plan.get("renderer_contracts"), dict):
        artifact_plan["renderer_contracts"] = {
            key: value for key, value in artifact_plan["renderer_contracts"].items() if key == target_id
        }
    if isinstance(artifact_plan.get("family_spec"), dict):
        artifact_plan["family_spec"] = {
            key: value for key, value in artifact_plan["family_spec"].items() if key == target_id
        }
    if isinstance(artifact_plan.get("fallback_policy"), dict):
        artifact_plan["fallback_policy"] = {
            key: value for key, value in artifact_plan["fallback_policy"].items() if key == target_id
        }

    render_manifest["artifact_plan"] = artifact_plan
    render_manifest["targets"] = copy.deepcopy(filtered_targets)
    render_manifest["primary_target"] = primary_target
    if isinstance(render_manifest.get("render_inputs"), dict):
        render_manifest["render_inputs"] = {
            key: value for key, value in render_manifest["render_inputs"].items() if key == target_id
        }

    plan["artifact_plan"] = artifact_plan
    plan["render_manifest"] = render_manifest
    return artifact_plan, render_manifest, plan


def _apply_style_pack(
    case: dict[str, Any],
    plan: dict[str, Any],
    artifact_plan: dict[str, Any],
    render_manifest: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    style_pack_id = str(case.get("style_pack") or artifact_plan.get("style_pack") or "").strip()
    if not style_pack_id:
        return artifact_plan, render_manifest, plan

    pack = _load_style_pack(style_pack_id)
    if not pack:
        return artifact_plan, render_manifest, plan

    resolved = {
        "style_pack": style_pack_id,
        "style_pack_ids": [style_pack_id],
        "motion_grammar": pack.get("motion_grammar"),
        "typography_system": pack.get("typography_system"),
        "still_family": pack.get("still_family"),
        "color_mode": pack.get("color_mode"),
        "negative_space_target": pack.get("negative_space_target"),
        "accent_intensity": pack.get("accent_intensity"),
        "grain": pack.get("grain"),
    }
    for key, value in resolved.items():
        artifact_plan[key] = value
        render_manifest[key] = value

    quality_constraints = artifact_plan.get("quality_constraints", {}) if isinstance(artifact_plan.get("quality_constraints", {}), dict) else {}
    if resolved.get("negative_space_target") is not None:
        quality_constraints["negative_space_target"] = float(resolved["negative_space_target"] or 0.4)
    artifact_plan["quality_constraints"] = quality_constraints
    render_manifest["quality_constraints"] = quality_constraints

    for target in artifact_plan.get("targets", []):
        if not isinstance(target, dict):
            continue
        for key, value in resolved.items():
            if key == "style_pack_ids":
                continue
            target[key] = value

    for target in render_manifest.get("targets", []):
        if not isinstance(target, dict):
            continue
        for key, value in resolved.items():
            if key == "style_pack_ids":
                continue
            target[key] = value

    plan["artifact_plan"] = artifact_plan
    plan["render_manifest"] = render_manifest
    return artifact_plan, render_manifest, plan


def _estimate_preview_dimensions(preview_report: dict[str, Any], *, artifact_class: str) -> dict[str, float]:
    dimensions = STILL_DIMENSIONS if artifact_class == "still" else MOTION_DIMENSIONS
    base_score = float(preview_report.get("score", 72.0) or 72.0)
    estimated = {name: round(base_score, 1) for name in dimensions}
    penalty_map = {
        "overcrowding": {"spatial_intelligence": 16.0, "typographic_craft": 10.0},
        "poor_negative_space": {"spatial_intelligence": 18.0, "poster_impact": 10.0},
        "weak_focal_point": {"hierarchy_strength": 14.0, "poster_impact": 10.0},
        "layout_overload": {"spatial_intelligence": 14.0, "poster_impact": 8.0},
        "flat_hierarchy": {"hierarchy_strength": 18.0, "typographic_craft": 10.0},
        "motion_pacing": {"temporal_rhythm": 16.0, "silence_quality": 14.0, "motion_coherence": 8.0},
        "resolve_hard_veto": {"brand_discipline": 60.0},
        "gradient_detected": {"brand_discipline": 55.0, "material_finish": 16.0},
        "logo_detected": {"brand_discipline": 70.0},
    }
    for issue in preview_report.get("issues", []):
        if not isinstance(issue, dict):
            continue
        issue_code = str(issue.get("code", "")).strip()
        for name, penalty in penalty_map.get(issue_code, {}).items():
            if name in estimated:
                estimated[name] = round(max(0.0, estimated[name] - penalty), 1)
    if preview_report.get("hard_veto") and "brand_discipline" in estimated:
        estimated["brand_discipline"] = min(estimated["brand_discipline"], 12.0)
    return estimated


def _weak_dimensions(dimension_scores: dict[str, float]) -> list[str]:
    return [
        name
        for name, score in sorted(dimension_scores.items(), key=lambda item: item[1])
        if float(score) < 70.0
    ][:4]


def _run_final_quality(
    plan: dict[str, Any],
    artifact_plan: dict[str, Any],
    render_manifest: dict[str, Any],
    *,
    target_id: str,
    output_path: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    target = next(
        (
            item
            for item in artifact_plan.get("targets", [])
            if isinstance(item, dict) and str(item.get("id", "")).strip() == target_id
        ),
        {},
    )
    quality_report = run_quality_pipeline(
        [
            {
                "target": target_id,
                "mode": target.get("render_mode", "still"),
                "output": output_path,
                "fallback": False,
            }
        ],
        artifact_plan,
        context={
            "archetype": plan.get("archetype"),
            "render_manifest": render_manifest,
        },
    )
    return quality_report.get("target_reports", {}).get(target_id, {}), quality_report


def _extract_final_score(target_report: dict[str, Any]) -> float | None:
    if not isinstance(target_report, dict):
        return None
    batch_summary = target_report.get("batch_summary", {}) if isinstance(target_report.get("batch_summary", {}), dict) else {}
    score = batch_summary.get("avg_score")
    if score is None:
        return None
    return round(float(score), 1)


def _extract_final_dimensions(target_report: dict[str, Any]) -> dict[str, float]:
    frame_scores = target_report.get("frame_scores", []) if isinstance(target_report.get("frame_scores", []), list) else []
    if not frame_scores:
        return {}
    dims = frame_scores[0].get("dimensions", []) if isinstance(frame_scores[0], dict) else []
    return {
        str(item.get("name", "")).strip(): float(item.get("score", 0.0) or 0.0)
        for item in dims
        if isinstance(item, dict) and str(item.get("name", "")).strip()
    }


def _target_value(artifact_plan: dict[str, Any], target_id: str, key: str) -> Any:
    for target in artifact_plan.get("targets", []):
        if isinstance(target, dict) and str(target.get("id", "")).strip() == target_id:
            return target.get(key)
    return artifact_plan.get(key)
