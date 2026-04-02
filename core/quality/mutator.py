"""
mutator.py — Parameter mutation logic for self-correcting quality loops.

This module provides deterministic "nudges" to manifest parameters based on
judge findings (weak dimensions or objective signals).
"""

from typing import Any, Dict, List, Optional

# Bounding constants to preserve "Premium Architecture"
LIMITS = {
    "negative_space_target": (0.2, 0.75),
    "accent_intensity": (0.0, 0.8),
    "grain": (0.02, 0.2),
    "max_words_per_screen": (1, 8),
    "minimum_hold_ms": (150, 1500),
}


def mutate_render_manifest(
    manifest: Dict[str, Any],
    findings: List[Dict[str, Any]],
    objective_signals: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Applies small, bounded mutations to manifest parameters based on judge results.

    Args:
        manifest: The current render manifest (mutated in-place or copied).
        findings: List of issue dictionaries (from PreviewIssue or DimensionScore).
        objective_signals: Optional raw objective metrics from the judge.

    Returns:
        The mutated manifest with recorded changes.
    """
    mutated = manifest  # We modify the dict reference directly as per user request scope
    mutations = []

    # Helper to apply bounded shift
    def _shift(key: str, delta: float, path: Optional[List[str]] = None):
        targets_to_patch = [mutated]
        
        # If this is an artifact_plan, also patch all individual targets
        if "targets" in mutated and isinstance(mutated["targets"], list):
            targets_to_patch.extend([t for t in mutated["targets"] if isinstance(t, dict)])
            
        for target in targets_to_patch:
            curr = target
            if path:
                for segment in path:
                    if segment not in curr:
                        curr[segment] = {}
                    curr = curr[segment]
            
            old_val = curr.get(key)
            if old_val is None:
                # Try to find a sensible starting point if missing
                old_val = LIMITS.get(key, (0, 1))[0]

            try:
                new_val = float(old_val) + delta
                # Apply clamping
                low, high = LIMITS.get(key, (-1000, 1000))
                new_val = max(low, min(high, new_val))
                
                if abs(new_val - float(old_val)) > 0.001:
                    curr[key] = int(new_val) if isinstance(old_val, int) else round(new_val, 3)
                    # Only record main mutation
                    if target is mutated:
                        mutations.append({
                            "parameter": key,
                            "old": old_val,
                            "new": curr[key],
                            "reason": f"Signal-driven nudge ({delta:+.2f})"
                        })
            except (ValueError, TypeError):
                pass

    # Extract finding codes/names
    codes = {f.get("code", f.get("name", "")).lower() for f in findings}
    
    # 1. Spatial Intelligence / Negative Space
    if "poor_negative_space" in codes or "spatial_intelligence" in codes:
        _shift("negative_space_target", 0.1)

    # 2. Overcrowding / Hierarchy
    if "overcrowding" in codes or "hierarchy_strength" in codes:
        _shift("max_words_per_screen", -1, ["quality_constraints"])
        _shift("max_words_per_frame", -1, ["copy_budget"])

    # 3. Brand Discipline / Accents
    if "brand_discipline" in codes or "weak_focal_point" in codes:
        _shift("accent_intensity", -0.1)

    # 4. Material Finish / Grain
    if "material_finish" in codes:
        # Check objective signals if grain variance is high
        if objective_signals and objective_signals.get("grain_variance", 0) > 0.1:
            _shift("grain", -0.05)
        else:
            _shift("grain", 0.02) # Subtly increase if it felt "dirty" (low quality)

    # 5. Motion Pacing / Temporal Rhythm
    if "motion_pacing" in codes or "temporal_rhythm" in codes or "silence_quality" in codes:
        _shift("minimum_hold_ms", 50, ["quality_constraints"])
        _shift("target_silence_ratio", 0.05, ["copy_budget"])

    # Log mutations to the manifest for transparency
    if mutations:
        if "_mutation_audit" not in mutated:
            mutated["_mutation_audit"] = []
        mutated["_mutation_audit"].append(mutations)

    return mutated
