"""Persona Zara: Physics & Entropy Engineer.

Reads archetype YAML phases[] for granular per-phase entropy curves.
Returns EntropyProfile dict with flat() backward-compat summary.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
_ARCHETYPE_DIR = ROOT / "contracts" / "narrative" / "archetypes"
_SIGNATURES_DIR = ROOT / "contracts" / "motion" / "signatures"


def _load_archetype(name: str) -> dict[str, Any]:
    path = _ARCHETYPE_DIR / f"{name}.yaml"
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _load_signature(name: str) -> dict[str, Any]:
    if not name:
        return {}
    path = _SIGNATURES_DIR / f"{name}.yaml"
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


# Backward compat alias used by workers.py
def _load_archetypes(archetypes_dir: str | None = None) -> dict[str, Any]:
    from core.agents.aria import _load_archetypes as _aria_load
    return _aria_load(archetypes_dir or str(_ARCHETYPE_DIR))


def define_entropy(archetype_name: str, base_entropy: float = 0.5) -> dict[str, Any]:
    """
    Persona Zara: Engenharia Física e Comportamental.

    Returns EntropyProfile dict:
    - phases: per-phase granular entropy + motion params
    - summary: mean values (backward compat flat dict)
    """
    arch_data = _load_archetype(archetype_name)
    phases_raw = arch_data.get("phases", [])

    if phases_raw:
        phases = []
        for phase in phases_raw:
            entropy = phase.get("entropy", {})
            phases.append({
                "id": str(phase.get("id", "phase")),
                "duration_frac": float(phase.get("duration", 0.33)),
                "physical": float(entropy.get("physical", base_entropy)),
                "structural": float(entropy.get("structural", base_entropy)),
                "aesthetic": float(entropy.get("aesthetic", base_entropy)),
                "motion_params": phase.get("motion", {}),
            })

        n = len(phases)
        summary = {
            "physical": round(sum(p["physical"] for p in phases) / n, 3),
            "structural": round(sum(p["structural"] for p in phases) / n, 3),
            "aesthetic": round(sum(p["aesthetic"] for p in phases) / n, 3),
        }
        return {"archetype": archetype_name, "phases": phases, "summary": summary}

    # Fallback: legacy static mapping from entropy_profile string
    profile_str = arch_data.get("entropy_profile", "medium")
    _LEGACY = {
        "low_to_medium":  {"physical": 0.3, "structural": 0.2, "aesthetic": 0.4},
        "high_to_low":    {"physical": 0.8, "structural": 0.6, "aesthetic": 0.7},
        "low_to_high":    {"physical": 0.4, "structural": 0.3, "aesthetic": 0.5},
        "high_structural": {"physical": 0.6, "structural": 0.9, "aesthetic": 0.6},
        "rhythmic":       {"physical": 0.5, "structural": 0.5, "aesthetic": 0.5},
    }
    flat = _LEGACY.get(profile_str, {"structural": base_entropy, "aesthetic": base_entropy, "physical": base_entropy})
    return {"archetype": archetype_name, "phases": [], "summary": flat}


def resolve_motion_bias(archetype_name: str) -> str:
    """Extrai a assinatura primária do arquétipo com enriquecimento do signature YAML."""
    arch_data = _load_archetype(archetype_name)
    bias_name = arch_data.get("motion_bias") or ""
    if not bias_name:
        return ""
    # Verify signature exists and is non-trivial
    sig = _load_signature(bias_name)
    return bias_name if sig else bias_name
