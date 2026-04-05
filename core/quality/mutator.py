"""
mutator.py — Deterministic live-loop parameter mutation.

This module only mutates fields that are consumed by the rerender path:
- negative_space_target
- accent_intensity
- grain

Discrete structural changes such as typography_system, still_family, and
motion_grammar remain in fix_plan.py.
"""

from __future__ import annotations

import copy
from typing import Any

LIMITS = {
    "negative_space_target": (0.20, 0.75),
    "accent_intensity": (0.00, 0.80),
    "grain": (0.02, 0.20),
}


def _clamp_numeric(key: str, value: float) -> float:
    low, high = LIMITS[key]
    return round(max(low, min(high, value)), 3)


def _target_lookup(artifact_plan: dict[str, Any], target_id: str) -> dict[str, Any] | None:
    for target in artifact_plan.get("targets", []):
        if isinstance(target, dict) and str(target.get("id", "")).strip() == target_id:
            return target
    return None


def _artifact_scalar(artifact_plan: dict[str, Any], target_id: str, key: str, fallback: float) -> float:
    target = _target_lookup(artifact_plan, target_id)
    raw = None
    if isinstance(target, dict) and target.get(key) is not None:
        raw = target.get(key)
    elif artifact_plan.get(key) is not None:
        raw = artifact_plan.get(key)
    else:
        raw = fallback
    return float(raw or fallback)


def build_mutation_plan(
    artifact_plan: dict[str, Any],
    findings: list[dict[str, Any]],
    objective_signals: dict[str, Any] | None = None,
) -> dict[str, Any]:
    objective_signals = objective_signals or {}
    directives: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    primary_target_id = str(artifact_plan.get("primary_target_id", "")).strip()

    for finding in findings:
        if not isinstance(finding, dict):
            continue
        code = str(finding.get("code") or finding.get("name") or "").strip().lower()
        target_id = str(finding.get("target_id", "")).strip() or primary_target_id
        if not code or not target_id:
            continue

        if code in {"poor_negative_space", "spatial_intelligence"}:
            current = _artifact_scalar(artifact_plan, target_id, "negative_space_target", 0.40)
            value = _clamp_numeric("negative_space_target", current + 0.08)
            action = "set_negative_space_target"
        elif code in {"weak_focal_point", "brand_discipline"}:
            current = _artifact_scalar(artifact_plan, target_id, "accent_intensity", 0.12)
            value = _clamp_numeric("accent_intensity", current - 0.08)
            action = "set_accent_intensity"
        elif code == "material_finish":
            current = _artifact_scalar(artifact_plan, target_id, "grain", 0.04)
            grain_variance = float(objective_signals.get("grain_variance", 0.0) or 0.0)
            delta = -0.03 if grain_variance > 0.10 else 0.02
            value = _clamp_numeric("grain", current + delta)
            action = "set_grain"
        elif code in {
            "overcrowding",
            "hierarchy_strength",
            "layout_overload",
            "flat_hierarchy",
            "motion_pacing",
            "temporal_rhythm",
            "silence_quality",
        }:
            skipped.append(
                {
                    "code": code,
                    "target_id": target_id,
                    "reason": "delegated_to_fix_plan_or_non_renderer_scalar",
                }
            )
            continue
        else:
            continue

        dedupe_key = (action, target_id)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        directives.append(
            {
                "action": action,
                "target_id": target_id,
                "value": value,
                "reason": str(finding.get("message") or finding.get("directive") or code).strip(),
                "source_code": code,
            }
        )

    return {
        "ok": bool(directives),
        "directives": directives,
        "skipped": skipped,
        "summary": [directive["action"] for directive in directives],
    }


def _record_mutation_audit(
    artifact_plan: dict[str, Any],
    render_manifest: dict[str, Any],
    plan: dict[str, Any],
    entries: list[dict[str, Any]],
) -> None:
    if not entries:
        return
    artifact_plan.setdefault("_mutation_audit", []).append(copy.deepcopy(entries))
    render_manifest.setdefault("_mutation_audit", []).append(copy.deepcopy(entries))
    plan.setdefault("_mutation_audit", []).append(copy.deepcopy(entries))


def apply_mutation_plan(
    artifact_plan: dict[str, Any],
    render_manifest: dict[str, Any],
    plan: dict[str, Any],
    mutation_plan: dict[str, Any],
) -> dict[str, Any]:
    updated_artifact_plan = copy.deepcopy(artifact_plan)
    updated_render_manifest = copy.deepcopy(render_manifest)
    updated_plan = copy.deepcopy(plan)
    directives = mutation_plan.get("directives", []) if isinstance(mutation_plan.get("directives", []), list) else []
    audit_entries: list[dict[str, Any]] = []

    for directive in directives:
        if not isinstance(directive, dict):
            continue
        action = str(directive.get("action", "")).strip()
        target_id = str(directive.get("target_id", "")).strip()
        value = directive.get("value")

        if action == "set_negative_space_target":
            audit_entries.extend(
                _apply_target_numeric(
                    updated_artifact_plan,
                    updated_render_manifest,
                    target_id,
                    "negative_space_target",
                    float(value),
                    reason=str(directive.get("reason", "")).strip(),
                    source_code=str(directive.get("source_code", "")).strip(),
                )
            )
        elif action == "set_accent_intensity":
            audit_entries.extend(
                _apply_target_numeric(
                    updated_artifact_plan,
                    updated_render_manifest,
                    target_id,
                    "accent_intensity",
                    float(value),
                    reason=str(directive.get("reason", "")).strip(),
                    source_code=str(directive.get("source_code", "")).strip(),
                )
            )
        elif action == "set_grain":
            audit_entries.extend(
                _apply_target_numeric(
                    updated_artifact_plan,
                    updated_render_manifest,
                    target_id,
                    "grain",
                    float(value),
                    reason=str(directive.get("reason", "")).strip(),
                    source_code=str(directive.get("source_code", "")).strip(),
                )
            )

    updated_plan["artifact_plan"] = updated_artifact_plan
    updated_plan["render_manifest"] = updated_render_manifest
    _record_mutation_audit(updated_artifact_plan, updated_render_manifest, updated_plan, audit_entries)
    return {
        "artifact_plan": updated_artifact_plan,
        "render_manifest": updated_render_manifest,
        "plan": updated_plan,
        "audit_entries": audit_entries,
    }


def _apply_target_numeric(
    artifact_plan: dict[str, Any],
    render_manifest: dict[str, Any],
    target_id: str,
    key: str,
    value: float,
    *,
    reason: str,
    source_code: str,
) -> list[dict[str, Any]]:
    audit_entries: list[dict[str, Any]] = []
    current_global = artifact_plan.get(key)
    if current_global is None or str(artifact_plan.get("primary_target_id", "")).strip() == target_id:
        if current_global is None or float(current_global) != value:
            audit_entries.append(
                {
                    "scope": "artifact_plan",
                    "target_id": target_id,
                    "parameter": key,
                    "old": current_global,
                    "new": value,
                    "reason": reason,
                    "source_code": source_code,
                }
            )
        artifact_plan[key] = value
        render_manifest[key] = value

    quality_constraints = artifact_plan.setdefault("quality_constraints", {})
    if key == "negative_space_target":
        quality_constraints[key] = value

    for target in artifact_plan.get("targets", []):
        if not isinstance(target, dict):
            continue
        if target_id and str(target.get("id", "")).strip() != target_id:
            continue
        old_value = target.get(key)
        if old_value is None or float(old_value) != value:
            audit_entries.append(
                {
                    "scope": "target",
                    "target_id": target_id,
                    "parameter": key,
                    "old": old_value,
                    "new": value,
                    "reason": reason,
                    "source_code": source_code,
                }
            )
        target[key] = value

    render_inputs = render_manifest.setdefault("render_inputs", {})
    target_inputs = render_inputs.get(target_id)
    if isinstance(target_inputs, dict):
        old_value = target_inputs.get(key)
        if old_value is None or float(old_value) != value:
            audit_entries.append(
                {
                    "scope": "render_input",
                    "target_id": target_id,
                    "parameter": key,
                    "old": old_value,
                    "new": value,
                    "reason": reason,
                    "source_code": source_code,
                }
            )
        target_inputs[key] = value

    return audit_entries


def mutate_render_manifest(
    manifest: dict[str, Any],
    findings: list[dict[str, Any]],
    objective_signals: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Backwards-compatible in-place mutation entrypoint.

    This is kept for side paths. The live preview loop now uses
    build_mutation_plan() + apply_mutation_plan().
    """
    mutation_plan = build_mutation_plan(manifest, findings, objective_signals)
    applied = apply_mutation_plan(manifest, manifest, {"artifact_plan": manifest, "render_manifest": manifest}, mutation_plan)
    manifest.clear()
    manifest.update(applied["artifact_plan"])
    return manifest
