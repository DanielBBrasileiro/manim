from __future__ import annotations

import copy
from typing import Any


def generate_fix_plan(preview_report: dict[str, Any], artifact_plan: dict[str, Any]) -> dict[str, Any]:
    issues = preview_report.get("issues", []) if isinstance(preview_report.get("issues", []), list) else []
    directives: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for issue in issues:
        if not isinstance(issue, dict):
            continue
        directive = str(issue.get("directive", "")).strip()
        target_id = str(issue.get("target_id", "")).strip()
        key = (directive, target_id)
        if not directive or key in seen:
            continue
        seen.add(key)

        if directive == "reduce_text_density":
            current_budget = int((artifact_plan.get("copy_budget", {}) or {}).get("max_words_per_frame", 5) or 5)
            directives.append(
                {
                    "action": "reduce_text_density",
                    "target_id": target_id,
                    "value": max(3, current_budget - 1),
                    "reason": issue.get("message", ""),
                }
            )
        elif directive == "increase_negative_space":
            directives.append(
                {
                    "action": "increase_negative_space",
                    "target_id": target_id,
                    "value": min(0.8, float(issue.get("metrics", {}).get("target", 0.45) or 0.45) + 0.08),
                    "reason": issue.get("message", ""),
                }
            )
        elif directive == "tighten_hierarchy":
            directives.append(
                {
                    "action": "tighten_hierarchy",
                    "target_id": target_id,
                    "value": "editorial_minimal",
                    "reason": issue.get("message", ""),
                }
            )
        elif directive == "switch_still_family":
            directives.append(
                {
                    "action": "switch_still_family",
                    "target_id": target_id,
                    "value": "poster_minimal",
                    "reason": issue.get("message", ""),
                }
            )
        elif directive == "adjust_typography_scale":
            directives.append(
                {
                    "action": "adjust_typography_scale",
                    "target_id": target_id,
                    "value": "editorial_minimal",
                    "reason": issue.get("message", ""),
                }
            )
        elif directive == "change_motion_grammar":
            directives.append(
                {
                    "action": "change_motion_grammar",
                    "target_id": target_id,
                    "value": "cinematic_restrained",
                    "reason": issue.get("message", ""),
                }
            )
        elif directive == "resolve_hard_veto":
            directives.append(
                {
                    "action": "resolve_hard_veto",
                    "target_id": target_id,
                    "value": "reduce_text_density",
                    "reason": issue.get("message", ""),
                }
            )

    return {
        "ok": bool(directives),
        "directives": directives,
        "summary": [directive["action"] for directive in directives],
    }


def apply_fix_plan(
    artifact_plan: dict[str, Any],
    render_manifest: dict[str, Any],
    plan: dict[str, Any],
    fix_plan: dict[str, Any],
) -> dict[str, Any]:
    updated_artifact_plan = copy.deepcopy(artifact_plan)
    updated_render_manifest = copy.deepcopy(render_manifest)
    updated_plan = copy.deepcopy(plan)
    directives = fix_plan.get("directives", []) if isinstance(fix_plan.get("directives", []), list) else []

    for directive in directives:
        if not isinstance(directive, dict):
            continue
        action = str(directive.get("action", "")).strip()
        target_id = str(directive.get("target_id", "")).strip()
        value = directive.get("value")
        if action == "reduce_text_density":
            _apply_reduce_text_density(updated_artifact_plan, updated_render_manifest, value)
        elif action == "increase_negative_space":
            _apply_increase_negative_space(updated_artifact_plan, updated_render_manifest, target_id, float(value or 0.5))
        elif action in {"tighten_hierarchy", "adjust_typography_scale"}:
            _apply_typography_system(updated_artifact_plan, updated_render_manifest, target_id, str(value or "editorial_minimal"))
        elif action == "switch_still_family":
            _apply_still_family(updated_artifact_plan, updated_render_manifest, target_id, str(value or "poster_minimal"))
        elif action == "change_motion_grammar":
            _apply_motion_grammar(updated_artifact_plan, updated_render_manifest, updated_plan, target_id, str(value or "cinematic_restrained"))
        elif action == "resolve_hard_veto":
            _apply_reduce_text_density(updated_artifact_plan, updated_render_manifest, 3)
            _apply_increase_negative_space(updated_artifact_plan, updated_render_manifest, target_id, 0.6)

    updated_plan["artifact_plan"] = updated_artifact_plan
    updated_plan["render_manifest"] = updated_render_manifest
    return {
        "artifact_plan": updated_artifact_plan,
        "render_manifest": updated_render_manifest,
        "plan": updated_plan,
    }


def _trim_words(value: Any, max_words: int) -> Any:
    if not isinstance(value, str):
        return value
    return " ".join(value.split()[:max_words]).strip()


def _apply_reduce_text_density(artifact_plan: dict[str, Any], render_manifest: dict[str, Any], max_words: int) -> None:
    artifact_plan.setdefault("copy_budget", {})["max_words_per_frame"] = max_words
    artifact_plan.setdefault("quality_constraints", {})["max_words_per_screen"] = max_words

    story_atoms = artifact_plan.get("story_atoms", {})
    if isinstance(story_atoms, dict):
        for key in ("title", "tagline", "thesis", "resolve_word"):
            if key in story_atoms:
                story_atoms[key] = _trim_words(story_atoms.get(key), max_words)

    for target in artifact_plan.get("targets", []):
        if not isinstance(target, dict):
            continue
        target["summary"] = _trim_words(target.get("summary"), max_words)
        for beat in target.get("beats", []):
            if isinstance(beat, dict):
                for key in ("text", "label"):
                    if key in beat:
                        beat[key] = _trim_words(beat.get(key), max_words)
        for slide in target.get("slides", []):
            if isinstance(slide, dict) and isinstance(slide.get("text_blocks"), list):
                slide["text_blocks"] = [_trim_words(block, max_words) for block in slide.get("text_blocks", [])]
        for chapter in target.get("chapters", []):
            if isinstance(chapter, dict) and "label" in chapter:
                chapter["label"] = _trim_words(chapter.get("label"), max_words)

    render_manifest["title"] = _trim_words(render_manifest.get("title"), max_words)
    render_manifest["tagline"] = _trim_words(render_manifest.get("tagline"), max_words)
    render_manifest["visual_metaphor"] = _trim_words(render_manifest.get("visual_metaphor"), max_words)
    render_manifest["resolve_word"] = _trim_words(render_manifest.get("resolve_word"), max_words)
    for cue in render_manifest.get("text_cues", []):
        if isinstance(cue, dict):
            for key in ("text", "content"):
                if key in cue:
                    cue[key] = _trim_words(cue.get(key), max_words)
    for act in render_manifest.get("acts", []):
        if isinstance(act, dict):
            for cue in act.get("text_cues", []):
                if isinstance(cue, dict):
                    for key in ("text", "content"):
                        if key in cue:
                            cue[key] = _trim_words(cue.get(key), max_words)
    for target_input in (render_manifest.get("render_inputs") or {}).values():
        if not isinstance(target_input, dict):
            continue
        for cue in target_input.get("text_cues", []):
            if isinstance(cue, dict):
                for key in ("text", "content"):
                    if key in cue:
                        cue[key] = _trim_words(cue.get(key), max_words)
        story_atoms_payload = target_input.get("story_atoms", {})
        if isinstance(story_atoms_payload, dict):
            for key in ("title", "tagline", "thesis", "resolve_word"):
                if key in story_atoms_payload:
                    story_atoms_payload[key] = _trim_words(story_atoms_payload.get(key), max_words)


def _apply_increase_negative_space(
    artifact_plan: dict[str, Any],
    render_manifest: dict[str, Any],
    target_id: str,
    value: float,
) -> None:
    artifact_plan.setdefault("quality_constraints", {})["negative_space_target"] = value
    render_manifest["negative_space_target"] = value
    for target in artifact_plan.get("targets", []):
        if not isinstance(target, dict):
            continue
        if target_id and str(target.get("id", "")).strip() != target_id:
            continue
        target["negative_space_target"] = value
        layout = target.get("editorial_layout", {})
        if isinstance(layout, dict):
            title_box = layout.get("title_box")
            eyebrow_box = layout.get("eyebrow_box")
            empty_zone = layout.get("empty_zone")
            if isinstance(title_box, dict):
                title_box["w"] = max(0.20, float(title_box.get("w", 0.3) or 0.3) - 0.05)
            if isinstance(eyebrow_box, dict):
                eyebrow_box["w"] = max(0.18, float(eyebrow_box.get("w", 0.22) or 0.22) - 0.04)
            if isinstance(empty_zone, dict):
                empty_zone["w"] = min(0.50, float(empty_zone.get("w", 0.36) or 0.36) + 0.06)
    for key, target_input in (render_manifest.get("render_inputs") or {}).items():
        if not isinstance(target_input, dict):
            continue
        if target_id and str(key).strip() != target_id:
            continue
        target_input["negative_space_target"] = value


def _apply_typography_system(
    artifact_plan: dict[str, Any],
    render_manifest: dict[str, Any],
    target_id: str,
    typography_system: str,
) -> None:
    artifact_plan["typography_system"] = typography_system
    render_manifest["typography_system"] = typography_system
    for target in artifact_plan.get("targets", []):
        if isinstance(target, dict) and str(target.get("id", "")).strip() == target_id:
            target["typography_system"] = typography_system
    target_input = (render_manifest.get("render_inputs") or {}).get(target_id)
    if isinstance(target_input, dict):
        target_input["typography_system"] = typography_system


def _apply_still_family(
    artifact_plan: dict[str, Any],
    render_manifest: dict[str, Any],
    target_id: str,
    still_family: str,
) -> None:
    artifact_plan["still_family"] = still_family
    render_manifest["still_family"] = still_family
    for target in artifact_plan.get("targets", []):
        if isinstance(target, dict) and str(target.get("id", "")).strip() == target_id:
            target["still_family"] = still_family
    target_input = (render_manifest.get("render_inputs") or {}).get(target_id)
    if isinstance(target_input, dict):
        target_input["still_family"] = still_family


def _apply_motion_grammar(
    artifact_plan: dict[str, Any],
    render_manifest: dict[str, Any],
    plan: dict[str, Any],
    target_id: str,
    motion_grammar: str,
) -> None:
    render_manifest["motion_grammar"] = motion_grammar
    plan["motion_grammar"] = motion_grammar
    if isinstance(plan.get("pacing"), dict):
        plan["pacing"]["motion_grammar"] = motion_grammar

    for target in artifact_plan.get("targets", []):
        if isinstance(target, dict) and str(target.get("id", "")).strip() == target_id:
            target["motion_grammar"] = motion_grammar
            act_profile = target.get("act_quality_profile", {})
            if isinstance(act_profile, dict):
                for profile in act_profile.values():
                    if isinstance(profile, dict):
                        profile["minimum_hold_ms"] = max(300, int(profile.get("minimum_hold_ms", 0) or 0) + 120)
                        breath_points = list(profile.get("breath_points", []) or [])
                        if 0.5 not in breath_points:
                            breath_points.append(0.5)
                        profile["breath_points"] = sorted(breath_points)

    target_input = (render_manifest.get("render_inputs") or {}).get(target_id)
    if isinstance(target_input, dict):
        target_input["motion_grammar"] = motion_grammar
