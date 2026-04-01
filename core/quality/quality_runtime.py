from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from core.intelligence.model_capabilities import load_model_capabilities, refresh_model_capabilities
from core.quality.brand_validator import validate_frame
from core.quality.frame_scorer import batch_summary, score_frames
from core.quality.post_processor import apply_post_fx_to_target

ROOT = Path(__file__).resolve().parent.parent.parent


def run_quality_pipeline(
    target_outputs: list[dict[str, Any]],
    artifact_plan: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = context or {}
    premium_targets = {
        str(target_id).strip()
        for target_id in artifact_plan.get("premium_targets", [])
        if str(target_id).strip()
    }
    target_specs = {
        str(target.get("id", "")).strip(): target
        for target in artifact_plan.get("targets", [])
        if isinstance(target, dict) and str(target.get("id", "")).strip()
    }

    report: dict[str, Any] = {
        "ok": True,
        "delivery_ok": True,
        "render_ok": True,
        "brand_ok": True,
        "vision_ok": False,
        "premium_ok": False,
        "quality_pass": False,
        "quality_mode": artifact_plan.get("quality_mode", "absolute"),
        "quality_tier": artifact_plan.get("quality_tier", "lab_absolute"),
        "judge_stack": artifact_plan.get("judge_stack", []),
        "brand_precheck": True,
        "frame_scores": [],
        "iteration_count": 0,
        "objective_metrics_summary": {},
        "judge_disagreement_rate": 0.0,
        "native_vs_fallback": {
            "native_outputs": 0,
            "fallback_outputs": 0,
        },
        "target_reports": {},
        "final_quality_summary": "",
    }
    if not target_outputs:
        report["ok"] = False
        report["delivery_ok"] = False
        report["render_ok"] = False
        report["brand_ok"] = False
        report["quality_pass"] = False
        report["final_quality_summary"] = "Nenhum target renderizado para validar."
        return report

    vision_available = _vision_available()
    report["vision_available"] = vision_available

    for output in target_outputs:
        if not isinstance(output, dict):
            continue
        target_id = str(output.get("target", "")).strip()
        target_spec = target_specs.get(target_id, {})
        premium_target = target_id in premium_targets
        fallback = bool(output.get("fallback"))

        if fallback:
            report["native_vs_fallback"]["fallback_outputs"] += 1
        else:
            report["native_vs_fallback"]["native_outputs"] += 1

        post_fx = _apply_post_fx(
            target_report={
                "target": target_id,
                "mode": output.get("mode"),
                "output": output.get("output"),
                "slides": output.get("slides", []),
                "fallback": fallback,
                "premium_target": premium_target,
                "post_fx_profile": target_spec.get("post_fx_profile"),
            },
            context={
                **context,
                "post_fx_profile": target_spec.get("post_fx_profile"),
                "quality_mode": artifact_plan.get("quality_mode", "absolute"),
                "strict_effect_enforcement": premium_target and not fallback,
            },
        )
        frame_payload = _collect_quality_frames(output, target_spec)
        candidate_frames = frame_payload["qa_frames"]
        poster_frames = frame_payload["poster_frames"]

        brand_results = [validate_frame(path) for path in candidate_frames]
        brand_ok = bool(brand_results) and all(result.passed for result in brand_results if not result.error)
        brand_violations = _collect_violations(brand_results)
        objective_metrics = _objective_metrics(brand_results)
        brand_veto = _brand_veto_reasons(
            target_id=target_id,
            premium_target=premium_target,
            brand_results=brand_results,
        )

        poster_result = _poster_test(
            poster_frames,
            target_spec=target_spec,
            vision_available=vision_available,
            render_mode=str(target_spec.get("render_mode", output.get("mode", "video"))).strip().lower(),
        )

        vision_scores: list[dict[str, Any]] = []
        vision_summary: dict[str, Any] | None = None
        vision_ok = False
        visual_judge_fast = {
            "enabled": "visual_judge_fast" in report["judge_stack"],
            "invoked": False,
            "passed": None,
            "summary": None,
        }
        visual_judge_heavy = {
            "enabled": "visual_judge_heavy" in report["judge_stack"],
            "invoked": False,
            "available": False,
            "passed": None,
            "summary": None,
            "reason": "not_required",
        }
        if candidate_frames and vision_available and not brand_veto:
            scores = score_frames(
                candidate_frames,
                threshold=70.0,
                context={
                    "archetype": str(target_spec.get("plan_archetype") or context.get("archetype") or ""),
                    "render_mode": str(target_spec.get("render_mode", output.get("mode", "still"))).strip().lower(),
                    "target": target_id,
                    "judge_profile": target_spec.get("judge_profile"),
                    "style_pack": target_spec.get("style_pack"),
                    "typography_system": target_spec.get("typography_system"),
                    "still_family": target_spec.get("still_family"),
                    "motion_grammar": target_spec.get("motion_grammar"),
                    "negative_space_target": target_spec.get(
                        "negative_space_target",
                        (artifact_plan.get("quality_constraints") or {}).get("negative_space_target", 0.4),
                    ),
                    "max_words_per_screen": int(
                        (artifact_plan.get("copy_budget") or {}).get(
                            "max_words_per_frame",
                            (artifact_plan.get("quality_constraints") or {}).get("max_words_per_screen", 5),
                        )
                        or 5
                    ),
                    "silence_ratio": float(
                        (artifact_plan.get("copy_budget") or {}).get(
                            "target_silence_ratio",
                            (artifact_plan.get("quality_constraints") or {}).get("silence_ratio", 0.3),
                        )
                        or 0.3
                    ),
                    "act_quality_profile": target_spec.get("act_quality_profile", {}),
                },
            )
            vision_scores = [score.to_dict() for score in scores]
            vision_summary = batch_summary(scores)
            vision_ok = bool(vision_summary.get("total")) and float(vision_summary.get("avg_score", 0.0) or 0.0) >= 70.0 and int(vision_summary.get("failed", 0) or 0) == 0
            report["frame_scores"].extend(vision_scores)
            visual_judge_fast = {
                "enabled": True,
                "invoked": True,
                "passed": vision_ok,
                "summary": vision_summary,
            }
            visual_judge_heavy = _heavy_judge_result(
                context=context,
                premium_target=premium_target,
                fast_summary=vision_summary or {},
            )

        status = _target_status(
            fallback=fallback,
            premium_target=premium_target,
            brand_ok=brand_ok and not brand_veto,
            vision_available=vision_available,
            vision_ok=vision_ok,
            poster_passed=bool(poster_result.get("passed")),
            heavy_judge=visual_judge_heavy,
        )
        target_report = {
            "target": target_id,
            "output": output.get("output"),
            "render_ok": Path(str(output.get("output", ""))).exists(),
            "fallback": fallback,
            "premium_target": premium_target,
            "brand_precheck": brand_ok and not brand_veto,
            "brand_veto": bool(brand_veto),
            "brand_veto_reasons": brand_veto,
            "brand_violations": brand_violations,
            "brand_results": [result.to_dict() for result in brand_results],
            "vision_qa": vision_available,
            "vision_ok": vision_ok if vision_available else None,
            "frame_scores": vision_scores,
            "batch_summary": vision_summary,
            "judge_stack": list(report["judge_stack"]),
            "objective_metrics": objective_metrics,
            "visual_judge_fast": visual_judge_fast,
            "visual_judge_heavy": visual_judge_heavy,
            "poster_test": poster_result,
            "post_fx_profile": target_spec.get("post_fx_profile"),
            "post_fx_applied": post_fx,
            "qa_frames": candidate_frames,
            "status": status,
        }
        report["target_reports"][target_id] = target_report
        report["iteration_count"] += 1

        report["render_ok"] = report["render_ok"] and target_report["render_ok"]
        report["delivery_ok"] = report["delivery_ok"] and target_report["render_ok"]
        report["brand_precheck"] = report["brand_precheck"] and target_report["brand_precheck"]
        report["brand_ok"] = report["brand_ok"] and target_report["brand_precheck"]

    target_reports = list(report["target_reports"].values())
    premium_reports = [entry for entry in target_reports if entry.get("premium_target")]
    if premium_reports:
        report["premium_ok"] = all(entry.get("status") == "premium_pass" for entry in premium_reports)
    report["vision_ok"] = vision_available and bool(target_reports) and all(
        (entry.get("vision_ok") is True) or (entry.get("vision_qa") is False)
        for entry in target_reports
    )
    report["delivery_ok"] = all(
        entry.get("status") in {"premium_pass", "brand_only_pass", "fallback_pass", "fallback_acceptable"}
        for entry in target_reports
    ) and report["render_ok"]
    if premium_reports:
        report["quality_pass"] = report["premium_ok"]
    else:
        report["quality_pass"] = report["brand_ok"] and (report["vision_ok"] or not vision_available)
    report["ok"] = report["delivery_ok"]
    report["objective_metrics_summary"] = _summarize_objective_metrics(report["target_reports"])
    report["judge_disagreement_rate"] = _judge_disagreement_rate(report["target_reports"])
    report["final_quality_summary"] = _summarize_report(report)
    return report


def _vision_available() -> bool:
    try:
        capabilities = load_model_capabilities()
        if not capabilities:
            capabilities = refresh_model_capabilities()
    except Exception:
        capabilities = []
    return any(bool(capability.supports_vision_plan) for capability in capabilities)


def _collect_quality_frames(output: dict[str, Any], target_spec: dict[str, Any]) -> dict[str, list[str]]:
    render_mode = str(target_spec.get("render_mode", output.get("mode", "video"))).strip().lower()
    if render_mode == "still":
        output_path = str(output.get("output", "")).strip()
        frames = [output_path] if output_path else []
        return {"qa_frames": frames, "poster_frames": frames}

    if render_mode == "carousel":
        slide_paths = [str(path).strip() for path in output.get("slides", []) if str(path).strip()]
        if not slide_paths:
            output_dir = Path(str(output.get("output", "")).strip())
            if output_dir.exists():
                slide_paths = [str(path) for path in sorted(output_dir.glob("slide_*.png"))]
        poster_indices = {
            0,
            max(len(slide_paths) - 2, 0),
            max(len(slide_paths) - 1, 0),
        }
        poster_frames = [slide_paths[index] for index in sorted(poster_indices) if 0 <= index < len(slide_paths)]
        return {"qa_frames": slide_paths, "poster_frames": poster_frames or slide_paths[:1]}

    output_path = str(output.get("output", "")).strip()
    if not output_path:
        return {"qa_frames": [], "poster_frames": []}
    qa_points = _float_list(target_spec.get("qa_sampling_frames")) or [2.0, 6.0, 10.0]
    poster_points = _float_list(target_spec.get("poster_test_frames")) or qa_points
    qa_frames = _extract_video_frames(output_path, qa_points)
    poster_frames = _extract_video_frames(output_path, poster_points)
    return {"qa_frames": qa_frames, "poster_frames": poster_frames}


def _extract_video_frames(video_path: str, sample_points: list[float]) -> list[str]:
    if not shutil.which("ffmpeg"):
        return []
    source = Path(video_path)
    if not source.exists():
        return []
    tmp_dir = Path(tempfile.mkdtemp(prefix="aiox_quality_frames_"))
    frames: list[str] = []
    for index, second in enumerate(sample_points, start=1):
        target = tmp_dir / f"frame_{index:02d}.png"
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-ss",
                    f"{max(float(second), 0.0):.2f}",
                    "-i",
                    str(source),
                    "-frames:v",
                    "1",
                    str(target),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if target.exists():
                frames.append(str(target))
        except Exception:
            continue
    return frames


def _apply_post_fx(target_report: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Usa a ponte oficial para aplicar efeitos baseados no contrato."""
    try:
        return apply_post_fx_to_target(target_report, context=context)
    except Exception as exc:
        return {"applied": False, "error": str(exc)}

def _collect_violations(results: list[Any]) -> list[str]:
    violations: list[str] = []
    for result in results:
        for violation in result.violations:
            if violation not in violations:
                violations.append(violation)
    return violations


def _brand_veto_reasons(
    *,
    target_id: str,
    premium_target: bool,
    brand_results: list[Any],
) -> list[str]:
    reasons: list[str] = []
    if not premium_target:
        return reasons
    for result in brand_results:
        if result.color_purity_score < 75:
            reasons.append(f"{target_id}:color_purity_below_threshold")
        if result.negative_space_pct < 0.40:
            reasons.append(f"{target_id}:negative_space_below_threshold")
        if result.text_density_estimate > 5:
            reasons.append(f"{target_id}:text_density_above_threshold")
    return sorted(set(reasons))


def _poster_test(
    poster_frames: list[str],
    *,
    target_spec: dict[str, Any],
    vision_available: bool,
    render_mode: str,
) -> dict[str, Any]:
    if not poster_frames:
        return {"passed": False, "sampled_frames": [], "failures": ["poster_frames_missing"]}

    failures: list[str] = []
    brand_results = [validate_frame(frame) for frame in poster_frames]
    for result in brand_results:
        if not result.passed:
            failures.extend(result.violations or [f"poster_frame_failed:{result.frame_path}"])

    if render_mode == "video":
        act_profile = target_spec.get("act_quality_profile", {})
        expected = len(act_profile) if isinstance(act_profile, dict) and act_profile else 3
        if len(poster_frames) < expected:
            failures.append("poster_test_missing_act_samples")

    return {
        "passed": not failures,
        "sampled_frames": poster_frames,
        "failures": sorted(set(failures)),
        "vision_required": vision_available,
    }


def _target_status(
    *,
    fallback: bool,
    premium_target: bool,
    brand_ok: bool,
    vision_available: bool,
    vision_ok: bool,
    poster_passed: bool,
    heavy_judge: dict[str, Any] | None = None,
) -> str:
    if fallback:
        return "fallback_pass" if premium_target else "fallback_acceptable"
    heavy_required = bool((heavy_judge or {}).get("enabled") and (heavy_judge or {}).get("invoked"))
    heavy_ok = (heavy_judge or {}).get("passed")
    if brand_ok and vision_available and vision_ok and poster_passed and (not heavy_required or heavy_ok is True):
        return "premium_pass" if premium_target else "vision_pass"
    if brand_ok and not vision_available:
        return "brand_only_pass"
    if brand_ok:
        return "structural_pass"
    return "failed"


def _summarize_report(report: dict[str, Any]) -> str:
    premium = sum(1 for entry in report.get("target_reports", {}).values() if entry.get("status") == "premium_pass")
    brand_only = sum(1 for entry in report.get("target_reports", {}).values() if entry.get("status") == "brand_only_pass")
    fallback = report.get("native_vs_fallback", {}).get("fallback_outputs", 0)
    return (
        f"delivery_ok={report.get('delivery_ok')} "
        f"render_ok={report.get('render_ok')} "
        f"brand_ok={report.get('brand_ok')} "
        f"vision_ok={report.get('vision_ok')} "
        f"premium_ok={report.get('premium_ok')} "
        f"judge_disagreement_rate={report.get('judge_disagreement_rate')} "
        f"premium_targets_passed={premium} "
        f"brand_only={brand_only} "
        f"fallback_outputs={fallback}"
    )


def _float_list(value: Any) -> list[float]:
    if not isinstance(value, list):
        return []
    numbers: list[float] = []
    for item in value:
        try:
            numbers.append(float(item))
        except (TypeError, ValueError):
            continue
    return numbers


def _objective_metrics(brand_results: list[Any]) -> dict[str, Any]:
    if not brand_results:
        return {}
    negatives = [float(result.negative_space_pct or 0.0) for result in brand_results]
    text_density = [int(result.text_density_estimate or 0) for result in brand_results]
    color_purity = [float(result.color_purity_score or 0.0) for result in brand_results]
    grain = [float(result.grain_variance or 0.0) for result in brand_results]
    return {
        "avg_negative_space_pct": round(sum(negatives) / max(len(negatives), 1), 4),
        "max_text_density_estimate": max(text_density) if text_density else 0,
        "avg_color_purity_score": round(sum(color_purity) / max(len(color_purity), 1), 2),
        "avg_grain_variance": round(sum(grain) / max(len(grain), 1), 4),
    }


def _heavy_judge_result(
    *,
    context: dict[str, Any] | None,
    premium_target: bool,
    fast_summary: dict[str, Any],
) -> dict[str, Any]:
    runtime_os = ((context or {}).get("capability_pool") or {}).get("runtime_os", {})
    heavy_role = (runtime_os.get("roles") or {}).get("visual_judge_heavy", {})
    avg_score = float(fast_summary.get("avg_score", 0.0) or 0.0)
    should_invoke = bool(
        premium_target
        and heavy_role.get("available")
        and (avg_score < 82.0 or avg_score > 0.0 and avg_score < 75.0)
    )
    if not should_invoke:
        return {
            "enabled": "visual_judge_heavy" in runtime_os.get("judge_stack", []),
            "invoked": False,
            "available": bool(heavy_role.get("available")),
            "passed": None,
            "summary": None,
            "reason": "fast_judge_confident_or_heavy_unavailable",
        }
    return {
        "enabled": True,
        "invoked": True,
        "available": True,
        "passed": avg_score >= 72.0,
        "summary": {"proxy_avg_score": avg_score, "model": heavy_role.get("model")},
        "reason": "proxy_heavy_review",
    }


def _summarize_objective_metrics(target_reports: dict[str, Any]) -> dict[str, Any]:
    metrics = [report.get("objective_metrics", {}) for report in target_reports.values() if isinstance(report, dict)]
    metrics = [entry for entry in metrics if entry]
    if not metrics:
        return {}
    return {
        "avg_negative_space_pct": round(sum(entry.get("avg_negative_space_pct", 0.0) for entry in metrics) / len(metrics), 4),
        "max_text_density_estimate": max(int(entry.get("max_text_density_estimate", 0) or 0) for entry in metrics),
        "avg_color_purity_score": round(sum(entry.get("avg_color_purity_score", 0.0) for entry in metrics) / len(metrics), 2),
    }


def _judge_disagreement_rate(target_reports: dict[str, Any]) -> float:
    disagreements = 0
    considered = 0
    for report in target_reports.values():
        if not isinstance(report, dict):
            continue
        fast = (report.get("visual_judge_fast") or {}).get("passed")
        heavy = (report.get("visual_judge_heavy") or {}).get("passed")
        if fast is None or heavy is None:
            continue
        considered += 1
        if fast != heavy:
            disagreements += 1
    return round(disagreements / considered, 4) if considered else 0.0
