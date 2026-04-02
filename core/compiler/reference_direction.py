from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
REFERENCE_DIR = ROOT / "contracts" / "references"


def load_reference_contract(reference_id_or_path: str) -> dict[str, Any]:
    raw = str(reference_id_or_path or "").strip()
    if not raw:
        return {}

    path = Path(raw)
    candidates: list[Path] = []
    if path.is_absolute() or path.exists():
        candidates.append(path)
    else:
        candidates.extend(
            [
                ROOT / raw,
                REFERENCE_DIR / raw,
                REFERENCE_DIR / f"{raw}.yaml",
                REFERENCE_DIR / f"{raw}.json",
            ]
        )

    for candidate in candidates:
        if not candidate.exists():
            continue
        if candidate.suffix.lower() == ".json":
            return json.loads(candidate.read_text(encoding="utf-8"))
        return yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
    return {}


def resolve_reference_native_direction(
    seed: dict[str, Any] | None,
    *,
    brief: dict[str, Any] | None = None,
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or {}
    brief = brief or {}
    plan = plan or {}

    explicit_direction = _collect_direct_reference_direction(seed, brief, plan)
    reference_ids = _collect_reference_ids(seed, brief, plan)
    reference_contracts = [
        {
            "id": ref_id,
            "contract": load_reference_contract(ref_id),
        }
        for ref_id in reference_ids
    ]
    reference_contracts = [entry for entry in reference_contracts if isinstance(entry.get("contract"), dict) and entry["contract"]]

    translation = _translation_from_reference_contracts(reference_contracts)
    if explicit_direction:
        translation = _merge_dicts(translation, explicit_direction)

    if not translation and not reference_contracts:
        return {}

    primary_translation = translation
    target_overrides = _build_target_overrides(primary_translation)
    evidence = [
        {
            "id": entry["id"],
            "source_type": str((entry["contract"].get("source") or {}).get("type") or entry["contract"].get("reference", {}).get("type") or "reference_contract"),
            "style_pack_hint": ((entry["contract"].get("aiox_translation") or {}) or {}).get("style_pack_hint"),
            "motion_grammar_hint": ((entry["contract"].get("aiox_translation") or {}) or {}).get("motion_grammar_hint"),
        }
        for entry in reference_contracts
    ]
    return {
        "reference_ids": reference_ids,
        "reference_contracts": [entry["id"] for entry in reference_contracts],
        "resolved": primary_translation,
        "target_overrides": target_overrides,
        "reference_evidence": evidence,
        "emulate": list(primary_translation.get("emulate", []) or []),
        "avoid_literal_copy": list(primary_translation.get("avoid_literal_copy", []) or []),
    }


def apply_reference_direction_to_plan(
    plan: dict[str, Any],
    reference_direction: dict[str, Any] | None,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(reference_direction, dict) or not reference_direction:
        return plan

    updated = copy.deepcopy(plan)
    updated["reference_native_direction"] = copy.deepcopy(reference_direction)

    explicit_values = _collect_explicit_scalar_overrides(seed or {}, updated)
    for key, value in explicit_values.items():
        if value in {None, ""}:
            continue
        if key == "style_pack":
            updated["style_pack"] = str(value).strip()
            updated["style_pack_ids"] = _merge_unique([str(value).strip()], updated.get("style_pack_ids", []))
            continue
        updated[key] = value

    explicit = _collect_explicit_overrides(seed or {}, updated)
    resolved = reference_direction.get("resolved", {}) if isinstance(reference_direction.get("resolved", {}), dict) else {}

    if not explicit.get("style_pack"):
        style_pack = str(resolved.get("style_pack", "")).strip()
        if style_pack:
            updated["style_pack_ids"] = _merge_unique([style_pack], updated.get("style_pack_ids", []))

    if not explicit.get("motion_grammar"):
        motion_grammar = str(resolved.get("motion_grammar", "")).strip()
        if motion_grammar:
            updated["motion_grammar"] = motion_grammar

    if not explicit.get("typography_system"):
        typography_system = str(resolved.get("typography_system", "")).strip()
        if typography_system:
            updated["typography_system"] = typography_system

    if not explicit.get("still_family"):
        still_family = str(resolved.get("still_family", "")).strip()
        if still_family:
            updated["still_family"] = still_family

    return updated


def attach_reference_to_brief(
    brief: dict[str, Any] | None,
    *,
    reference_id: str | None = None,
    translation: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    updated = copy.deepcopy(brief or {})
    references = updated.get("references", {}) if isinstance(updated.get("references", {}), dict) else {}

    raw_reference_id = str(reference_id or "").strip()
    if raw_reference_id:
        references["active_reference"] = raw_reference_id
        existing_ids = references.get("reference_contracts") or references.get("reference_ids") or []
        merged_ids = _merge_unique([raw_reference_id], existing_ids)
        references["reference_contracts"] = merged_ids

    if isinstance(translation, dict) and translation:
        references["aiox_translation"] = copy.deepcopy(translation)

    if isinstance(metadata, dict) and metadata:
        references["reference_native_metadata"] = copy.deepcopy(metadata)

    if references:
        updated["references"] = references
    return updated


def ingest_reference_zip_to_contract(
    zip_path: str | Path,
    *,
    screenshots: list[str] | None = None,
    notes: str | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    from core.tools.reference_translation import (
        analyze_site_zip,
        build_reference_contract,
        synthesize_design_dna,
        translate_site_dna_to_aiox,
        write_reference_contract,
    )

    analysis = analyze_site_zip(zip_path, screenshots=screenshots, notes=notes)
    dna = synthesize_design_dna(analysis)
    translation = translate_site_dna_to_aiox(analysis, dna)
    contract = build_reference_contract(analysis, dna, translation)
    paths = write_reference_contract(contract, output_dir=output_dir)
    return {
        "reference_contract_id": paths.slug,
        "reference_contract_path": str(paths.yaml_path),
        "reference_contract_json_path": str(paths.json_path),
        "analysis": analysis,
        "design_dna": dna,
        "aiox_translation": translation,
        "contract": contract,
    }


def reference_value_for_target(plan: dict[str, Any], target_id: str, key: str) -> Any:
    reference_direction = (
        plan.get("reference_native_direction", {})
        if isinstance(plan.get("reference_native_direction", {}), dict)
        else {}
    )
    target_overrides = reference_direction.get("target_overrides", {}) if isinstance(reference_direction.get("target_overrides", {}), dict) else {}
    target_block = target_overrides.get(str(target_id).strip(), {}) if isinstance(target_overrides.get(str(target_id).strip(), {}), dict) else {}
    if key in target_block and target_block.get(key) not in {None, ""}:
        return target_block.get(key)
    resolved = reference_direction.get("resolved", {}) if isinstance(reference_direction.get("resolved", {}), dict) else {}
    return resolved.get(key)


def _collect_reference_ids(*sources: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for source in sources:
        if not isinstance(source, dict):
            continue
        for key in ("reference_contract_id", "reference_contract", "active_reference", "reference_id"):
            value = str(source.get(key, "")).strip()
            if value:
                values.append(value)
        references = source.get("references", {})
        if isinstance(references, dict):
            for key in ("active_reference", "reference_contract_id", "reference_contract"):
                value = str(references.get(key, "")).strip()
                if value:
                    values.append(value)
            contract_values = references.get("reference_contracts") or references.get("reference_ids")
            if isinstance(contract_values, list):
                values.extend(str(item).strip() for item in contract_values if str(item).strip())
    return _merge_unique(values, [])


def _collect_direct_reference_direction(*sources: dict[str, Any]) -> dict[str, Any]:
    direction: dict[str, Any] = {}
    for source in sources:
        if not isinstance(source, dict):
            continue
        for key in ("reference_native_direction", "translated_reference", "aiox_translation"):
            payload = source.get(key)
            if isinstance(payload, dict):
                direction = _merge_dicts(direction, _normalize_translation_payload(payload))
        references = source.get("references", {})
        if isinstance(references, dict):
            for key in ("reference_native_direction", "translated_reference", "aiox_translation"):
                payload = references.get(key)
                if isinstance(payload, dict):
                    direction = _merge_dicts(direction, _normalize_translation_payload(payload))
    return direction


def _translation_from_reference_contracts(reference_contracts: list[dict[str, Any]]) -> dict[str, Any]:
    translation: dict[str, Any] = {}
    for entry in reference_contracts:
        contract = entry.get("contract", {})
        if not isinstance(contract, dict):
            continue
        payload = contract.get("aiox_translation")
        if isinstance(payload, dict):
            translation = _merge_dicts(translation, _normalize_translation_payload(payload))
            continue
        translation = _merge_dicts(translation, _legacy_contract_translation(contract))
    return translation


def _legacy_contract_translation(contract: dict[str, Any]) -> dict[str, Any]:
    style_classification = str(contract.get("style_classification", "")).strip()
    mood = str(contract.get("mood", "")).lower()
    typography = contract.get("typography", {}) if isinstance(contract.get("typography", {}), dict) else {}
    spacing = contract.get("spacing", {}) if isinstance(contract.get("spacing", {}), dict) else {}
    palette = contract.get("palette", {}) if isinstance(contract.get("palette", {}), dict) else {}
    style_pack = "silent_luxury"
    typography_system = "editorial_minimal"
    still_family = "poster_minimal"
    motion_grammar = "cinematic_restrained"
    negative_space_target = 0.58
    accent_intensity = 0.18
    grain = 0.04

    if style_classification in {"product_precision", "technical_minimal"} or "technical" in mood or "precise" in mood:
        style_pack = "kinetic_editorial"
        typography_system = "editorial_dense"
        still_family = "editorial_portrait"
        motion_grammar = "kinetic_editorial"
        negative_space_target = 0.42
        accent_intensity = 0.42
        grain = 0.08
    elif style_classification == "editorial_minimal":
        style_pack = "silent_luxury"
        typography_system = "editorial_minimal"
        still_family = "poster_minimal"
        motion_grammar = "cinematic_restrained"
        negative_space_target = 0.62
        accent_intensity = 0.14

    content_width = str(spacing.get("content_max_width", "")).lower()
    if content_width.endswith("px"):
        try:
            width_px = float(content_width[:-2])
            if width_px <= 980:
                typography_system = "editorial_dense"
                still_family = "editorial_portrait"
        except ValueError:
            pass

    if any(token in str(palette).lower() for token in ("#000", "#0f0f0f", "#0b0d12")):
        grain = max(grain, 0.06)

    heading_family = ""
    if isinstance(typography.get("heading"), dict):
        heading_family = str(typography.get("heading", {}).get("family", "")).strip()
    elif isinstance(typography, dict):
        heading_family = str(typography.get("primary_family", "")).strip()

    emulate = [
        "Translate reference hierarchy and spacing rhythm into AIOX-native compositions.",
        "Borrow editorial temperament, not literal modules or components.",
    ]
    if heading_family:
        emulate.append(f"Use {heading_family} as typography tone guidance when compatible with AIOX contracts.")

    return {
        "style_pack": style_pack,
        "typography_system": typography_system,
        "still_family": still_family,
        "motion_grammar": motion_grammar,
        "negative_space_target": negative_space_target,
        "accent_intensity": accent_intensity,
        "grain": grain,
        "material_hint": "soft_ui" if grain >= 0.06 else "editorial_flat",
        "emulate": emulate,
        "avoid_literal_copy": [
            "Do not copy literal layouts or proprietary UI modules.",
            "Do not treat legacy reference gradients or logos as AIOX assets.",
        ],
    }


def _normalize_translation_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "style_pack": str(payload.get("style_pack") or payload.get("style_pack_hint") or "").strip(),
        "typography_system": str(payload.get("typography_system") or payload.get("typography_system_hint") or "").strip(),
        "still_family": str(payload.get("still_family") or payload.get("still_family_hint") or "").strip(),
        "motion_grammar": str(payload.get("motion_grammar") or payload.get("motion_grammar_hint") or "").strip(),
        "negative_space_target": payload.get("negative_space_target") if payload.get("negative_space_target") is not None else payload.get("negative_space_target_hint"),
        "accent_intensity": payload.get("accent_intensity") if payload.get("accent_intensity") is not None else payload.get("accent_intensity_hint"),
        "grain": payload.get("grain") if payload.get("grain") is not None else payload.get("grain_hint"),
        "material_hint": str(payload.get("material_hint", "")).strip(),
        "emulate": list(payload.get("emulate", []) or []),
        "avoid_literal_copy": list(payload.get("avoid_literal_copy", []) or []),
    }


def _build_target_overrides(translation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not translation:
        return {}

    style_pack = str(translation.get("style_pack", "")).strip()
    typography_system = str(translation.get("typography_system", "")).strip()
    still_family = str(translation.get("still_family", "")).strip()
    motion_grammar = str(translation.get("motion_grammar", "")).strip()
    negative_space = translation.get("negative_space_target")
    accent = translation.get("accent_intensity")
    grain = translation.get("grain")

    technical_variant_style = "kinetic_editorial" if style_pack != "kinetic_editorial" else style_pack
    technical_typography = "editorial_dense"

    return {
        "linkedin_feed_4_5": {
            "style_pack": style_pack or "silent_luxury",
            "typography_system": typography_system or "editorial_minimal",
            "still_family": still_family or "poster_minimal",
            "negative_space_target": negative_space if negative_space is not None else 0.58,
            "accent_intensity": min(float(accent or 0.16), 0.28),
            "grain": float(grain or 0.04),
        },
        "short_cinematic_vertical": {
            "style_pack": style_pack or "silent_luxury",
            "motion_grammar": motion_grammar or "cinematic_restrained",
            "negative_space_target": negative_space if negative_space is not None else 0.52,
            "accent_intensity": float(accent or 0.18),
            "grain": float(grain or 0.04),
        },
        "youtube_essay_16_9": {
            "style_pack": technical_variant_style,
            "typography_system": technical_typography,
            "motion_grammar": motion_grammar or "kinetic_editorial",
            "negative_space_target": min(float(negative_space or 0.48), 0.52),
            "accent_intensity": max(float(accent or 0.32), 0.32),
            "grain": max(float(grain or 0.06), 0.06),
        },
    }


def _collect_explicit_overrides(seed: dict[str, Any], plan: dict[str, Any]) -> dict[str, bool]:
    return {
        "style_pack": any(str(source.get(key, "")).strip() for source in (seed, plan) if isinstance(source, dict) for key in ("style_pack", "style_pack_id")),
        "motion_grammar": any(str(source.get("motion_grammar", "")).strip() for source in (seed, plan) if isinstance(source, dict)),
        "typography_system": any(str(source.get("typography_system", "")).strip() for source in (seed, plan) if isinstance(source, dict)),
        "still_family": any(str(source.get("still_family", "")).strip() for source in (seed, plan) if isinstance(source, dict)),
    }


def _collect_explicit_scalar_overrides(seed: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    sources = []
    if isinstance(seed, dict):
        sources.append(seed)
        references = seed.get("references", {})
        if isinstance(references, dict):
            sources.append(references)
    if isinstance(plan, dict):
        sources.append(plan)

    values: dict[str, Any] = {}
    scalar_keys = ("motion_grammar", "typography_system", "still_family", "color_mode", "negative_space_target", "accent_intensity", "grain", "material_hint")
    for source in sources:
        if not isinstance(source, dict):
            continue
        style_pack = str(source.get("style_pack") or source.get("style_pack_id") or "").strip()
        if style_pack and "style_pack" not in values:
            values["style_pack"] = style_pack
        for key in scalar_keys:
            value = source.get(key)
            if value not in {None, ""} and key not in values:
                values[key] = value
    return values


def _merge_unique(primary: list[str], secondary: Any) -> list[str]:
    merged: list[str] = []
    for value in list(primary) + [str(item).strip() for item in (secondary or []) if str(item).strip()]:
        if value and value not in merged:
            merged.append(value)
    return merged


def _merge_dicts(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if value is None or value == "" or value == [] or value == {}:
            continue
        if key in {"emulate", "avoid_literal_copy"}:
            merged[key] = _merge_unique([str(item).strip() for item in merged.get(key, []) if str(item).strip()], value)
            continue
        merged[key] = value
    return merged
