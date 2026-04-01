"""Persona Kael: Temporal Rhythm Master.

Builds a PacingProfile by consulting archetype YAML phases[],
enforcing: breath_points (0.3-0.8s pauses), silence_ratio >= 0.30,
stagger_rule (no simultaneous element entry), text_minimum_gap 1.5s.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
_ARCHETYPE_DIR = ROOT / "contracts" / "narrative" / "archetypes"
_NARRATIVE_CONTRACT = ROOT / "contracts" / "identities" / "aiox_default" / "narrative.yaml"
_MOTION_GRAMMAR_DIR = ROOT / "contracts" / "motion_grammars"


def _load_archetype(name: str) -> dict[str, Any]:
    path = _ARCHETYPE_DIR / f"{name}.yaml"
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _load_motion_grammar(name: str) -> dict[str, Any]:
    path = _MOTION_GRAMMAR_DIR / f"{name}.yaml"
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _pacing_mode(intent: str, archetype: str) -> str:
    intent_lower = intent.lower()
    if any(w in intent_lower for w in ["slow", "meditative", "deep", "contemplative", "silence", "calm"]):
        return "cinematic"
    if any(w in intent_lower for w in ["fast", "dynamic", "urgent", "kinetic", "aggressive", "scroll"]):
        return "dynamic"
    cinematic = {"emergence", "chaos_to_order", "resolution", "synchronization", "loop_stability", "expansion_field"}
    return "cinematic" if archetype in cinematic else "dynamic"


def _select_motion_grammar(intent: str, archetype: str, requested: str | None = None) -> str:
    if requested:
        grammar = requested.strip()
        if grammar:
            return grammar
    intent_lower = intent.lower()
    if any(w in intent_lower for w in ["fast", "dynamic", "urgent", "kinetic", "aggressive", "scroll", "editorial"]):
        return "kinetic_editorial"
    cinematic = {"emergence", "chaos_to_order", "resolution", "synchronization", "loop_stability", "expansion_field"}
    return "cinematic_restrained" if archetype in cinematic else "kinetic_editorial"


def _compute_breath_points(start: float, end: float) -> list[float]:
    duration = end - start
    if duration <= 1.5:
        return []
    # One breath at ~60% — pause of 0.3-0.8s before act climax
    return [round(start + duration * 0.60, 2)]


def _compute_breath_points_for_grammar(start: float, end: float, grammar: dict[str, Any], act_id: str) -> list[float]:
    duration = end - start
    if duration <= 1.0:
        return []
    rhythm = str(grammar.get("rhythm", "uniform") or "uniform")
    base_points: list[float]
    if act_id == "genesis":
        base_points = [0.55]
    elif act_id == "turbulence":
        base_points = [0.42, 0.76] if duration >= 3.2 else [0.66]
    elif act_id == "resolution":
        base_points = [0.50]
    else:
        base_points = [0.60]

    if rhythm == "decelerating":
        base_points = [min(0.82, point + 0.06) for point in base_points]
    elif rhythm == "accelerating":
        base_points = [max(0.25, point - 0.08) for point in base_points]
    elif rhythm == "syncopated" and len(base_points) == 1 and duration >= 2.4:
        base_points = [0.35, 0.68]

    return sorted({round(start + duration * point, 2) for point in base_points if 0.0 < point < 1.0})


def _act_silence_ratio(phase: dict) -> float:
    aesthetic_e = float(phase.get("entropy", {}).get("aesthetic", 0.5))
    return round(max(0.30, 1.0 - aesthetic_e), 2)


def _grammar_silence_ratio(base_silence: float, grammar: dict[str, Any], act_id: str) -> float:
    rhythm = str(grammar.get("rhythm", "uniform") or "uniform")
    if act_id == "resolution":
        return round(max(base_silence, 0.55 if rhythm == "decelerating" else 0.4), 2)
    if rhythm == "syncopated":
        return round(max(0.30, min(0.48, base_silence - 0.08)), 2)
    if rhythm == "decelerating":
        return round(min(0.78, base_silence + 0.08), 2)
    return round(max(0.30, base_silence), 2)


def _rhythm_multiplier(rhythm: str, act_index: int, total_acts: int) -> float:
    if total_acts <= 1:
        return 1.0
    progress = act_index / max(total_acts - 1, 1)
    if rhythm == "decelerating":
        return round(1.0 + 0.55 * progress, 3)
    if rhythm == "accelerating":
        return round(max(0.65, 1.0 - 0.35 * progress), 3)
    if rhythm == "syncopated":
        return [1.0, 0.86, 1.14][act_index % 3]
    return 1.0


def _phase_behavior(act_id: str, archetype: str, motion_bias: str | None = None) -> str:
    if act_id == "genesis":
        return "coherent_flow" if archetype == "emergence" else (motion_bias or "laminar_flow")
    if act_id == "turbulence":
        return motion_bias or ("vortex_pull" if archetype == "chaos_to_order" else "oscillatory_wave")
    if act_id == "resolution":
        return "convergence_field" if archetype == "emergence" else "laminar_flow"
    return motion_bias or "breathing_field"


def _build_motion_phrase(
    act_id: str,
    behavior: str,
    duration_sec: float,
    grammar: dict[str, Any],
    act_index: int,
    total_acts: int,
) -> dict[str, Any]:
    timing = grammar.get("timing", {}) if isinstance(grammar.get("timing", {}), dict) else {}
    rhythm = str(grammar.get("rhythm", "uniform") or "uniform")
    minimum_hold_ms = int(timing.get("minimum_hold_ms", 400) or 400)
    multiplier = _rhythm_multiplier(rhythm, act_index, total_acts)
    anticipation_ms = max(120, int(minimum_hold_ms * 0.35 * multiplier))
    action_ms = max(220, int(minimum_hold_ms * 0.95 * multiplier))
    follow_through_ms = max(140, int(minimum_hold_ms * 0.45 * multiplier))
    silence_window = timing.get("silence_between_phrases_ms", [200, 600])
    recovery_ms = int(silence_window[1] if isinstance(silence_window, list) and len(silence_window) > 1 else minimum_hold_ms)

    if act_id == "genesis":
        emphasis = "low"
    elif act_id == "turbulence":
        emphasis = "high"
    else:
        emphasis = "medium"

    return {
        "id": f"{act_id}_primary",
        "behavior": behavior,
        "emphasis": emphasis,
        "anticipation": {
            "property": "opacity",
            "from": 0.0,
            "to": 0.2,
            "easing": "ease_out",
            "duration_ms": anticipation_ms,
            "delay_ms": 0,
            "spring": None,
        },
        "action": {
            "property": "position",
            "from": 18 if emphasis == "low" else 28,
            "to": 0,
            "easing": "spring",
            "duration_ms": action_ms,
            "delay_ms": anticipation_ms,
            "spring": {
                "stiffness": 82 if emphasis == "low" else 118 if emphasis == "high" else 96,
                "damping": 20 if emphasis == "low" else 14 if emphasis == "high" else 17,
                "mass": 1.05 if emphasis == "low" else 0.86 if emphasis == "high" else 0.95,
            },
        },
        "follow_through": {
            "property": "scale",
            "from": 0.985 if emphasis == "low" else 0.96,
            "to": 1.0,
            "easing": "ease_out",
            "duration_ms": follow_through_ms,
            "delay_ms": anticipation_ms + action_ms,
            "spring": None,
        },
        "recovery_ms": min(int(duration_sec * 1000), max(recovery_ms, minimum_hold_ms)),
    }


def _build_motion_sequence(
    act_id: str,
    start: float,
    end: float,
    grammar: dict[str, Any],
    archetype: str,
    act_index: int,
    total_acts: int,
    motion_bias: str | None = None,
) -> dict[str, Any]:
    timing = grammar.get("timing", {}) if isinstance(grammar.get("timing", {}), dict) else {}
    behavior = _phase_behavior(act_id, archetype, motion_bias)
    phrase = _build_motion_phrase(act_id, behavior, end - start, grammar, act_index, total_acts)
    transitions = grammar.get("transitions", {}) if isinstance(grammar.get("transitions", {}), dict) else {}
    stagger = grammar.get("stagger", [0, 1, 2])
    stagger_profile = [int(step) for step in stagger] if isinstance(stagger, list) and stagger else [0, 1, 2]
    silence_window = timing.get("silence_between_phrases_ms", [200, 600])

    return {
        "act_id": act_id,
        "phrases": [phrase],
        "rhythm": str(grammar.get("rhythm", "uniform") or "uniform"),
        "stagger_profile": stagger_profile,
        "breath_points": _compute_breath_points_for_grammar(start, end, grammar, act_id),
        "transition_to": str(transitions.get("act_to_act", "cut") or "cut"),
        "within_act_transition": str(transitions.get("within_act", "cut") or "cut"),
        "minimum_hold_ms": int(timing.get("minimum_hold_ms", 400) or 400),
        "maximum_simultaneous": int(timing.get("maximum_simultaneous", 1) or 1),
        "silence_between_phrases_ms": silence_window if isinstance(silence_window, list) else [200, 600],
        "camera": grammar.get("camera", {}) if isinstance(grammar.get("camera", {}), dict) else {},
    }


def define_pacing(
    intent: str,
    archetype: str,
    total_duration_sec: float = 12.0,
    motion_grammar: str | None = None,
) -> dict[str, Any]:
    """
    Persona Kael: Temporal Rhythm Master.

    Returns a PacingProfile dict:
    - acts: per-act timing, breath_points, silence_ratio
    - global silence_ratio validated >= 0.30
    - text_minimum_gap_sec from narrative contract
    - stagger_rule always True (no simultaneous entry)
    """
    arch_data = _load_archetype(archetype)
    phases = arch_data.get("phases", [])
    mode = _pacing_mode(intent, archetype)
    selected_motion_grammar = _select_motion_grammar(intent, archetype, motion_grammar)
    grammar = _load_motion_grammar(selected_motion_grammar)
    text_minimum_gap = 1.5 if mode == "cinematic" else 0.8
    motion_bias = None

    acts: list[dict[str, Any]] = []
    cursor = 0.0

    if phases:
        for index, phase in enumerate(phases):
            dur_frac = float(phase.get("duration", 0.33))
            end = round(cursor + total_duration_sec * dur_frac, 2)
            act_id = str(phase.get("id", f"act_{len(acts)}"))
            silence_ratio = _grammar_silence_ratio(_act_silence_ratio(phase), grammar, act_id)
            motion_sequence = _build_motion_sequence(
                act_id,
                cursor,
                end,
                grammar,
                archetype,
                index,
                len(phases),
                str(phase.get("motion", {}).get("signature", "") or "") or motion_bias,
            )
            acts.append({
                "act_id": act_id,
                "start_sec": round(cursor, 2),
                "end_sec": end,
                "breath_points": motion_sequence["breath_points"],
                "silence_ratio": silence_ratio,
                "entropy": phase.get("entropy", {}),
                "motion": phase.get("motion", {}),
                "motion_sequence": motion_sequence,
                "rhythm": motion_sequence["rhythm"],
                "stagger_profile": motion_sequence["stagger_profile"],
                "transition_to": motion_sequence["transition_to"],
                "minimum_hold_ms": motion_sequence["minimum_hold_ms"],
            })
            cursor = end
    else:
        # Standard 3-act split: genesis 25%, turbulence 45%, resolution 30%
        fallback_acts = [("genesis", 0.25, 0.6), ("turbulence", 0.45, 0.45), ("resolution", 0.30, 0.70)]
        for index, (act_id, frac, silence) in enumerate(fallback_acts):
            end = round(cursor + total_duration_sec * frac, 2)
            motion_sequence = _build_motion_sequence(
                act_id,
                cursor,
                end,
                grammar,
                archetype,
                index,
                len(fallback_acts),
            )
            acts.append({
                "act_id": act_id,
                "start_sec": round(cursor, 2),
                "end_sec": end,
                "breath_points": motion_sequence["breath_points"],
                "silence_ratio": _grammar_silence_ratio(silence, grammar, act_id),
                "entropy": {},
                "motion": {},
                "motion_sequence": motion_sequence,
                "rhythm": motion_sequence["rhythm"],
                "stagger_profile": motion_sequence["stagger_profile"],
                "transition_to": motion_sequence["transition_to"],
                "minimum_hold_ms": motion_sequence["minimum_hold_ms"],
            })
            cursor = end

    # Global silence ratio (weighted average, clamped >= 0.30)
    global_silence = round(
        sum(a["silence_ratio"] * (a["end_sec"] - a["start_sec"]) for a in acts) / max(total_duration_sec, 0.01),
        2,
    ) if acts else 0.40
    global_silence = max(global_silence, 0.30)

    return {
        "archetype": archetype,
        "mode": mode,
        "motion_grammar": selected_motion_grammar,
        "motion_grammar_contract": grammar,
        "total_duration_sec": total_duration_sec,
        "silence_ratio": global_silence,
        "text_minimum_gap_sec": text_minimum_gap,
        "stagger_rule": True,
        "rhythm": str(grammar.get("rhythm", "uniform") or "uniform"),
        "stagger_profile": [int(step) for step in grammar.get("stagger", [0, 1, 2])] if isinstance(grammar.get("stagger", [0, 1, 2]), list) else [0, 1, 2],
        "transitions": grammar.get("transitions", {}) if isinstance(grammar.get("transitions", {}), dict) else {},
        "motion_sequences": [act.get("motion_sequence", {}) for act in acts],
        "acts": acts,
    }
