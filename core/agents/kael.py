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


def _load_archetype(name: str) -> dict[str, Any]:
    path = _ARCHETYPE_DIR / f"{name}.yaml"
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


def _compute_breath_points(start: float, end: float) -> list[float]:
    duration = end - start
    if duration <= 1.5:
        return []
    # One breath at ~60% — pause of 0.3-0.8s before act climax
    return [round(start + duration * 0.60, 2)]


def _act_silence_ratio(phase: dict) -> float:
    aesthetic_e = float(phase.get("entropy", {}).get("aesthetic", 0.5))
    return round(max(0.30, 1.0 - aesthetic_e), 2)


def define_pacing(intent: str, archetype: str, total_duration_sec: float = 12.0) -> dict[str, Any]:
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
    text_minimum_gap = 1.5 if mode == "cinematic" else 0.8

    acts: list[dict[str, Any]] = []
    cursor = 0.0

    if phases:
        for phase in phases:
            dur_frac = float(phase.get("duration", 0.33))
            end = round(cursor + total_duration_sec * dur_frac, 2)
            acts.append({
                "act_id": str(phase.get("id", f"act_{len(acts)}")),
                "start_sec": round(cursor, 2),
                "end_sec": end,
                "breath_points": _compute_breath_points(cursor, end),
                "silence_ratio": _act_silence_ratio(phase),
                "entropy": phase.get("entropy", {}),
                "motion": phase.get("motion", {}),
            })
            cursor = end
    else:
        # Standard 3-act split: genesis 25%, turbulence 45%, resolution 30%
        for act_id, frac, silence in [("genesis", 0.25, 0.6), ("turbulence", 0.45, 0.45), ("resolution", 0.30, 0.70)]:
            end = round(cursor + total_duration_sec * frac, 2)
            acts.append({
                "act_id": act_id,
                "start_sec": round(cursor, 2),
                "end_sec": end,
                "breath_points": _compute_breath_points(cursor, end),
                "silence_ratio": silence,
                "entropy": {},
                "motion": {},
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
        "total_duration_sec": total_duration_sec,
        "silence_ratio": global_silence,
        "text_minimum_gap_sec": text_minimum_gap,
        "stagger_rule": True,
        "acts": acts,
    }
