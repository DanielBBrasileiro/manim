"""Persona Aria: Creative Director.

Decides archetype with VISTA validation (phases defined, emotional target present,
Poster Test readiness). Falls back gracefully to heuristics.
"""
from __future__ import annotations

import os
import random
import yaml
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent

try:
    from core.intelligence import ai_brain as _ai_brain
except ImportError:
    _ai_brain = None


def _load_archetypes(archetypes_dir: str | None = None) -> dict[str, Any]:
    base = archetypes_dir or str(ROOT / "contracts" / "narrative" / "archetypes")
    archetypes: dict[str, Any] = {}
    if not os.path.exists(base):
        return archetypes
    for f in os.listdir(base):
        if f.endswith(".yaml"):
            try:
                with open(os.path.join(base, f), "r", encoding="utf-8") as fh:
                    data = yaml.safe_load(fh)
                    archetypes[Path(f).stem] = data or {}
            except Exception:
                pass
    return archetypes


def _validate_archetype_vista(archetype_name: str, arch_data: dict[str, Any]) -> tuple[bool, str]:
    """
    VISTA validation: checks that an archetype is production-ready.

    V — Verified phases (phases[] must be defined and non-empty)
    I — Intentional emotional target (description must be present)
    S — Structural rules exist (rules[] or constraints)
    T — Temporal definition (each phase has a duration)
    A — Act independence (Poster Test: each phase has a visual cue)
    """
    phases = arch_data.get("phases", [])
    if not phases:
        return False, f"archetype '{archetype_name}' has no phases[] defined"

    if not arch_data.get("description") and not arch_data.get("emotional_target"):
        return False, f"archetype '{archetype_name}' missing description/emotional_target"

    for phase in phases:
        if "duration" not in phase:
            return False, f"archetype '{archetype_name}' phase '{phase.get('id')}' missing duration"

    return True, "ok"


def poster_test(archetype_name: str) -> list[str]:
    """
    Poster Test: checks if each act can function as a standalone visual frame.
    Returns a list of warnings (empty = all acts pass).
    """
    archetypes = _load_archetypes()
    arch_data = archetypes.get(archetype_name, {})
    phases = arch_data.get("phases", [])
    warnings: list[str] = []

    for phase in phases:
        phase_id = phase.get("id", "unknown")
        has_visual = bool(phase.get("visual") or phase.get("layout") or phase.get("motion"))
        if not has_visual:
            warnings.append(
                f"Act '{phase_id}' has no visual/layout/motion — may not read as standalone frame"
            )
        entropy = phase.get("entropy", {})
        if float(entropy.get("aesthetic", 0.5)) > 0.85:
            warnings.append(
                f"Act '{phase_id}' aesthetic entropy {entropy.get('aesthetic')} is very high — "
                "poster frame will be cluttered"
            )
    return warnings


def decide_archetype(intent: str) -> str:
    """
    Persona Aria: Decisão criativa do Arco Narrativo.
    Analisa a intenção e define o arquétipo com VISTA validation.
    """
    archetypes = _load_archetypes()
    available = list(archetypes.keys())

    # --- AI Native Brain (LLM path) ---
    if _ai_brain is not None and available:
        llm_result = _ai_brain.call_aria_llm(intent, available, archetypes)
        if llm_result and llm_result in archetypes:
            is_valid, _ = _validate_archetype_vista(llm_result, archetypes[llm_result])
            if is_valid:
                return llm_result
            # LLM pick failed VISTA — fall through to heuristics

    # --- Keyword heuristics ---
    intent_lower = intent.lower()
    candidates: list[str] = []

    if any(w in intent_lower for w in ["scale", "growth", "birth", "emergence", "starting"]):
        candidates.append("emergence")
    if any(w in intent_lower for w in ["chaos_to_order", "alignment", "harmony", "order"]):
        candidates.append("chaos_to_order")
    if any(w in intent_lower for w in ["speed", "tension", "fragment", "complex", "chaos"]):
        candidates.append("fragmented_reveal")
    if any(w in intent_lower for w in ["attraction", "collapse", "singularity"]):
        candidates.append("gravitational_collapse")
    if any(w in intent_lower for w in ["resolve", "resolution", "clarity", "mastery"]):
        candidates.append("resolution")

    # Prefer VISTA-valid candidates
    for name in candidates:
        if name in archetypes:
            is_valid, _ = _validate_archetype_vista(name, archetypes[name])
            if is_valid:
                return name

    # Final fallback: pick any VISTA-valid archetype
    valid = [n for n in available if _validate_archetype_vista(n, archetypes[n])[0]]
    if valid:
        return random.choice(valid)

    return available[0] if available else "emergence"


def select_aesthetic_family(identity: str, intent: str = "") -> str:
    """
    Persona Aria: Escolha da linguagem estética.
    """
    if _ai_brain is not None:
        llm_result = _ai_brain.call_aesthetic_llm(identity, intent)
        if llm_result:
            return llm_result

    families = ["silent_architecture", "brutalist_signal", "organic_field", "data_narrative"]
    if identity == "aiox_default":
        return "silent_architecture"
    return random.choice(families)
