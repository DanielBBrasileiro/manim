"""
post_processor.py — Contract-driven post-processing bridge.

Loads contracts/post_processing.yaml and applies archetype-aware,
mode-aware effects through the generator-grade PostProcessor.
"""
from __future__ import annotations

import shutil
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from core.generators.post_processor import EFFECT_FNS, PostProcessor

ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACT_PATH = ROOT / "contracts" / "post_processing.yaml"


@lru_cache(maxsize=1)
def load_post_processing_contract() -> dict[str, Any]:
    if not CONTRACT_PATH.exists():
        return {}
    try:
        with open(CONTRACT_PATH, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except Exception:
        return {}


def resolve_post_fx_plan(target_report: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    contract = load_post_processing_contract()
    constraints = contract.get("constraints", {}) if isinstance(contract.get("constraints", {}), dict) else {}
    archetypes = contract.get("archetypes", {}) if isinstance(contract.get("archetypes", {}), dict) else {}
    modes = contract.get("modes", {}) if isinstance(contract.get("modes", {}), dict) else {}

    archetype = str(context.get("archetype") or "emergence").strip() or "emergence"
    archetype_config = archetypes.get(archetype) or archetypes.get("emergence") or {}

    render_mode = str(target_report.get("mode") or "video").strip().lower()
    mode_config = modes.get(render_mode, {}) if isinstance(modes.get(render_mode, {}), dict) else {}

    preset = str(
        target_report.get("post_fx_profile")
        or context.get("post_fx_profile")
        or archetype_config.get("preset")
        or "cinematic"
    ).strip() or "cinematic"
    emotion = str(archetype_config.get("emotion_default") or context.get("emotion") or "mastery").strip() or "mastery"

    mandatory = _string_list(archetype_config.get("mandatory"))
    optional = _string_list(archetype_config.get("optional"))
    strict = bool(context.get("strict_effect_enforcement", False))
    requested_effects = mandatory + ([] if strict else optional)

    effects = _build_effects(
        requested_effects=requested_effects,
        constraints=constraints,
        emotion=emotion,
        render_mode=render_mode,
        mode_config=mode_config,
    )

    missing_mandatory = [name for name in mandatory if name not in {effect.get("name") for effect in effects}]

    return {
        "contract_loaded": bool(contract),
        "archetype": archetype,
        "render_mode": render_mode,
        "preset": preset,
        "emotion": emotion,
        "strict": strict,
        "effects": effects,
        "mandatory": mandatory,
        "optional": optional,
        "missing_mandatory": missing_mandatory,
        "constraints": constraints,
        "mode_config": mode_config,
    }


def apply_post_fx_to_target(target_report: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    plan = resolve_post_fx_plan(target_report, context=context)
    output_path = str(target_report.get("output") or "").strip()
    if not output_path or not Path(output_path).exists():
        return {
            **plan,
            "applied": False,
            "reason": "output_missing",
        }

    if plan["strict"] and plan["missing_mandatory"]:
        return {
            **plan,
            "applied": False,
            "reason": "mandatory_effects_missing",
        }

    processor = PostProcessor(effects=plan["effects"] or None, preset=plan["preset"] if not plan["effects"] else None)

    try:
        if plan["render_mode"] == "still":
            processor.process_image(output_path)
            applied = True
        elif plan["render_mode"] == "carousel":
            applied = False
            for slide_path in target_report.get("slides", []) or []:
                slide = str(slide_path).strip()
                if slide and Path(slide).exists():
                    processor.process_image(slide)
                    applied = True
        elif plan["render_mode"] == "video":
            target_id = str(target_report.get("target") or "").strip()
            if target_id == "short_cinematic_vertical":
                source = Path(output_path)
                temp_output = source.with_name(f"{source.stem}.postfx{source.suffix}")
                fps = float(plan["mode_config"].get("fps", 60) or 60.0)
                crf = int(plan["mode_config"].get("crf", 18) or 18)
                applied = bool(processor.process_video(output_path, str(temp_output), fps=fps, crf=crf))
                if applied and temp_output.exists():
                    shutil.move(str(temp_output), output_path)
            else:
                applied = False
        else:
            applied = False
    except Exception as exc:
        return {
            **plan,
            "applied": False,
            "reason": f"{type(exc).__name__}: {exc}",
        }

    return {
        **plan,
        "applied": applied,
        "reason": "ok" if applied else "unsupported_target_or_mode",
    }


def _build_effects(
    *,
    requested_effects: list[str],
    constraints: dict[str, Any],
    emotion: str,
    render_mode: str,
    mode_config: dict[str, Any],
) -> list[dict[str, Any]]:
    effects: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_effect(effect: dict[str, Any]) -> None:
        name = str(effect.get("name") or "").strip()
        if not name or name in seen or name not in EFFECT_FNS:
            return
        seen.add(name)
        effects.append(effect)

    add_effect({"name": "color_grade", "emotion": emotion})
    for name in requested_effects:
        effect = _effect_from_contract(name, constraints, render_mode=render_mode, mode_config=mode_config)
        if effect:
            add_effect(effect)

    return effects


def _effect_from_contract(
    effect_name: str,
    constraints: dict[str, Any],
    *,
    render_mode: str,
    mode_config: dict[str, Any],
) -> dict[str, Any] | None:
    name = str(effect_name or "").strip()
    if name == "chromatic_aberration":
        limit = constraints.get("chromatic_aberration", {})
        return {
            "name": name,
            "strength": _clamp(
                float(limit.get("min_strength", 0.005) or 0.005),
                minimum=float(limit.get("min_strength", 0.002) or 0.002),
                maximum=float(limit.get("max_strength", 0.01) or 0.01),
            ),
        }
    if name == "film_grain":
        limit = constraints.get("film_grain", {})
        return {
            "name": name,
            "intensity": _clamp(
                float(limit.get("min_intensity", 0.04) or 0.04),
                minimum=float(limit.get("min_intensity", 0.02) or 0.02),
                maximum=float(limit.get("max_intensity", 0.12) or 0.12),
            ),
            "temporal": bool(mode_config.get("grain_temporal", render_mode == "video")),
        }
    if name == "halation":
        limit = constraints.get("halation", {})
        threshold_range = limit.get("threshold_range", [0.55, 0.85]) if isinstance(limit.get("threshold_range", [0.55, 0.85]), list) else [0.55, 0.85]
        threshold = float(sum(float(item) for item in threshold_range[:2]) / max(min(len(threshold_range), 2), 1))
        return {
            "name": name,
            "intensity": _clamp(
                float(limit.get("max_intensity", 0.35) or 0.35) * 0.7,
                minimum=0.05,
                maximum=float(limit.get("max_intensity", 0.5) or 0.5),
            ),
            "threshold": threshold,
        }
    if name == "breath_exposure":
        limit = constraints.get("breath_exposure", {})
        if not bool(mode_config.get("breath_enabled", render_mode == "video")):
            return None
        freq_range = limit.get("freq_range", [0.1, 0.5]) if isinstance(limit.get("freq_range", [0.1, 0.5]), list) else [0.1, 0.5]
        frequency = float(sum(float(item) for item in freq_range[:2]) / max(min(len(freq_range), 2), 1))
        return {
            "name": name,
            "amplitude": _clamp(float(limit.get("max_amplitude", 0.04) or 0.04) * 0.5, minimum=0.005, maximum=float(limit.get("max_amplitude", 0.06) or 0.06)),
            "frequency": frequency,
        }
    if name == "vignette":
        return {"name": name, "strength": 0.35, "softness": 0.55}
    if name == "scanlines":
        return {"name": name, "spacing": 3, "darkness": 0.05}
    if name == "glow":
        return {"name": name, "radius": 8, "intensity": 0.18, "threshold": 0.78}
    if name == "color_grade":
        return {"name": name}
    return None


def _clamp(value: float, *, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
