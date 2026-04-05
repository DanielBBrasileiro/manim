from __future__ import annotations

import copy
import os
from typing import Any

from core.quality.fix_plan import apply_fix_plan, generate_fix_plan
from core.quality.mutator import apply_mutation_plan
from core.quality.preview_judge import run_preview_judge
from core.quality.preview_runtime import build_preview_bundle


def run_preview_iteration_loop(
    plan: dict[str, Any],
    artifact_plan: dict[str, Any],
    render_manifest: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = context or {}
    policy = artifact_plan.get("preview_policy", {}) if isinstance(artifact_plan.get("preview_policy", {}), dict) else {}
    env_flag = os.getenv("AIOX_PREVIEW_LOOP", "1").strip().lower()
    enabled = bool(policy.get("enabled", True)) and env_flag not in {"0", "false", "no"}
    if not enabled:
        return {
            "enabled": False,
            "accepted": True,
            "stopped_reason": "preview_loop_disabled",
            "iterations": [],
            "artifact_plan": artifact_plan,
            "render_manifest": render_manifest,
            "plan": plan,
        }

    max_iterations = max(1, min(2, int(policy.get("max_iterations", 2) or 2)))
    accept_score = float(policy.get("accept_score", 72.0) or 72.0)
    plateau_delta = float(policy.get("plateau_delta", 2.5) or 2.5)

    current_plan = copy.deepcopy(plan)
    current_artifact_plan = copy.deepcopy(artifact_plan)
    current_render_manifest = copy.deepcopy(render_manifest)
    iterations: list[dict[str, Any]] = []
    previous_score: float | None = None
    stopped_reason = "max_iterations_reached"
    accepted = False

    for iteration in range(1, max_iterations + 1):
        preview_bundle = build_preview_bundle(current_plan, current_artifact_plan)
        preview_report = run_preview_judge(preview_bundle, current_artifact_plan, context=context)
        mutation_plan = (
            preview_report.get("mutation_plan", {})
            if isinstance(preview_report.get("mutation_plan", {}), dict)
            else {}
        )
        applied_mutations: list[dict[str, Any]] = []

        if mutation_plan.get("ok") and not bool(preview_report.get("hard_veto")):
            mutated = apply_mutation_plan(
                current_artifact_plan,
                current_render_manifest,
                current_plan,
                mutation_plan,
            )
            current_artifact_plan = mutated["artifact_plan"]
            current_render_manifest = mutated["render_manifest"]
            current_plan = mutated["plan"]
            applied_mutations = mutated.get("audit_entries", [])

        preview_report["applied_mutations"] = copy.deepcopy(applied_mutations)
        fix_plan = generate_fix_plan(preview_report, current_artifact_plan)
        iteration_record = {
            "iteration": iteration,
            "preview": preview_bundle,
            "preview_judge": preview_report,
            "mutation_plan": mutation_plan,
            "applied_mutations": applied_mutations,
            "fix_plan": fix_plan,
        }
        iterations.append(iteration_record)

        current_score = float(preview_report.get("score", 0.0) or 0.0)
        hard_veto = bool(preview_report.get("hard_veto"))
        directives = fix_plan.get("directives", []) if isinstance(fix_plan.get("directives", []), list) else []
        mutation_directives = (
            mutation_plan.get("directives", [])
            if isinstance(mutation_plan.get("directives", []), list)
            else []
        )

        if preview_report.get("accepted") or current_score >= accept_score:
            accepted = True
            stopped_reason = "accepted_for_final_render"
            break
        if hard_veto:
            stopped_reason = "hard_veto_short_circuit"
            break
        if not directives and not mutation_directives:
            stopped_reason = "no_actionable_fix_or_mutation"
            break
        if previous_score is not None and abs(current_score - previous_score) < plateau_delta:
            stopped_reason = "quality_plateau_detected"
            break

        if directives:
            applied = apply_fix_plan(current_artifact_plan, current_render_manifest, current_plan, fix_plan)
            current_artifact_plan = applied["artifact_plan"]
            current_render_manifest = applied["render_manifest"]
            current_plan = applied["plan"]
        previous_score = current_score

    return {
        "enabled": True,
        "accepted": accepted,
        "stopped_reason": stopped_reason,
        "iterations": iterations,
        "artifact_plan": current_artifact_plan,
        "render_manifest": current_render_manifest,
        "plan": current_plan,
    }
