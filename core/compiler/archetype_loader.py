import os
import yaml

ARCHETYPE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "contracts", "narrative", "archetypes"
)

def get_archetype_timeline(archetype_id: str, bias: str = None) -> list:
    """Reads the narrative archetype contract from YAML and returns a timeline.
    Falls back to a safe default if the contract does not exist or is malformed.
    """
    file_path = os.path.join(ARCHETYPE_DIR, f"{archetype_id}.yaml")
    
    # Safe fallback if file doesn't exist
    if not os.path.exists(file_path):
        return _legacy_fallback(archetype_id, bias)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
            if not data:
                return _legacy_fallback(archetype_id, bias)
                
            # Pattern 1: Explicit Phases (e.g. resolution.yaml)
            if "phases" in data and isinstance(data["phases"], list):
                return _normalize_phases(data["phases"], bias)
                
            # Pattern 2: Simple Structure Array (e.g. emergence.yaml)
            if "structure" in data and isinstance(data["structure"], list):
                return _normalize_structure(data["structure"], data.get("entropy_profile"), bias)
                
            # Malformed or unrecognized format
            return _legacy_fallback(archetype_id, bias)
            
    except Exception:
        # Fallback gently on any read/parse error
        return _legacy_fallback(archetype_id, bias)


def _normalize_phases(phases: list, bias: str) -> list:
    timeline = []
    cursor = 0.0
    
    for idx, phase in enumerate(phases):
        duration = float(phase.get("duration", 0.0))
        # fallback for missing duration
        if duration == 0.0:
            duration = 1.0 / len(phases)
            
        start = cursor
        end = cursor + duration
        cursor = end
        
        # Derive behavior from visual or motion bias
        behavior = phase.get("visual") or phase.get("id") or bias or "coherent_flow"
        
        # Derive tension from entropy if possible
        entropy = phase.get("entropy", {})
        tension = "medium"
        struct_entropy = float(entropy.get("structural", 0.5))
        if struct_entropy > 0.7:
            tension = "high"
        elif struct_entropy < 0.3:
            tension = "low"
            
        timeline.append({
            "phase": [round(start, 3), round(end, 3)],
            "behavior": behavior,
            "tension": tension
        })
        
    # Ensure it ends exactly at 1.0
    if timeline:
        timeline[-1]["phase"][1] = 1.0
        
    return timeline


def _normalize_structure(structure: list, entropy_profile: str, bias: str) -> list:
    timeline = []
    total = len(structure)
    if total == 0:
        return timeline
        
    step = 1.0 / total
    
    # Very basic entropy profile translation
    base_tension = "medium"
    if entropy_profile == "high_to_low":
        tensions = ["high", "medium", "low", "low"]
    elif entropy_profile == "low_to_medium":
        tensions = ["low", "low", "medium", "medium"]
    else:
        tensions = ["medium"] * total
        
    for i, step_name in enumerate(structure):
        start = i * step
        end = (i + 1) * step
        
        # Map step name to some behavior
        # In the absence of strict mappings, we use the step name or bias
        behavior = step_name
        if i == total // 2 and bias:
            behavior = bias  # Apply bias near the middle
            
        tension = tensions[i] if i < len(tensions) else base_tension
        
        timeline.append({
            "phase": [round(start, 3), round(end, 3)],
            "behavior": behavior,
            "tension": tension
        })
        
    # Ensure it ends exactly at 1.0
    if timeline:
        timeline[-1]["phase"][1] = 1.0
        
    return timeline


def _legacy_fallback(archetype: str, bias: str) -> list:
    if archetype == "emergence":
        return [
             {"phase": [0.0, 0.4], "behavior": "coherent_flow", "tension": "low"},
             {"phase": [0.4, 0.8], "behavior": bias or "scattered_to_aligned", "tension": "medium"},
             {"phase": [0.8, 1.0], "behavior": "convergence_field", "tension": "high"}
        ]
    elif archetype == "chaos_to_order":
        return [
             {"phase": [0.0, 0.3], "behavior": "chaotic_burst", "tension": "high"},
             {"phase": [0.3, 0.7], "behavior": bias or "vortex_pull", "tension": "medium"},
             {"phase": [0.7, 1.0], "behavior": "laminar_flow", "tension": "low"}
        ]
    elif archetype == "order_to_chaos":
        return [
             {"phase": [0.0, 0.4], "behavior": "laminar_flow", "tension": "low"},
             {"phase": [0.4, 0.7], "behavior": bias or "oscillatory_wave", "tension": "medium"},
             {"phase": [0.7, 1.0], "behavior": "chaotic_dispersion", "tension": "high"}
        ]
    else:
        return [
             {"phase": [0.0, 0.5], "behavior": bias or "laminar_flow", "tension": "medium"},
             {"phase": [0.5, 1.0], "behavior": "breathing_field", "tension": "medium"}
        ]
