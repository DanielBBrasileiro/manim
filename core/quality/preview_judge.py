from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.quality.brand_validator import validate_frame
from core.quality.mutator import build_mutation_plan
from core.tools.quality_gate import evaluate_artifact_plan


@dataclass
class PreviewIssue:
    code: str
    severity: str
    target_id: str
    message: str
    directive: str
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "target_id": self.target_id,
            "message": self.message,
            "directive": self.directive,
            "metrics": self.metrics,
        }


def run_preview_judge(
    preview_bundle: dict[str, Any],
    artifact_plan: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = context or {}
    artifact_quality = evaluate_artifact_plan(artifact_plan)
    preview_path = str(preview_bundle.get("preview_path", "")).strip()
    brand_result = validate_frame(preview_path) if preview_path else None
    copy_budget = artifact_plan.get("copy_budget", {}) if isinstance(artifact_plan.get("copy_budget", {}), dict) else {}
    quality_constraints = artifact_plan.get("quality_constraints", {}) if isinstance(artifact_plan.get("quality_constraints", {}), dict) else {}
    target_map = {
        str(target.get("id", "")).strip(): target
        for target in artifact_plan.get("targets", [])
        if isinstance(target, dict) and str(target.get("id", "")).strip()
    }

    issues: list[PreviewIssue] = []
    hard_veto = bool(brand_result and brand_result.hard_veto_reasons)
    primary_target_id = str(artifact_plan.get("primary_target_id", "")).strip()
    primary_target = target_map.get(primary_target_id, {})
    max_words = int(copy_budget.get("max_words_per_frame", quality_constraints.get("max_words_per_screen", 5)) or 5)
    negative_space_target = float(quality_constraints.get("negative_space_target", 0.4) or 0.4)
    silence_ratio = float(copy_budget.get("target_silence_ratio", quality_constraints.get("silence_ratio", 0.3)) or 0.3)

    if brand_result:
        if brand_result.text_density_estimate > max_words:
            issues.append(
                PreviewIssue(
                    code="overcrowding",
                    severity="high",
                    target_id=primary_target_id,
                    message="Preview indicates text density above the current copy budget.",
                    directive="reduce_text_density",
                    metrics={"text_density_estimate": brand_result.text_density_estimate, "max_words": max_words},
                )
            )
        if brand_result.negative_space_pct < negative_space_target:
            issues.append(
                PreviewIssue(
                    code="poor_negative_space",
                    severity="high",
                    target_id=primary_target_id,
                    message="Preview negative space is below the target threshold.",
                    directive="increase_negative_space",
                    metrics={"negative_space_pct": brand_result.negative_space_pct, "target": negative_space_target},
                )
            )
        if brand_result.color_purity_score < 80:
            issues.append(
                PreviewIssue(
                    code="weak_focal_point",
                    severity="medium",
                    target_id=primary_target_id,
                    message="Preview palette purity is weak, suggesting a muddy focal structure.",
                    directive="tighten_hierarchy",
                    metrics={"color_purity_score": brand_result.color_purity_score},
                )
            )
        for veto in brand_result.hard_veto_reasons:
            issues.append(
                PreviewIssue(
                    code=str(veto.get("code", "hard_veto")),
                    severity="blocker",
                    target_id=primary_target_id,
                    message=str(veto.get("detail", "Preview frame violated a hard veto.")),
                    directive="resolve_hard_veto",
                    metrics=dict(veto.get("metrics", {})),
                )
            )

    for target_id, target in target_map.items():
        render_mode = str(target.get("render_mode", "still")).strip().lower()
        still_family = str(target.get("still_family", "")).strip()
        typography_system = str(target.get("typography_system", "")).strip()
        if render_mode in {"still", "carousel"}:
            max_text_elements = 0
            if render_mode == "carousel":
                max_text_elements = sum(
                    len(slide.get("text_blocks", []))
                    for slide in target.get("slides", [])
                    if isinstance(slide, dict)
                )
            else:
                max_text_elements = len([beat for beat in target.get("beats", []) if isinstance(beat, dict)])

            if max_text_elements > 3 and still_family != "poster_minimal":
                issues.append(
                    PreviewIssue(
                        code="layout_overload",
                        severity="medium",
                        target_id=target_id,
                        message="Still preview carries too many text elements for a premium poster-style composition.",
                        directive="switch_still_family",
                        metrics={"text_elements": max_text_elements, "still_family": still_family},
                    )
                )
            if typography_system == "editorial_dense" and target_id == "linkedin_feed_4_5":
                issues.append(
                    PreviewIssue(
                        code="flat_hierarchy",
                        severity="medium",
                        target_id=target_id,
                        message="Hero still preview needs stronger hierarchy than the current typography system provides.",
                        directive="adjust_typography_scale",
                        metrics={"typography_system": typography_system},
                    )
                )

        if render_mode == "video":
            act_profile = target.get("act_quality_profile", {}) if isinstance(target.get("act_quality_profile", {}), dict) else {}
            holds = [
                int(profile.get("minimum_hold_ms", 0) or 0)
                for profile in act_profile.values()
                if isinstance(profile, dict)
            ]
            average_hold = sum(holds) / len(holds) if holds else 0.0
            if silence_ratio < 0.25 or average_hold < 220:
                issues.append(
                    PreviewIssue(
                        code="motion_pacing",
                        severity="medium",
                        target_id=target_id,
                        message="Motion preview pacing is too dense for clean act separation.",
                        directive="change_motion_grammar",
                        metrics={"silence_ratio": silence_ratio, "average_hold_ms": round(average_hold, 1)},
                    )
                )

    score = 100.0
    score -= len(artifact_quality.get("errors", [])) * 18.0
    score -= len(artifact_quality.get("warnings", [])) * 4.0
    for issue in issues:
        if issue.severity == "blocker":
            score -= 24.0
        elif issue.severity == "high":
            score -= 14.0
        else:
            score -= 8.0
    score = max(0.0, min(100.0, score))

    policy = artifact_plan.get("preview_policy", {}) if isinstance(artifact_plan.get("preview_policy", {}), dict) else {}
    accept_score = float(policy.get("accept_score", 72.0) or 72.0)
    accepted = not hard_veto and not artifact_quality.get("errors") and score >= accept_score

    mutation_plan = {"ok": False, "directives": [], "skipped": [], "summary": []}
    if not accepted and not hard_veto:
        finding_dicts = [issue.to_dict() for issue in issues]
        mutation_plan = build_mutation_plan(
            artifact_plan,
            finding_dicts,
            brand_result.to_dict() if brand_result else None,
        )

    return {
        "accepted": accepted,
        "score": round(score, 1),
        "hard_veto": hard_veto,
        "issues": [issue.to_dict() for issue in issues],
        "mutation_plan": mutation_plan,
        "applied_mutations": [],
        "artifact_quality_report": artifact_quality,
        "brand_preview": brand_result.to_dict() if brand_result else None,
        "summary": {
            "issue_count": len(issues),
            "errors": len(artifact_quality.get("errors", [])),
            "warnings": len(artifact_quality.get("warnings", [])),
        },
        "context": {"archetype": context.get("archetype"), "preview_path": preview_path},
    }
