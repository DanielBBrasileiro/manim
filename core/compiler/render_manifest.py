"""
render_manifest.py — Builds the cinematic render manifest from a creative plan.

Extracted from creative_compiler.py to keep modules under 500 lines.
"""
import copy
from pathlib import Path
from typing import Any

import yaml
from core.compiler.reference_direction import reference_value_for_target
from core.compiler.project_profile import get_project_value
from core.intelligence.model_profiles import get_active_profile

ROOT = Path(__file__).resolve().parent.parent.parent

TEXT_WORD_LIMIT = 5
DEFAULT_CAMERA_BY_ACT = {
    "genesis": "static_breathe",
    "turbulence": "track_subject",
    "resolution": "static_breathe",
}
DEFAULT_PRIMITIVES_BY_ACT = {
    "genesis": ["living_curve"],
    "turbulence": ["particle_system"],
    "resolution": ["living_curve", "neural_grid"],
}
DEFAULT_EMOTION_BY_ACT = {
    "genesis": "curiosity",
    "turbulence": "tension",
    "resolution": "mastery",
}
DEFAULT_TENSION_BY_ACT = {
    "genesis": "low",
    "turbulence": "high",
    "resolution": "medium",
}
DEFAULT_RESOLVE_BY_ARCHETYPE = {
    "emergence": "Clarity",
    "chaos_to_order": "Resolve",
    "order_to_chaos": "Rupture",
    "fragmented_reveal": "Signal",
    "loop_stability": "Stillness",
    "gravitational_collapse": "Gravity",
}
DEFAULT_OUTPUT_TARGET = "short_cinematic_vertical"


def build_render_manifest(plan: dict, seed: dict | str) -> dict:
    brief = _coerce_brief(seed)
    narrative_contract = _load_contract("contracts/narrative.yaml")
    layout_contract = _load_contract("contracts/layout.yaml")
    artifact_plan = plan.get("artifact_plan") or build_artifact_plan(plan, seed)
    primary_target = artifact_plan.get("primary_target", {})
    duration = float(plan.get("duration", 12) or 12.0)
    fps = int(primary_target.get("fps") or 60)

    acts = _build_act_windows(duration, plan, narrative_contract)
    text_beats = _collect_text_beats(brief, acts, duration, plan)
    cues_by_act: dict[str, list[dict]] = {act["id"]: [] for act in acts}
    for cue in text_beats:
        cues_by_act.setdefault(cue["act"], []).append(cue)

    for act in acts:
        act["text_cues"] = cues_by_act.get(act["id"], [])

    resolve_word = _word_cap(
        brief.get("resolve_word")
        or brief.get("final_signature_word")
        or DEFAULT_RESOLVE_BY_ARCHETYPE.get(plan.get("archetype"), "AIOX"),
        limit=2,
    )
    render_inputs = _build_render_inputs(
        artifact_plan=artifact_plan,
        acts=acts,
        text_beats=text_beats,
        duration=duration,
        fps=fps,
        layout_contract=layout_contract,
        plan=plan,
        brief=brief,
    )

    return {
        "duration": duration,
        "duration_in_frames": int(round(duration * fps)),
        "fps": fps,
        "primary_target": primary_target,
        "targets": artifact_plan.get("targets", []),
        "artifact_plan": artifact_plan,
        "story_atoms": artifact_plan.get("story_atoms", {}),
        "style_pack": artifact_plan.get("style_pack"),
        "style_pack_ids": artifact_plan.get("style_pack_ids", []),
        "motion_grammar": artifact_plan.get("motion_grammar"),
        "typography_system": artifact_plan.get("typography_system"),
        "still_family": artifact_plan.get("still_family"),
        "color_mode": artifact_plan.get("color_mode"),
        "negative_space_target": artifact_plan.get("negative_space_target"),
        "accent_intensity": artifact_plan.get("accent_intensity"),
        "grain": artifact_plan.get("grain"),
        "material_hint": artifact_plan.get("material_hint"),
        "quality_constraints": artifact_plan.get("quality_constraints", {}),
        "quality_mode": artifact_plan.get("quality_mode", "absolute"),
        "premium_targets": artifact_plan.get("premium_targets", []),
        "preview_policy": artifact_plan.get("preview_policy", {}),
        "reference_native_direction": artifact_plan.get("reference_native_direction", {}),
        "reference_evidence": artifact_plan.get("reference_evidence", []),
        "qa_frames": artifact_plan.get("qa_frames"),
        "auto_iterate_max": artifact_plan.get("auto_iterate_max"),
        "brand_veto_policy": artifact_plan.get("brand_veto_policy", {}),
        "render_inputs": render_inputs,
        "title": brief.get("title") or "AIOX v4.0",
        "tagline": brief.get("tagline") or "Invisible Architecture",
        "emotional_target": brief.get("emotional_target") or _infer_emotional_target(plan),
        "visual_metaphor": brief.get("visual_metaphor") or _infer_visual_metaphor(plan),
        "resolve_word": resolve_word,
        "acts": acts,
        "text_cues": text_beats,
        "audio": {
            "enabled": True,
            "bed": "audio/aiox_signal_bed.m4a",
            "gain": 0.3,
        },
        "layout": primary_target.get("layout", layout_contract.get("formats", {}).get("vertical_9_16", {})),
        "seed": str(seed),
    }


def build_artifact_plan(plan: dict, seed: dict | str) -> dict:
    brief = _coerce_brief(seed)
    narrative_contract = _load_contract("contracts/narrative.yaml")
    layout_contract = _load_contract("contracts/layout.yaml")
    global_laws = _load_contract("contracts/global_laws.yaml")
    design_canon = _load_contract("contracts/design_canon.yaml")
    formats = layout_contract.get("formats", {}) if isinstance(layout_contract.get("formats", {}), dict) else {}
    target_catalog = _build_target_catalog(layout_contract, formats)
    requested_output_tokens = _extract_requested_output_tokens(seed, brief)
    requested_ids = _resolve_requested_target_ids(
        brief,
        plan,
        target_catalog,
        formats,
        requested_output_tokens=requested_output_tokens,
    )
    project_id = plan.get("project_id")
    duration = float(plan.get("duration", 12) or 12.0)
    acts = _build_act_windows(duration, plan, narrative_contract)
    text_beats = _collect_text_beats(brief, acts, duration, plan)
    story_atoms = _build_story_atoms(plan, brief)
    quality_constraints = _build_quality_constraints(narrative_contract, global_laws, design_canon, plan)
    style_pack_ids = _resolve_style_pack_ids(seed, brief=brief, plan=plan)
    style_retrieval_results = _build_style_retrieval_results(brief, style_pack_ids)
    variants = _build_variants(plan, story_atoms, style_pack_ids)

    selected_targets: list[dict[str, Any]] = []
    for target_id in requested_ids:
        target_spec = target_catalog.get(target_id)
        if target_spec and target_spec not in selected_targets:
            selected_targets.append(
                _expand_target(
                    target_spec=target_spec,
                    plan=plan,
                    story_atoms=story_atoms,
                    acts=acts,
                    text_beats=text_beats,
                    duration=duration,
                    design_canon=design_canon,
                )
            )

    if not selected_targets:
        default_target_id = _default_output_target(layout_contract, target_catalog)
        default_target = target_catalog.get(default_target_id)
        if default_target:
            selected_targets = [
                _expand_target(
                    target_spec=default_target,
                    plan=plan,
                    story_atoms=story_atoms,
                    acts=acts,
                    text_beats=text_beats,
                    duration=duration,
                    design_canon=design_canon,
                )
            ]

    primary_target = selected_targets[0] if selected_targets else {}
    primary_style_pack_id = str(
        primary_target.get("style_pack")
        or (style_pack_ids[0] if style_pack_ids else "silent_luxury")
    ).strip() or "silent_luxury"
    primary_style_pack = _style_pack_contract(primary_style_pack_id)
    chosen_variant = variants[0]["id"] if variants else "variant_01"
    premium_targets = _build_premium_targets(selected_targets)
    return {
        "schema_version": 3,
        "primary_target_id": primary_target.get("id", DEFAULT_OUTPUT_TARGET),
        "primary_target": primary_target,
        "targets": selected_targets,
        "requested_targets": requested_ids,
        "format": primary_target.get("format_id", "vertical_9_16"),
        "story_atoms": story_atoms,
        "style_pack": primary_style_pack_id,
        "style_pack_ids": style_pack_ids,
        "motion_grammar": primary_target.get("motion_grammar", primary_style_pack.get("motion_grammar")),
        "typography_system": primary_target.get("typography_system", primary_style_pack.get("typography_system")),
        "still_family": primary_target.get("still_family", primary_style_pack.get("still_family")),
        "color_mode": primary_target.get("color_mode", primary_style_pack.get("color_mode")),
        "negative_space_target": primary_target.get("negative_space_target", primary_style_pack.get("negative_space_target")),
        "accent_intensity": primary_target.get("accent_intensity", primary_style_pack.get("accent_intensity")),
        "grain": primary_target.get("grain", primary_style_pack.get("grain")),
        "material_hint": primary_target.get("material_hint", "editorial_flat"),
        "quality_constraints": quality_constraints,
        "quality_tier": "lab_absolute",
        "quality_mode": "absolute",
        "premium_targets": premium_targets,
        "qa_frames": int(quality_constraints.get("qa_frames", 5) or 5),
        "auto_iterate_max": int(quality_constraints.get("auto_iterate_max", 1) or 1),
        "judge_stack": [
            "brand_precheck",
            "structural_gate",
            "visual_judge_fast",
            "objective_metrics",
            "visual_judge_heavy",
            "variant_ranker",
        ],
        "brand_veto_policy": {
            "hero_target": "strict",
            "video_targets": "degrade_to_fallback_pass",
            "fallback_never_premium": True,
        },
        "variants": variants,
        "variant_scores": {},
        "chosen_variant": chosen_variant,
        "chosen_variant_reason": "initial_priority_seed",
        "review_session_id": None,
        "reference_native_direction": copy.deepcopy(plan.get("reference_native_direction", {}))
        if isinstance(plan.get("reference_native_direction", {}), dict)
        else {},
        "reference_evidence": copy.deepcopy(
            (
                plan.get("reference_native_direction", {})
                if isinstance(plan.get("reference_native_direction", {}), dict)
                else {}
            ).get("reference_evidence", [])
        ),
        "style_retrieval_results": style_retrieval_results,
        "objective_metrics": {
            "still_aesthetic_model": "hpsv2_optional",
            "video_benchmark": "vbench_subset_optional",
        },
        "family_spec": {
            target.get("id", f"target_{index}"): target.get("family_spec", "short_cinematic")
            for index, target in enumerate(selected_targets)
        },
        "motion_system": {
            "cadence_profile": "premium_lab",
            "negative_space_regime": "strict",
            "resolve_hold_sec": 1.5,
        },
        "preview_policy": {
            "enabled": True,
            "max_iterations": min(2, int(quality_constraints.get("auto_iterate_max", 1) or 1) + 1),
            "accept_score": 72.0,
            "plateau_delta": 2.5,
        },
        "copy_budget": {
            "max_words_per_frame": int(quality_constraints.get("max_words_per_screen", 5) or 5),
            "target_silence_ratio": float(quality_constraints.get("silence_ratio", 0.3) or 0.3),
        },
        "renderer_contracts": _build_renderer_contracts(selected_targets),
        "fallback_policy": _build_fallback_policy(selected_targets),
        "metrics_hooks": [
            "llm_latency_ms",
            "native_render_success",
            "fallback_rate",
            "artifact_updated",
            "negative_space_target",
            "judge_disagreement_rate",
            "premium_success_rate",
        ],
        "beat_map": {
            target.get("id", f"target_{index}"): [
                beat.get("label", beat.get("text", ""))
                for beat in target.get("beats", [])
                if isinstance(beat, dict)
            ]
            for index, target in enumerate(selected_targets)
        },
        "distribution_mode": "multi_target" if len(selected_targets) > 1 else "single_target",
        "brief": {
            "title": brief.get("title"),
            "tagline": brief.get("tagline"),
            "format": brief.get("format") or brief.get("platform"),
            "platform": brief.get("platform"),
            "audience": brief.get("audience"),
            "thesis": brief.get("thesis"),
            "output_targets": requested_output_tokens,
        },
        "project_id": project_id,
        "project_profile_id": project_id,
    }


def _build_style_retrieval_results(brief: dict[str, Any], style_pack_ids: list[str]) -> list[dict[str, Any]]:
    try:
        from core.runtime.style_retriever import search_style_packs
    except Exception:
        return [{"pack_id": pack_id, "score": 1.0, "matched_terms": []} for pack_id in style_pack_ids]

    query = " ".join(
        part
        for part in [
            str(brief.get("title", "")).strip(),
            str(brief.get("thesis", "")).strip(),
            str(brief.get("visual_metaphor", "")).strip(),
            str(brief.get("emotional_target", "")).strip(),
        ]
        if part
    ).strip()
    if not query:
        return [{"pack_id": pack_id, "score": 1.0, "matched_terms": []} for pack_id in style_pack_ids]

    results = search_style_packs(query, limit=5)
    if style_pack_ids:
        requested = {pack_id: {"pack_id": pack_id, "score": 1.0, "matched_terms": []} for pack_id in style_pack_ids}
        for item in results:
            if item.get("pack_id") in requested:
                requested[item["pack_id"]] = item
        return list(requested.values()) + [item for item in results if item.get("pack_id") not in requested]
    return results


def _coerce_brief(seed: dict | str) -> dict:
    if not isinstance(seed, dict):
        return {"prompt": str(seed)}

    creative_seed = seed.get("creative_seed")
    if isinstance(creative_seed, dict):
        return copy.deepcopy(creative_seed)

    if len(seed) == 1:
        only_value = next(iter(seed.values()))
        if isinstance(only_value, dict):
            return copy.deepcopy(only_value)

    return copy.deepcopy(seed)


def _load_contract(relative_path: str) -> dict:
    path = ROOT / relative_path
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _extract_requested_output_tokens(seed: dict | str, brief: dict) -> list[str]:
    tokens: list[str] = []
    if isinstance(seed, dict):
        output = seed.get("output", {})
        if isinstance(output, dict):
            tokens.extend(_string_list(output.get("targets")))
        tokens.extend(_string_list(seed.get("output_targets")))
    tokens.extend(_string_list(brief.get("output_targets")))
    tokens.extend(_string_list(brief.get("distribution_targets")))

    deduped: list[str] = []
    for token in tokens:
        if token not in deduped:
            deduped.append(token)
    return deduped


def _build_target_catalog(layout_contract: dict, formats: dict[str, dict]) -> dict[str, dict]:
    catalog: dict[str, dict] = {}
    raw_targets = layout_contract.get("output_targets", {})
    if not isinstance(raw_targets, dict):
        return catalog

    for target_id, target in raw_targets.items():
        if not isinstance(target, dict):
            continue
        format_id = str(target.get("format", target.get("format_id", ""))).strip() or target_id
        format_layout = copy.deepcopy(formats.get(format_id, {})) if isinstance(formats.get(format_id, {}), dict) else {}
        width = int(target.get("width", format_layout.get("width", 0)) or 0)
        height = int(target.get("height", format_layout.get("height", 0)) or 0)
        fps = int(target.get("fps", format_layout.get("fps", 0)) or 0)
        safe_zone = float(target.get("safe_zone", format_layout.get("safe_zone", 0.0)) or 0.0)
        catalog[target_id] = {
            "id": target_id,
            "format_id": format_id,
            "channel": str(target.get("channel", "")).strip(),
            "purpose": str(target.get("purpose", "")).strip(),
            "priority": int(target.get("priority", 0) or 0),
            "default": bool(target.get("default", False)),
            "preferred_channels": _string_list(target.get("preferred_channels")),
            "legacy_aliases": _string_list(target.get("legacy_aliases")),
            "width": width,
            "height": height,
            "fps": fps,
            "safe_zone": safe_zone,
            "layout": format_layout,
            "alias": str(target.get("alias", "")).strip(),
            "render_mode": str(target.get("render_mode", "video")).strip() or "video",
            "composition": str(target.get("composition", "")).strip(),
            "legacy_composition": str(target.get("legacy_composition", "")).strip(),
            "label": str(target.get("label", target_id)).strip() or target_id,
            "native_support": bool(target.get("native_support", True)),
            "output_ext": str(target.get("output_ext", "")).strip(),
            "min_slides": int(target.get("min_slides", 5) or 5),
            "max_slides": int(target.get("max_slides", 9) or 9),
        }

    return catalog


def _resolve_requested_target_ids(
    brief: dict,
    plan: dict,
    target_catalog: dict[str, dict],
    formats: dict[str, dict],
    requested_output_tokens: list[str] | None = None,
) -> list[str]:
    requested: list[str] = []
    explicit_sources = [
        requested_output_tokens or [],
        plan.get("targets"),
        plan.get("llm_scene_plan", {}).get("targets", []),
        brief.get("target"),
    ]
    fallback_sources = [
        brief.get("platform"),
        brief.get("format"),
        get_project_value(plan, "targets"),
    ]

    for source in explicit_sources:
        if isinstance(source, list):
            for item in source:
                requested.extend(_map_target_token(str(item), target_catalog, formats))
        elif isinstance(source, str):
            requested.extend(_map_target_token(source, target_catalog, formats))

    if not requested:
        for source in fallback_sources:
            if isinstance(source, list):
                for item in source:
                    requested.extend(_map_target_token(str(item), target_catalog, formats))
            elif isinstance(source, str):
                requested.extend(_map_target_token(source, target_catalog, formats))

    deduped: list[str] = []
    for target_id in requested:
        if target_id not in deduped:
            deduped.append(target_id)
    return deduped


def _map_target_token(token: str, target_catalog: dict[str, dict], formats: dict[str, dict]) -> list[str]:
    value = str(token).strip()
    if not value:
        return []
    if value in target_catalog:
        return [value]

    matches = [target_id for target_id, spec in target_catalog.items() if spec.get("format_id") == value]
    if matches:
        return [matches[0]]

    channel_matches = [
        target_id
        for target_id, spec in target_catalog.items()
        if value == spec.get("channel")
        or value in spec.get("preferred_channels", [])
        or value in spec.get("legacy_aliases", [])
    ]
    if channel_matches:
        return [channel_matches[0]]

    format_matches = [format_id for format_id in formats.keys() if format_id == value]
    if format_matches:
        for target_id, spec in target_catalog.items():
            if spec.get("format_id") == format_matches[0]:
                return [target_id]
        return [_default_output_target({}, target_catalog)]

    return []


def _default_output_target(layout_contract: dict, target_catalog: dict[str, dict]) -> str:
    default_target = str(layout_contract.get("default_output_target", "")).strip()
    if default_target and default_target in target_catalog:
        return default_target

    for target_id, spec in target_catalog.items():
        if spec.get("default"):
            return target_id

    if DEFAULT_OUTPUT_TARGET in target_catalog:
        return DEFAULT_OUTPUT_TARGET

    return next(iter(target_catalog.keys()), DEFAULT_OUTPUT_TARGET)


def _resolve_style_pack_ids(seed: dict | str, brief: dict | None = None, plan: dict | None = None) -> list[str]:
    candidates: list[str] = []

    def _append_style_pack_values(source: Any) -> None:
        if not isinstance(source, dict):
            return
        for key in ("style_pack", "style_pack_id"):
            value = str(source.get(key, "")).strip()
            if value:
                candidates.append(value)
        values = source.get("style_pack_ids") or source.get("style_packs")
        if isinstance(values, list):
            candidates.extend(str(item).strip() for item in values if str(item).strip())

    if isinstance(seed, dict):
        _append_style_pack_values(seed)
        references = seed.get("references", {})
        if isinstance(references, dict):
            _append_style_pack_values(references)
            translation = references.get("aiox_translation") or references.get("reference_native_direction")
            if isinstance(translation, dict):
                value = str(translation.get("style_pack") or translation.get("style_pack_hint") or "").strip()
                if value:
                    candidates.append(value)

    _append_style_pack_values(brief)
    _append_style_pack_values(plan)
    if isinstance(plan, dict):
        reference_direction = plan.get("reference_native_direction", {})
        if isinstance(reference_direction, dict):
            resolved = reference_direction.get("resolved", {})
            if isinstance(resolved, dict):
                value = str(resolved.get("style_pack", "")).strip()
                if value:
                    candidates.append(value)

    deduped: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in deduped:
            deduped.append(candidate)
    return deduped


def _style_pack_contract(style_pack_id: str | None) -> dict[str, Any]:
    from core.quality.contract_loader import load_quality_contract

    contract = load_quality_contract()
    requested = str(style_pack_id or "").strip()
    if requested:
        style_pack = contract.get_style_pack(requested)
        if isinstance(style_pack, dict) and style_pack:
            return style_pack

    fallback = contract.get_style_pack("silent_luxury")
    if isinstance(fallback, dict) and fallback:
        return fallback

    return {
        "id": "silent_luxury",
        "typography_system": "editorial_minimal",
        "motion_grammar": "cinematic_restrained",
        "still_family": "poster_minimal",
        "color_mode": "monochrome_pure",
        "negative_space_target": 0.65,
        "accent_intensity": 0.1,
        "grain": 0.04,
    }


def _build_story_atoms(plan: dict, brief: dict) -> dict[str, Any]:
    return {
        "title": brief.get("title") or "AIOX",
        "tagline": brief.get("tagline") or "Invisible Architecture",
        "thesis": brief.get("thesis") or _infer_visual_metaphor(plan),
        "audience": brief.get("audience") or "B2B brand and tech audience",
        "emotional_target": brief.get("emotional_target") or _infer_emotional_target(plan),
        "visual_metaphor": brief.get("visual_metaphor") or _infer_visual_metaphor(plan),
        "resolve_word": _word_cap(
            brief.get("resolve_word")
            or brief.get("final_signature_word")
            or DEFAULT_RESOLVE_BY_ARCHETYPE.get(plan.get("archetype"), "AIOX"),
            limit=2,
        ),
    }


def _build_quality_constraints(
    narrative_contract: dict,
    global_laws: dict,
    design_canon: dict,
    plan: dict,
) -> dict[str, Any]:
    pacing = narrative_contract.get("pacing", {}) if isinstance(narrative_contract.get("pacing", {}), dict) else {}
    constraints = global_laws.get("constraints", {}) if isinstance(global_laws.get("constraints", {}), dict) else {}
    canon_typography = design_canon.get("typography", {}) if isinstance(design_canon.get("typography", {}), dict) else {}
    canon_sizing = canon_typography.get("sizing", {}) if isinstance(canon_typography.get("sizing", {}), dict) else {}
    canon_math = design_canon.get("mathematical_precision", {}) if isinstance(design_canon.get("mathematical_precision", {}), dict) else {}
    pacing_profile = plan.get("pacing_profile", {}) if isinstance(plan.get("pacing_profile", {}), dict) else {}
    return {
        "text_minimum_gap": pacing_profile.get("text_minimum_gap_sec", pacing.get("text_minimum_gap", "1.5s")),
        "max_words_per_screen": int(canon_sizing.get("max_words_per_screen", pacing.get("max_text_words_per_screen", TEXT_WORD_LIMIT)) or TEXT_WORD_LIMIT),
        "silence_ratio": float(pacing_profile.get("silence_ratio", pacing.get("silence_ratio", 0.3)) or 0.3),
        "negative_space_target": float(canon_math.get("min_negative_space", constraints.get("min_negative_space", 0.4)) or 0.4),
        "max_colors": int(constraints.get("max_colors", 2) or 2),
        "contrast_floor": 4.5,
        "typography_conformance": "strict",
        "qa_frames": 5,
        "auto_iterate_max": 1,
    }


def _build_variants(plan: dict, story_atoms: dict[str, Any], style_pack_ids: list[str]) -> list[dict[str, Any]]:
    profile = get_active_profile()
    requested_count = max(3, min(int(profile.render_preferences.get("variant_count", 3) or 3), 5))
    primary_style = style_pack_ids[0] if style_pack_ids else "brand_core"
    style_candidates = [primary_style, "masterize_mid_path", "editorial_precision", "signal_frame", "architectural_resolve"]
    composition_modes = ["poster_focus", "single_metaphor", "editorial_spine", "architecture_reveal", "resolve_lockup"]
    typography_behaviors = ["quiet_hierarchy", "thesis_poster", "whisper_to_resolve", "editorial_grid", "hero_lockup"]
    shot_grammars = ["single_curve", "contained_break", "mid_event_flip", "grid_reveal", "calm_resolve"]

    variants: list[dict[str, Any]] = []
    for index in range(requested_count):
        variant_id = f"variant_{index + 1:02d}"
        variants.append(
            {
                "id": variant_id,
                "label": f"Variant {index + 1}",
                "style_pack_id": style_candidates[index % len(style_candidates)],
                "composition_mode": composition_modes[index % len(composition_modes)],
                "typography_behavior": typography_behaviors[index % len(typography_behaviors)],
                "shot_grammar": shot_grammars[index % len(shot_grammars)],
                "resolve_word": story_atoms.get("resolve_word"),
                "thesis": story_atoms.get("thesis"),
                "archetype": plan.get("archetype"),
                "hero_target": profile.render_preferences.get("hero_target", "linkedin_feed_4_5"),
            }
        )
    return variants


def _build_premium_targets(selected_targets: list[dict[str, Any]]) -> list[str]:
    ordered = ["linkedin_feed_4_5", "short_cinematic_vertical"]
    requested = {
        str(target.get("id", "")).strip()
        for target in selected_targets
        if isinstance(target, dict) and str(target.get("id", "")).strip()
    }
    premium_targets = [target_id for target_id in ordered if target_id in requested]
    if not premium_targets and selected_targets:
        first_target = str(selected_targets[0].get("id", "")).strip()
        if first_target:
            premium_targets.append(first_target)
    return premium_targets


def _build_renderer_contracts(selected_targets: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    contracts: dict[str, dict[str, Any]] = {}
    for target in selected_targets:
        target_id = str(target.get("id", "")).strip()
        if not target_id:
            continue
        render_mode = str(target.get("render_mode", "video")).strip().lower()
        contracts[target_id] = {
            "target_id": target_id,
            "composition": target.get("composition"),
            "render_mode": render_mode,
            "style_pack": target.get("style_pack"),
            "motion_grammar": target.get("motion_grammar"),
            "color_mode": target.get("color_mode"),
            "native_engine": "remotion",
            "fallback_engine": "fallback_artifact_renderer",
            "requires_base_video": render_mode == "video" and target_id == "short_cinematic_vertical",
            "native_support": bool(target.get("native_support", True)),
        }
    return contracts


def _build_fallback_policy(selected_targets: list[dict[str, Any]]) -> dict[str, Any]:
    hero_target = next((str(target.get("id")) for target in selected_targets if str(target.get("id")) == "linkedin_feed_4_5"), None)
    return {
        "mode": "native_then_fallback",
        "hero_target": hero_target or "linkedin_feed_4_5",
        "max_native_attempts": 1,
        "fallback_on_timeout": True,
        "fallback_on_render_error": True,
    }


def _expand_target(
    target_spec: dict[str, Any],
    plan: dict,
    story_atoms: dict[str, Any],
    acts: list[dict],
    text_beats: list[dict],
    duration: float,
    design_canon: dict[str, Any] | None = None,
) -> dict[str, Any]:
    target = copy.deepcopy(target_spec)
    target_reference = _target_reference_direction(plan, target)
    target["style_pack"] = _target_style_pack_id(plan, target, target_reference=target_reference)
    target_style_pack = _style_pack_contract(target["style_pack"])
    target["typography_system"] = _target_typography_system(plan, target, target_reference=target_reference, target_style_pack=target_style_pack)
    target["still_family"] = _target_still_family(plan, target, target_reference=target_reference, target_style_pack=target_style_pack)
    motion_grammar = _resolve_target_field(
        plan,
        target,
        "motion_grammar",
        target_reference=target_reference,
        project_value=get_project_value(plan, "motion_grammar"),
        style_pack_value=target_style_pack.get("motion_grammar"),
        fallback="cinematic_restrained",
    )
    color_mode = _resolve_target_field(
        plan,
        target,
        "color_mode",
        target_reference=target_reference,
        style_pack_value=target_style_pack.get("color_mode"),
        fallback="monochrome_pure",
    )
    negative_space_target = _resolve_target_field(
        plan,
        target,
        "negative_space_target",
        target_reference=target_reference,
        project_value=get_project_value(plan, "negative_space_target"),
        style_pack_value=target_style_pack.get("negative_space_target"),
        fallback=0.65,
    )
    accent_intensity = _resolve_target_field(
        plan,
        target,
        "accent_intensity",
        target_reference=target_reference,
        project_value=get_project_value(plan, "accent_intensity"),
        style_pack_value=target_style_pack.get("accent_intensity"),
        fallback=0.1,
    )
    grain = _resolve_target_field(
        plan,
        target,
        "grain",
        target_reference=target_reference,
        project_value=get_project_value(plan, "grain"),
        style_pack_value=target_style_pack.get("grain"),
        fallback=0.04,
    )
    material_hint = _resolve_target_field(
        plan,
        target,
        "material_hint",
        target_reference=target_reference,
        fallback="editorial_flat",
    )
    target["motion_grammar"] = str(motion_grammar).strip()
    target["color_mode"] = str(color_mode).strip()
    target["negative_space_target"] = float(negative_space_target)
    target["accent_intensity"] = float(accent_intensity)
    target["grain"] = float(grain)
    target["material_hint"] = str(material_hint).strip()
    target["judge_profile"] = _target_judge_profile(target)
    target["summary"] = _target_summary(target, story_atoms)
    target["duration_sec"] = _target_duration(target, duration)
    target["beats"] = _build_target_beats(target, story_atoms, acts, text_beats)
    target["slides"] = _build_target_slides(target, story_atoms, text_beats)
    target["chapters"] = _build_target_chapters(target, story_atoms, acts, text_beats)
    target["story_atoms"] = story_atoms
    target["still_frame"] = _target_still_frame(target, duration)
    target["plan_archetype"] = plan.get("archetype")
    target["quality_mode"] = "absolute" if str(target.get("id", "")).strip() == "linkedin_feed_4_5" else plan.get("quality_mode", "absolute")
    target["family_spec"] = _target_family_spec(target)
    target["act_quality_profile"] = _build_act_quality_profile(plan, acts)
    target["post_fx_profile"] = _target_post_fx_profile(target)
    target["qa_sampling_frames"] = _build_qa_sampling_frames(target, acts, duration)
    target["poster_test_frames"] = _build_poster_test_frames(target, acts, duration)
    target["editorial_layout"] = _build_editorial_layout(target, design_canon or {})
    target["master_asset_strategy"] = _build_master_asset_strategy(target)
    target["still_base_strategy"] = _build_still_base_strategy(target)
    return target


def _target_style_pack_id(plan: dict[str, Any], target: dict[str, Any], *, target_reference: dict[str, Any] | None = None) -> str:
    explicit_target_style_pack = str(target.get("style_pack", "")).strip()
    if explicit_target_style_pack:
        return explicit_target_style_pack

    explicit_style_pack = str(plan.get("style_pack", "")).strip()
    if explicit_style_pack:
        return explicit_style_pack

    style_pack_ids = [str(item).strip() for item in plan.get("style_pack_ids", []) if str(item).strip()]
    if style_pack_ids:
        return style_pack_ids[0]

    reference_style_pack = str((target_reference or {}).get("style_pack") or "").strip()
    if reference_style_pack:
        return reference_style_pack

    project_style_pack = str(get_project_value(plan, "style_pack") or "").strip()
    if project_style_pack:
        return project_style_pack

    render_mode = str(target.get("render_mode", "video")).strip().lower()
    family = _target_family_spec(target)

    if render_mode == "still" or family in {"hero_poster", "thumbnail"}:
        preferred = "silent_luxury"
    else:
        preferred = "kinetic_editorial"

    return preferred


def _target_typography_system(
    plan: dict[str, Any],
    target: dict[str, Any],
    *,
    target_reference: dict[str, Any] | None = None,
    target_style_pack: dict[str, Any] | None = None,
) -> str:
    typography_system = str(
        _resolve_target_field(
            plan,
            target,
            "typography_system",
            target_reference=target_reference or {},
            project_value=get_project_value(plan, "typography_system"),
            style_pack_value=(target_style_pack or {}).get("typography_system"),
        )
        or ""
    ).strip()
    if typography_system:
        return typography_system

    family = _target_family_spec(target)
    if family in {"hero_poster", "thumbnail"}:
        return "editorial_minimal"
    return "editorial_dense"


def _target_still_family(
    plan: dict[str, Any],
    target: dict[str, Any],
    *,
    target_reference: dict[str, Any] | None = None,
    target_style_pack: dict[str, Any] | None = None,
) -> str | None:
    render_mode = str(target.get("render_mode", "video")).strip().lower()
    if render_mode not in {"still", "carousel"}:
        return None

    still_family = str(
        _resolve_target_field(
            plan,
            target,
            "still_family",
            target_reference=target_reference or {},
            project_value=get_project_value(plan, "still_family"),
            style_pack_value=(target_style_pack or {}).get("still_family"),
        )
        or ""
    ).strip()
    if still_family:
        return still_family

    family = _target_family_spec(target)
    if family in {"hero_poster", "thumbnail"}:
        return "poster_minimal"
    return "editorial_portrait"


def _resolve_target_field(
    plan: dict[str, Any],
    target: dict[str, Any],
    key: str,
    *,
    target_reference: dict[str, Any] | None = None,
    project_value: Any = None,
    style_pack_value: Any = None,
    fallback: Any = None,
) -> Any:
    explicit_target = target.get(key)
    explicit_plan = plan.get(key)
    reference_value = (target_reference or {}).get(key)
    for candidate in (explicit_target, explicit_plan, reference_value, project_value, style_pack_value, fallback):
        if candidate not in {None, ""}:
            return candidate
    return None


def _target_judge_profile(target: dict[str, Any]) -> str:
    render_mode = str(target.get("render_mode", "video")).strip().lower()
    if render_mode == "still":
        return "premium_still"
    return "motion_frame"


def _target_reference_direction(plan: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    target_id = str(target.get("id", "")).strip()
    keys = ("style_pack", "typography_system", "still_family", "motion_grammar", "color_mode", "negative_space_target", "accent_intensity", "grain", "material_hint")
    resolved: dict[str, Any] = {}
    for key in keys:
        value = reference_value_for_target(plan, target_id, key)
        if value not in {None, ""}:
            resolved[key] = value
    return resolved


def _build_editorial_layout_dict(target: dict[str, Any], design_canon: dict[str, Any]) -> dict[str, Any]:
    layout_id = str(target.get("still_family") or "poster_minimal").strip().lower()
    design_layout = design_canon.get(layout_id, {})

    return {
        "family": layout_id,
        "grammar": design_layout.get("grammar"),
        "safe_margin_px": design_layout.get("safe_margin_px"),
        "hero_zone": design_layout.get("hero_zone"),
        "support_zone": design_layout.get("support_zone"),
        "empty_zone": design_layout.get("empty_zone"),
        "focal_zone": design_layout.get("focal_zone"),
        "title_box": design_layout.get("title_box"),
        "eyebrow_box": design_layout.get("eyebrow_box"),
        "accent_anchor": design_layout.get("accent_anchor"),
        "asset_crop": design_layout.get("asset_crop"),
    }


def _build_editorial_layout(target: dict[str, Any], design_canon: dict[str, Any]) -> dict[str, Any]:
    math_precision = (
        design_canon.get("mathematical_precision", {})
        if isinstance(design_canon.get("mathematical_precision", {}), dict)
        else {}
    )
    phi = float(math_precision.get("golden_ratio", 1.618) or 1.618)
    fibonacci = math_precision.get("fibonacci_spacing", [8, 13, 21, 34, 55, 89])
    baseline_step = int(fibonacci[2] if isinstance(fibonacci, list) and len(fibonacci) > 2 else 21)
    width = int(target.get("width", 1080) or 1080)
    height = int(target.get("height", 1350) or 1350)
    safe_margin_px = max(int(math_precision.get("safe_zone_margin_px", 64) or 64), int(min(width, height) * 0.06))
    family = _target_family_spec(target)
    still_family = str(target.get("still_family", "")).strip()
    runtime_native_still_grammars = {
        "centered_resolve": "centered",
        "asymmetric_corner": "asymmetric",
        "architectural_grid": "editorial_grid",
    }

    base_layout = {
        "family": family,
        "golden_ratio": phi,
        "baseline_step_px": baseline_step,
        "safe_margin_px": safe_margin_px,
        "hero_zone": {"x": 0.11, "y": 0.68, "w": 0.32, "h": 0.16},
        "support_zone": {"x": 0.11, "y": 0.14, "w": 0.26, "h": 0.05},
        "empty_zone": {"x": 0.50, "y": 0.08, "w": 0.36, "h": 0.48},
        "focal_zone": {"x": 0.08, "y": 0.08, "w": 0.84, "h": 0.80},
        "curve_box": {"x": 0.08, "y": 0.08, "w": 0.84, "h": 0.80},
        "eyebrow_box": {"x": 0.11, "y": 0.14, "w": 0.26, "h": 0.05},
        "title_box": {"x": 0.11, "y": 0.68, "w": 0.32, "h": 0.16},
        "accent_anchor": {"x": 0.90, "y": 0.14},
        "asset_crop": {"object_position": "58% 46%", "veil_opacity": 0.34, "grayscale": 1.0, "contrast": 1.18},
    }

    if still_family == "poster_minimal":
        return {
            **base_layout,
            "family": "poster_minimal",
            "grammar": "monumental",
            "hero_zone": {"x": 0.10, "y": 0.62, "w": 0.28, "h": 0.18},
            "support_zone": {"x": 0.10, "y": 0.14, "w": 0.22, "h": 0.05},
            "empty_zone": {"x": 0.48, "y": 0.08, "w": 0.42, "h": 0.52},
            "focal_zone": {"x": 0.08, "y": 0.08, "w": 0.84, "h": 0.80},
            "curve_box": {"x": 0.08, "y": 0.08, "w": 0.84, "h": 0.80},
            "eyebrow_box": {"x": 0.10, "y": 0.14, "w": 0.22, "h": 0.05},
            "title_box": {"x": 0.10, "y": 0.62, "w": 0.28, "h": 0.18},
            "accent_anchor": {"x": 0.90, "y": 0.14},
            "asset_crop": {"object_position": "58% 46%", "veil_opacity": 0.52, "grayscale": 1.0, "contrast": 1.12},
        }
    if still_family == "editorial_portrait":
        return {
            **base_layout,
            "family": "editorial_portrait",
            "grammar": "editorial_grid",
            "hero_zone": {"x": 0.08, "y": 0.50, "w": 0.42, "h": 0.24},
            "support_zone": {"x": 0.08, "y": 0.12, "w": 0.30, "h": 0.12},
            "empty_zone": {"x": 0.56, "y": 0.10, "w": 0.28, "h": 0.46},
            "focal_zone": {"x": 0.06, "y": 0.08, "w": 0.88, "h": 0.82},
            "curve_box": {"x": 0.06, "y": 0.08, "w": 0.88, "h": 0.78},
            "eyebrow_box": {"x": 0.08, "y": 0.12, "w": 0.30, "h": 0.06},
            "title_box": {"x": 0.08, "y": 0.52, "w": 0.40, "h": 0.22},
            "accent_anchor": {"x": 0.90, "y": 0.16},
            "asset_crop": {"object_position": "56% 42%", "veil_opacity": 0.36, "grayscale": 1.0, "contrast": 1.16},
        }
    if still_family in runtime_native_still_grammars:
        # Preserve runtime-native family geometry instead of flattening it back
        # into the generic hero-poster scaffold at compiler handoff time.
        return {
            "family": still_family,
            "grammar": runtime_native_still_grammars[still_family],
            "golden_ratio": phi,
            "baseline_step_px": baseline_step,
            "safe_margin_px": safe_margin_px,
        }

    if family == "thumbnail":
        return {
            **base_layout,
            "hero_zone": {"x": 0.08, "y": 0.64, "w": 0.30, "h": 0.18},
            "support_zone": {"x": 0.08, "y": 0.14, "w": 0.22, "h": 0.05},
            "empty_zone": {"x": 0.54, "y": 0.08, "w": 0.34, "h": 0.42},
            "focal_zone": {"x": 0.08, "y": 0.10, "w": 0.86, "h": 0.74},
            "curve_box": {"x": 0.08, "y": 0.10, "w": 0.86, "h": 0.74},
            "eyebrow_box": {"x": 0.08, "y": 0.14, "w": 0.22, "h": 0.05},
            "title_box": {"x": 0.08, "y": 0.64, "w": 0.30, "h": 0.18},
            "accent_anchor": {"x": 0.92, "y": 0.16},
            "asset_crop": {"object_position": "64% 44%", "veil_opacity": 0.28, "grayscale": 1.0, "contrast": 1.2},
        }
    if family == "carousel":
        return {
            **base_layout,
            "hero_zone": {"x": 0.10, "y": 0.62, "w": 0.42, "h": 0.20},
            "support_zone": {"x": 0.10, "y": 0.12, "w": 0.28, "h": 0.06},
            "empty_zone": {"x": 0.54, "y": 0.12, "w": 0.28, "h": 0.40},
            "focal_zone": {"x": 0.08, "y": 0.10, "w": 0.84, "h": 0.72},
            "curve_box": {"x": 0.08, "y": 0.10, "w": 0.84, "h": 0.72},
            "eyebrow_box": {"x": 0.10, "y": 0.12, "w": 0.28, "h": 0.06},
            "title_box": {"x": 0.10, "y": 0.62, "w": 0.42, "h": 0.20},
            "accent_anchor": {"x": 0.88, "y": 0.16},
            "asset_crop": {"object_position": "55% 42%", "veil_opacity": 0.24, "grayscale": 1.0, "contrast": 1.14},
        }
    if family == "loop_gif":
        return {
            **base_layout,
            "hero_zone": {"x": 0.09, "y": 0.70, "w": 0.28, "h": 0.14},
            "support_zone": {"x": 0.09, "y": 0.12, "w": 0.22, "h": 0.05},
            "empty_zone": {"x": 0.56, "y": 0.10, "w": 0.24, "h": 0.40},
            "focal_zone": {"x": 0.06, "y": 0.08, "w": 0.88, "h": 0.78},
            "curve_box": {"x": 0.06, "y": 0.08, "w": 0.88, "h": 0.78},
            "eyebrow_box": {"x": 0.09, "y": 0.12, "w": 0.22, "h": 0.05},
            "title_box": {"x": 0.09, "y": 0.70, "w": 0.28, "h": 0.14},
            "accent_anchor": {"x": 0.90, "y": 0.16},
            "asset_crop": {"object_position": "60% 45%", "veil_opacity": 0.22, "grayscale": 1.0, "contrast": 1.12},
        }
    return base_layout


def _build_master_asset_strategy(target: dict[str, Any]) -> dict[str, Any]:
    family = _target_family_spec(target)
    if family in {"hero_poster", "thumbnail", "carousel", "loop_gif"}:
        return {
            "role": "hero_anchor",
            "source": "manim_hero_bg.png",
            "inherit_visual_dna": True,
            "crop_mode": "cover",
        }
    return {
        "role": "supporting_anchor",
        "source": "manim_hero_bg.png",
        "inherit_visual_dna": family in {"short_cinematic", "essay_video", "motion_preview"},
        "crop_mode": "cover",
    }


def _build_still_base_strategy(target: dict[str, Any]) -> dict[str, Any]:
    from core.quality.contract_loader import load_quality_contract

    still_family_id = str(target.get("still_family", "")).strip()
    if not still_family_id:
        return {
            "base": None,
            "background": "solid_dark",
            "requires_manim": False,
            "allow_manim_bypass": True,
            "use_asset_if_available": True,
        }

    contract = load_quality_contract()
    still_family = contract.get_still_family(still_family_id)
    base = still_family.get("base")
    background = str(still_family.get("background", "solid_dark") or "solid_dark")
    requires_manim = str(base).strip().lower() == "manim_geometry"
    use_asset_if_available = background in {"photo_with_veil", "dark_with_geometry_base"} or base not in {None, "null", ""}
    return {
        "base": base,
        "background": background,
        "requires_manim": requires_manim,
        "allow_manim_bypass": not requires_manim,
        "use_asset_if_available": use_asset_if_available,
    }


def _target_family_spec(target: dict[str, Any]) -> str:
    target_id = str(target.get("id", "")).strip()
    if target_id == "linkedin_feed_4_5":
        return "hero_poster"
    if target_id == "short_cinematic_vertical":
        return "short_cinematic"
    if target_id == "linkedin_carousel_square":
        return "carousel"
    if target_id in {"loop_gif_square", "loop_gif_vertical"}:
        return "loop_gif"
    if target_id == "motion_preview_webm":
        return "motion_preview"
    if target_id == "youtube_essay_16_9":
        return "essay_video"
    if target_id == "youtube_thumbnail_16_9":
        return "thumbnail"
    if target_id in {"loop_gif_square", "loop_gif_vertical"}:
        return "loop_gif"
    if target_id == "motion_preview_webm":
        return "motion_preview"
    return "short_cinematic"


def _build_act_quality_profile(plan: dict, acts: list[dict]) -> dict[str, dict[str, Any]]:
    pacing_profile = plan.get("pacing_profile", {}) if isinstance(plan.get("pacing_profile", {}), dict) else {}
    pacing_acts = {
        str(act.get("act_id", "")).strip(): act
        for act in pacing_profile.get("acts", [])
        if isinstance(act, dict) and str(act.get("act_id", "")).strip()
    }
    profile: dict[str, dict[str, Any]] = {}
    for act in acts:
        act_id = str(act.get("id", "")).strip()
        pacing_act = pacing_acts.get(act_id, {})
        profile[act_id] = {
            "emotion": act.get("emotion"),
            "tension": act.get("tension"),
            "breath_points": list(pacing_act.get("breath_points", [])) if isinstance(pacing_act.get("breath_points", []), list) else [],
            "silence_ratio": float(pacing_act.get("silence_ratio", pacing_profile.get("silence_ratio", 0.3)) or 0.3),
            "poster_test": True,
        }
    return profile


def _target_post_fx_profile(target: dict[str, Any]) -> str:
    target_id = str(target.get("id", "")).strip()
    render_mode = str(target.get("render_mode", "video")).strip().lower()
    if target_id in {"linkedin_feed_4_5", "youtube_thumbnail_16_9"}:
        return "premium"
    if render_mode == "carousel":
        return "premium"
    if target_id == "short_cinematic_vertical":
        return "premium"
    if target_id == "youtube_essay_16_9":
        return "cinematic"
    return "cinematic"


def _build_qa_sampling_frames(target: dict[str, Any], acts: list[dict], duration: float) -> list[float]:
    render_mode = str(target.get("render_mode", "video")).strip().lower()
    if render_mode == "still":
        return [float(target.get("still_frame", 0) or 0)]
    if render_mode == "carousel":
        slides = target.get("slides", []) if isinstance(target.get("slides", []), list) else []
        return [float(index) for index in range(min(len(slides), 6))]

    samples: list[float] = []
    for act in acts:
        start = float(act.get("start_sec", 0.0) or 0.0)
        end = float(act.get("end_sec", duration) or duration)
        midpoint = round((start + end) / 2.0, 2)
        samples.append(midpoint)
    if not samples:
        samples = [round(duration * ratio, 2) for ratio in (0.2, 0.5, 0.8)]
    return samples


def _build_poster_test_frames(target: dict[str, Any], acts: list[dict], duration: float) -> list[float]:
    render_mode = str(target.get("render_mode", "video")).strip().lower()
    if render_mode == "still":
        return [float(target.get("still_frame", 0) or 0)]
    if render_mode == "carousel":
        slides = target.get("slides", []) if isinstance(target.get("slides", []), list) else []
        if len(slides) >= 5:
            return [0.0, 4.0, float(len(slides) - 1)]
        return [float(index) for index in range(len(slides))]
    if acts:
        return [round((float(act.get("start_sec", 0.0) or 0.0) + float(act.get("end_sec", duration) or duration)) / 2.0, 2) for act in acts]
    return [round(duration * ratio, 2) for ratio in (0.25, 0.55, 0.85)]


def _target_duration(target: dict[str, Any], base_duration: float) -> float:
    target_id = str(target.get("id", ""))
    if target_id == "youtube_essay_16_9":
        return max(60.0, base_duration * 6)
    if target.get("render_mode") == "still":
        return 0.0
    return base_duration


def _target_summary(target: dict[str, Any], story_atoms: dict[str, Any]) -> str:
    target_id = str(target.get("id", ""))
    if target_id == "linkedin_feed_4_5":
        return f"Poster-first still built around the thesis: {story_atoms.get('thesis')}"
    if target_id == "linkedin_carousel_square":
        return f"Narrative carousel translating '{story_atoms.get('visual_metaphor')}' into cover, proof and CTA."
    if target_id == "youtube_essay_16_9":
        return f"Wide visual essay expanding the thesis for {story_atoms.get('audience')}."
    if target_id == "youtube_thumbnail_16_9":
        return f"Thumbnail resolve built around the word '{story_atoms.get('resolve_word')}'."
    return f"Short cinematic built around '{story_atoms.get('visual_metaphor')}'."


def _build_target_beats(
    target: dict[str, Any],
    story_atoms: dict[str, Any],
    acts: list[dict],
    text_beats: list[dict],
) -> list[dict[str, Any]]:
    target_id = str(target.get("id", ""))
    if target_id == "linkedin_carousel_square":
        return []
    if target_id == "youtube_thumbnail_16_9":
        return [
            {"label": _word_cap(story_atoms.get("thesis")), "text": _word_cap(story_atoms.get("thesis")), "role": "statement"},
            {"label": story_atoms.get("resolve_word"), "text": story_atoms.get("resolve_word"), "role": "resolve"},
        ]

    if target_id == "linkedin_feed_4_5":
        return [
            {"label": "thesis", "text": _word_cap(story_atoms.get("thesis")), "role": "statement"},
            {"label": "resolve", "text": story_atoms.get("resolve_word"), "role": "resolve"},
        ]

    beats: list[dict[str, Any]] = []
    for act in acts:
        beats.append(
            {
                "label": act.get("id"),
                "act": act.get("id"),
                "start_sec": act.get("start_sec"),
                "end_sec": act.get("end_sec"),
                "text": _first_text_for_act(text_beats, act.get("id")) or story_atoms.get("thesis"),
            }
        )
    return beats


def _build_target_slides(
    target: dict[str, Any],
    story_atoms: dict[str, Any],
    text_beats: list[dict],
) -> list[dict[str, Any]]:
    if str(target.get("id", "")) != "linkedin_carousel_square":
        return []

    return [
        {"archetype": "cover", "title": story_atoms.get("title"), "text_blocks": [story_atoms.get("thesis")]},
        {"archetype": "thesis", "title": "Thesis", "text_blocks": [story_atoms.get("thesis")]},
        {"archetype": "proof", "title": "Proof", "text_blocks": [_first_text_for_act(text_beats, "turbulence") or story_atoms.get("visual_metaphor")]},
        {"archetype": "breakdown", "title": "Breakdown", "text_blocks": [story_atoms.get("visual_metaphor")]},
        {"archetype": "turn", "title": "Turn", "text_blocks": [story_atoms.get("emotional_target")]},
        {"archetype": "cta", "title": story_atoms.get("resolve_word"), "text_blocks": [story_atoms.get("tagline")]},
    ]


def _build_target_chapters(
    target: dict[str, Any],
    story_atoms: dict[str, Any],
    acts: list[dict],
    text_beats: list[dict],
) -> list[dict[str, Any]]:
    if str(target.get("id", "")) != "youtube_essay_16_9":
        return []

    return [
        {"archetype": "cold_open", "label": story_atoms.get("title"), "seconds": 8},
        {"archetype": "thesis", "label": story_atoms.get("thesis"), "seconds": 10},
        {"archetype": "escalation", "label": _first_text_for_act(text_beats, "turbulence") or "Escalation", "seconds": 12},
        {"archetype": "architecture_reveal", "label": story_atoms.get("visual_metaphor"), "seconds": 14},
        {"archetype": "proof", "label": story_atoms.get("emotional_target"), "seconds": 10},
        {"archetype": "resolve", "label": story_atoms.get("resolve_word"), "seconds": 8},
    ]


def _target_still_frame(target: dict[str, Any], duration: float) -> int:
    fps = int(target.get("fps", 30) or 30)
    if str(target.get("id", "")) == "youtube_thumbnail_16_9":
        return int(round(duration * fps * 0.82))
    return int(round(duration * fps * 0.72))


def _first_text_for_act(text_beats: list[dict], act_id: str) -> str:
    for beat in text_beats:
        if str(beat.get("act", "")).strip().lower() == str(act_id).strip().lower():
            return str(beat.get("text", "")).strip()
    return ""


def _build_render_inputs(
    artifact_plan: dict,
    acts: list[dict],
    text_beats: list[dict],
    duration: float,
    fps: int,
    layout_contract: dict,
    plan: dict,
    brief: dict,
) -> dict[str, dict]:
    render_inputs: dict[str, dict] = {}
    for target in artifact_plan.get("targets", []):
        if not isinstance(target, dict):
            continue
        format_layout = target.get("layout", {})
        render_inputs[target["id"]] = {
            "target_id": target["id"],
            "format_id": target.get("format_id", "vertical_9_16"),
            "channel": target.get("channel", ""),
            "purpose": target.get("purpose", ""),
            "priority": target.get("priority", 0),
            "label": target.get("label", target["id"]),
            "render_mode": target.get("render_mode", "video"),
            "composition": target.get("composition", ""),
            "width": target.get("width", 0),
            "height": target.get("height", 0),
            "fps": target.get("fps", fps),
            "safe_zone": target.get("safe_zone", 0.0),
            "layout": format_layout,
            "duration": target.get("duration_sec", duration),
            "duration_in_frames": int(
                round(float(target.get("duration_sec", duration) or duration) * int(target.get("fps", fps) or fps))
            ),
            "acts": acts,
            "text_cues": text_beats,
            "beats": target.get("beats", []),
            "slides": target.get("slides", []),
            "chapters": target.get("chapters", []),
            "story_atoms": artifact_plan.get("story_atoms", {}),
            "style_pack": target.get("style_pack", artifact_plan.get("style_pack")),
            "style_pack_ids": artifact_plan.get("style_pack_ids", []),
            "motion_grammar": target.get("motion_grammar", artifact_plan.get("motion_grammar")),
            "typography_system": target.get("typography_system", artifact_plan.get("typography_system")),
            "still_family": target.get("still_family", artifact_plan.get("still_family")),
            "color_mode": target.get("color_mode", artifact_plan.get("color_mode")),
            "negative_space_target": target.get("negative_space_target", artifact_plan.get("negative_space_target")),
            "accent_intensity": target.get("accent_intensity", artifact_plan.get("accent_intensity")),
            "grain": target.get("grain", artifact_plan.get("grain")),
            "material_hint": target.get("material_hint", artifact_plan.get("material_hint")),
            "quality_constraints": artifact_plan.get("quality_constraints", {}),
            "quality_mode": target.get("quality_mode", artifact_plan.get("quality_mode", "absolute")),
            "premium_targets": artifact_plan.get("premium_targets", []),
            "qa_frames": artifact_plan.get("qa_frames"),
            "auto_iterate_max": artifact_plan.get("auto_iterate_max"),
            "brand_veto_policy": artifact_plan.get("brand_veto_policy", {}),
            "act_quality_profile": target.get("act_quality_profile", {}),
            "post_fx_profile": target.get("post_fx_profile"),
            "qa_sampling_frames": target.get("qa_sampling_frames", []),
            "poster_test_frames": target.get("poster_test_frames", []),
            "brief": {
                "title": brief.get("title"),
                "tagline": brief.get("tagline"),
                "platform": brief.get("platform"),
                "format": brief.get("format"),
                "output_targets": list(brief.get("output_targets", []))
                if isinstance(brief.get("output_targets"), list)
                else [],
            },
            "plan": {
                "archetype": plan.get("archetype"),
                "pacing": plan.get("pacing"),
                "emotion": _infer_emotional_target(plan),
            },
            "reference_native_direction": artifact_plan.get("reference_native_direction", {}),
            "reference_evidence": artifact_plan.get("reference_evidence", []),
        }
    return render_inputs


def _build_act_windows(duration: float, plan: dict, narrative_contract: dict) -> list[dict]:
    structure = narrative_contract.get("structure", {}).get("acts", {})
    ordered_ids = ["genesis", "turbulence", "resolution"]
    timeline = plan.get("timeline", [])
    llm_scenes = plan.get("llm_scene_plan", {}).get("scenes", [])

    acts: list[dict] = []
    cursor = 0.0
    for index, act_id in enumerate(ordered_ids):
        act_contract = structure.get(act_id, {})
        ratio = float(act_contract.get("duration_ratio", 0.33) or 0.33)
        act_duration = duration * ratio if index < len(ordered_ids) - 1 else max(0.0, duration - cursor)
        start = round(cursor, 3)
        end = round(min(duration, cursor + act_duration), 3)
        midpoint = ((start + end) / 2.0) / max(duration, 0.001)
        behavior, tension = _timeline_state_for_progress(timeline, midpoint)
        visual_primitives = _primitives_for_act(act_id, llm_scenes) or list(DEFAULT_PRIMITIVES_BY_ACT[act_id])

        acts.append(
            {
                "id": act_id,
                "start_sec": start,
                "end_sec": end,
                "overlap_buffer_ms": 300 if index > 0 else 0,
                "transition_pattern": "fade_through" if index > 0 else "entrance",
                "emotion": act_contract.get("emotion", DEFAULT_EMOTION_BY_ACT[act_id]),
                "behavior": behavior,
                "tension": tension or DEFAULT_TENSION_BY_ACT[act_id],
                "camera": DEFAULT_CAMERA_BY_ACT[act_id],
                "visual_primitives": visual_primitives,
                "text_cues": [],
            }
        )
        cursor += act_duration

    if acts:
        acts[-1]["end_sec"] = round(duration, 3)
    return acts


def _timeline_state_for_progress(timeline: list[dict], progress: float) -> tuple[str, str]:
    for block in timeline:
        phase = block.get("phase", [0.0, 1.0])
        if len(phase) != 2:
            continue
        start, end = phase
        if float(start) <= progress <= float(end):
            return str(block.get("behavior", "coherent_flow")), str(block.get("tension", "medium"))
    return "coherent_flow", "medium"


def _primitives_for_act(act_id: str, llm_scenes: list[dict]) -> list[str]:
    primitives: list[str] = []
    if isinstance(llm_scenes, list):
        for scene in llm_scenes:
            if not isinstance(scene, dict):
                continue
            scene_act = str(scene.get("act", "")).strip().lower()
            if scene_act and scene_act != act_id:
                continue
            for primitive in scene.get("primitives", []):
                text = str(primitive).strip()
                if text and text not in primitives:
                    primitives.append(text)
    return primitives


def _collect_text_beats(brief: dict, acts: list[dict], duration: float, plan: dict) -> list[dict]:
    text_beats = brief.get("text_beats")
    if isinstance(text_beats, list) and text_beats:
        cues = [_normalize_text_beat(item, acts, duration) for item in text_beats]
        return [cue for cue in cues if cue is not None]

    return _default_text_beats(brief, acts, plan)


def _normalize_text_beat(item: dict, acts: list[dict], duration: float) -> dict | None:
    if not isinstance(item, dict):
        return None

    act_id = str(item.get("act", "")).strip().lower()
    if act_id not in {act["id"] for act in acts}:
        act_id = "turbulence"

    act_window = next(act for act in acts if act["id"] == act_id)
    at_ratio = item.get("at_ratio")
    if at_ratio is not None:
        at_sec = act_window["start_sec"] + (act_window["end_sec"] - act_window["start_sec"]) * float(at_ratio)
    else:
        at_sec = float(item.get("at_sec", act_window["start_sec"]))

    if act_id == "genesis":
        at_sec = max(at_sec, 2.0)

    text = _word_cap(str(item.get("text", "")).strip())
    if not text:
        return None

    return {
        "act": act_id,
        "at_sec": round(min(duration, max(0.0, at_sec)), 3),
        "text": text,
        "position": _normalize_position(item.get("position", "bottom_zone")),
        "role": str(item.get("role", "narration")).strip() or "narration",
        "weight": int(item.get("weight", 400)),
        "color_state": str(item.get("color_state", "default")).strip() or "default",
    }


def _default_text_beats(brief: dict, acts: list[dict], plan: dict) -> list[dict]:
    turbulence = next(act for act in acts if act["id"] == "turbulence")
    resolution = next(act for act in acts if act["id"] == "resolution")
    agitation = _word_cap(
        brief.get("agitation_text")
        or brief.get("hook_text")
        or _default_agitation_copy(plan),
    )
    resolve_word = _word_cap(
        brief.get("resolve_word") or DEFAULT_RESOLVE_BY_ARCHETYPE.get(plan.get("archetype"), "AIOX"),
        limit=2,
    )
    title = _word_cap(brief.get("title") or "Invisible Architecture")

    return [
        {
            "act": "turbulence",
            "at_sec": round(turbulence["start_sec"] + 0.9, 3),
            "text": agitation,
            "position": "top_zone",
            "role": "hook",
            "weight": 320,
            "color_state": "default",
        },
        {
            "act": "turbulence",
            "at_sec": round(max(turbulence["start_sec"] + 2.4, turbulence["end_sec"] - 1.6), 3),
            "text": title,
            "position": "bottom_zone",
            "role": "narration",
            "weight": 420,
            "color_state": "default",
        },
        {
            "act": "resolution",
            "at_sec": round(max(resolution["start_sec"] + 1.4, resolution["end_sec"] - 2.0), 3),
            "text": resolve_word,
            "position": "center_climax",
            "role": "resolve",
            "weight": 560,
            "color_state": "default",
        },
    ]


def _default_agitation_copy(plan: dict) -> str:
    archetype = str(plan.get("archetype", "emergence"))
    if archetype == "chaos_to_order":
        return "order fights the noise"
    if archetype == "order_to_chaos":
        return "systems bend before rupture"
    if archetype == "fragmented_reveal":
        return "signal breaks the surface"
    if archetype == "gravitational_collapse":
        return "everything falls inward"
    return "silence before the surge"


def _normalize_position(position: str) -> str:
    allowed = {"top_zone", "bottom_zone", "center_climax", "center"}
    value = str(position or "bottom_zone").strip().lower()
    return value if value in allowed else "bottom_zone"


def _word_cap(text: str, limit: int = TEXT_WORD_LIMIT) -> str:
    words = [word for word in str(text or "").strip().split() if word]
    return " ".join(words[:limit]).strip()


def _infer_emotional_target(plan: dict) -> str:
    archetype = str(plan.get("archetype", "emergence"))
    if archetype == "chaos_to_order":
        return "transform tension into mastery"
    if archetype == "order_to_chaos":
        return "reveal fracture before impact"
    if archetype == "fragmented_reveal":
        return "make pressure feel elegant"
    return "make hidden order feel inevitable"


def _infer_visual_metaphor(plan: dict) -> str:
    archetype = str(plan.get("archetype", "emergence"))
    if archetype == "chaos_to_order":
        return "noise collapsing into architecture"
    if archetype == "order_to_chaos":
        return "precision cracking under pressure"
    if archetype == "fragmented_reveal":
        return "signal piercing a dark field"
    return "a living curve teaching matter to align"
