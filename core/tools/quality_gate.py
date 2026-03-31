"""
quality_gate.py — lightweight quality checks for Story Engine artifact plans.
"""

from __future__ import annotations

from typing import Any


REQUIRED_STORY_ATOMS = ("thesis", "emotional_target", "visual_metaphor")


def evaluate_artifact_plan(artifact_plan: dict[str, Any]) -> dict[str, Any]:
    report = {
        "ok": True,
        "errors": [],
        "warnings": [],
        "stats": {},
    }

    story_atoms = artifact_plan.get("story_atoms", {}) if isinstance(artifact_plan, dict) else {}
    targets = artifact_plan.get("targets", []) if isinstance(artifact_plan, dict) else []
    quality_constraints = artifact_plan.get("quality_constraints", {}) if isinstance(artifact_plan, dict) else {}
    variants = artifact_plan.get("variants", []) if isinstance(artifact_plan, dict) else []
    renderer_contracts = artifact_plan.get("renderer_contracts", {}) if isinstance(artifact_plan, dict) else {}

    if int(artifact_plan.get("schema_version", 1) or 1) < 2:
        report["warnings"].append("artifact_plan_schema_legacy")

    for key in REQUIRED_STORY_ATOMS:
        if not str(story_atoms.get(key, "")).strip():
            report["errors"].append(f"missing_story_atom:{key}")

    if not isinstance(targets, list) or not targets:
        report["errors"].append("missing_targets")
    else:
        for index, target in enumerate(targets):
            if not isinstance(target, dict):
                report["errors"].append(f"invalid_target:{index}")
                continue
            _check_target(target, report)
            if str(target.get("id", "")).strip() not in renderer_contracts:
                report["warnings"].append(f"renderer_contract_missing:{target.get('id', index)}")

    max_words = int(quality_constraints.get("max_words_per_screen", 5) or 5)
    if max_words > 5:
        report["warnings"].append("max_words_per_screen_above_brand_rule")

    negative_space_target = float(quality_constraints.get("negative_space_target", 0.4) or 0.4)
    if negative_space_target < 0.3:
        report["warnings"].append("negative_space_target_below_recommended")

    if not isinstance(variants, list) or len(variants) < 3:
        report["warnings"].append("variant_count_below_recommended")

    chosen_variant = str(artifact_plan.get("chosen_variant", "")).strip()
    if chosen_variant and not any(isinstance(variant, dict) and variant.get("id") == chosen_variant for variant in variants):
        report["errors"].append("chosen_variant_missing")

    report["stats"] = {
        "target_count": len(targets) if isinstance(targets, list) else 0,
        "variant_count": len(variants) if isinstance(variants, list) else 0,
        "max_words_per_screen": max_words,
        "negative_space_target": negative_space_target,
    }
    report["ok"] = not report["errors"]
    return report


def summarize_quality_report(report: dict[str, Any]) -> str:
    lines = [
        f"Quality Gate: {'PASS' if report.get('ok') else 'FAIL'}",
        f"errors={len(report.get('errors', []))} warnings={len(report.get('warnings', []))}",
    ]
    if report.get("errors"):
        lines.append("Errors: " + ", ".join(report["errors"]))
    if report.get("warnings"):
        lines.append("Warnings: " + ", ".join(report["warnings"]))
    return "\n".join(lines)


def _check_target(target: dict[str, Any], report: dict[str, Any]) -> None:
    target_id = target.get("id") or "unknown"
    if not str(target_id).strip():
        report["errors"].append("target_missing_id")

    if not str(target.get("composition", "")).strip():
        report["errors"].append(f"target_missing_composition:{target_id}")

    render_mode = str(target.get("render_mode", "")).strip().lower()
    if render_mode not in {"video", "still", "carousel"}:
        report["errors"].append(f"target_invalid_render_mode:{target_id}")

    fmt = target.get("format", {})
    if not isinstance(fmt, dict):
        fmt = target.get("layout", {}) if isinstance(target.get("layout", {}), dict) else {}
    width = target.get("width") or fmt.get("width")
    height = target.get("height") or fmt.get("height")
    if not width or not height:
        report["errors"].append(f"target_missing_format:{target_id}")

    safe_zone = float(target.get("safe_zone", fmt.get("safe_zone", 0.0)) or 0.0)
    if safe_zone <= 0:
        report["warnings"].append(f"target_missing_safe_zone:{target_id}")

    text_blocks = []
    for beat in target.get("beats", []):
        if isinstance(beat, dict):
            text_blocks.append(str(beat.get("text", beat.get("label", ""))).strip())
    for slide in target.get("slides", []):
        if isinstance(slide, dict):
            text_blocks.extend(
                str(block).strip()
                for block in slide.get("text_blocks", [])
                if str(block).strip()
            )
    for chapter in target.get("chapters", []):
        if isinstance(chapter, dict):
            text_blocks.append(str(chapter.get("label", "")).strip())

    for block in text_blocks:
        if len(block.split()) > 5:
            report["warnings"].append(f"text_block_above_word_limit:{target_id}:{block}")

    if render_mode == "carousel":
        slides = target.get("slides", [])
        if not isinstance(slides, list) or not (5 <= len(slides) <= 9):
            report["errors"].append(f"carousel_slide_count_out_of_range:{target_id}")
