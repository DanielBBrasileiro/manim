"""
semantic_memory.py — Semantic vector memory for Persona Uma (AIOX Studio)

Encodes creative signatures as ~10-dimensional numeric vectors and computes
cosine similarity to measure how different a new signature is from recent history.
No external ML libraries required — uses numpy if available, math otherwise.
"""

import math
import os
import yaml

# ---------------------------------------------------------------------------
# Encoding maps
# ---------------------------------------------------------------------------

PACING_MAP = {
    "cinematic": 0.2,
    "slow": 0.3,
    "meditative": 0.35,
    "dynamic": 0.8,
    "rhythmic": 0.65,
    "urgent": 1.0,
    "fast": 0.9,
}

AESTHETIC_FAMILY_MAP = {
    "silent_architecture": 0.0,
    "brutalist_signal": 0.33,
    "organic_field": 0.66,
    "data_narrative": 1.0,
}

# entropy_profile string → (physical, structural, aesthetic) numeric approximations
ENTROPY_PROFILE_STRING_MAP = {
    "low_to_medium":  (0.15, 0.15, 0.40),
    "low_to_high":    (0.15, 0.15, 0.85),
    "medium_to_high": (0.50, 0.50, 0.85),
    "high_to_low":    (0.85, 0.85, 0.15),
    "high_structural": (0.50, 0.90, 0.50),
    "high":           (0.85, 0.85, 0.85),
    "medium":         (0.50, 0.50, 0.50),
    "low":            (0.15, 0.15, 0.15),
}

# motion_bias strings → hash-like stable float
MOTION_BIAS_MAP = {
    "scattered_to_aligned": 0.10,
    "inward_to_outward":    0.20,
    "outward_to_inward":    0.30,
    "lateral":              0.40,
    "rotational":           0.50,
    "oscillating":          0.60,
    "pulsing":              0.70,
    "collapsing":           0.80,
    "expanding":            0.90,
    "breathing_field":      0.55,
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _stable_hash_norm(s: str) -> float:
    """Return a stable 0-1 float from a string using Python's built-in hash seed=0 trick."""
    # Use sum of (char * position) to get a seed-independent, stable hash
    if not s:
        return 0.5
    h = 0
    for i, c in enumerate(s):
        h = (h * 31 + ord(c)) & 0xFFFFFFFF
    return (h % 10000) / 10000.0


def _load_archetype_meta(archetype_name: str, archetypes_dir: str) -> dict:
    """Load YAML for a given archetype id. Returns {} on failure."""
    if not archetype_name:
        return {}
    path = os.path.join(archetypes_dir, f"{archetype_name}.yaml")
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _resolve_entropy_triple(entry: dict) -> tuple:
    """
    Extract (physical, structural, aesthetic) floats from an entry dict.
    Handles both flat dict entries and nested creative_plan entries.
    Returns (physical, structural, aesthetic) each in [0, 1].
    """
    # Try direct top-level entropy_profile dict
    ep = entry.get("entropy_profile", {})

    if isinstance(ep, dict):
        raw = ep.get("raw", ep)
        physical   = float(raw.get("physical",   ep.get("physical",   0.5)))
        structural = float(raw.get("structural", ep.get("structural", 0.5)))
        aesthetic  = float(raw.get("aesthetic",  ep.get("aesthetic",  0.5)))
        return (physical, structural, aesthetic)

    if isinstance(ep, str):
        return ENTROPY_PROFILE_STRING_MAP.get(ep, (0.5, 0.5, 0.5))

    # Try nested creative_plan.entropy
    cp = entry.get("creative_plan", {})
    if cp:
        ent = cp.get("entropy", {})
        if ent:
            return (
                float(ent.get("physical",   0.5)),
                float(ent.get("structural", 0.5)),
                float(ent.get("aesthetic",  0.5)),
            )

    return (0.5, 0.5, 0.5)


def _resolve_pacing(entry: dict) -> float:
    pacing = entry.get("pacing")
    if not pacing:
        pacing = entry.get("creative_plan", {}).get("pacing", "dynamic")
    return PACING_MAP.get(str(pacing).lower(), 0.5)


def _resolve_aesthetic_family(entry: dict) -> float:
    fam = entry.get("aesthetic_family")
    if not fam:
        fam = entry.get("creative_plan", {}).get("aesthetic_family", "")
    return AESTHETIC_FAMILY_MAP.get(str(fam).lower(), 0.5)


def _resolve_archetype_name(entry: dict) -> str:
    name = (
        entry.get("narrative_archetype")
        or entry.get("archetype")
        or entry.get("creative_plan", {}).get("archetype")
        or entry.get("output_signature", {}).get("structure")
        or ""
    )
    return str(name).lower().strip()


def _resolve_motion_signature(entry: dict) -> str:
    ms = (
        entry.get("motion_bias")
        or entry.get("creative_plan", {}).get("interpretation", {}).get("motion_signature")
        or entry.get("output_signature", {}).get("motion")
        or ""
    )
    return str(ms).lower().strip()

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def encode_signature(
    signature: dict,
    archetypes_dir: str = "contracts/narrative/archetypes",
) -> list:
    """
    Encode a creative signature as a numeric vector of 10 dimensions.

    Dimensions:
      0  physical entropy (from signature or archetype YAML)
      1  structural entropy
      2  aesthetic entropy
      3  pacing numeric
      4  aesthetic_family numeric
      5  archetype name hash (stable, 0-1)
      6  motion_signature hash (stable, 0-1)
      7  archetype YAML entropy_profile physical approx
      8  archetype YAML entropy_profile structural approx
      9  archetype YAML entropy_profile aesthetic approx
    """
    # -- dims 0-2: entropy from the signature itself
    phys, struct, aes = _resolve_entropy_triple(signature)

    # -- dim 3: pacing
    pacing_val = _resolve_pacing(signature)

    # -- dim 4: aesthetic family
    aesthetic_val = _resolve_aesthetic_family(signature)

    # -- dim 5: archetype name hash
    arch_name = _resolve_archetype_name(signature)
    arch_hash = _stable_hash_norm(arch_name)

    # -- dim 6: motion signature hash
    motion_str = _resolve_motion_signature(signature)
    if not motion_str:
        # try loading from archetype YAML
        meta = _load_archetype_meta(arch_name, archetypes_dir)
        motion_str = str(meta.get("motion_bias", "")).lower()
    motion_val = MOTION_BIAS_MAP.get(motion_str, _stable_hash_norm(motion_str))

    # -- dims 7-9: archetype YAML entropy profile
    meta = _load_archetype_meta(arch_name, archetypes_dir)
    yaml_ep = meta.get("entropy_profile", "medium")
    if isinstance(yaml_ep, str):
        yp, ys, ya = ENTROPY_PROFILE_STRING_MAP.get(yaml_ep, (0.5, 0.5, 0.5))
    else:
        yp, ys, ya = 0.5, 0.5, 0.5

    return [phys, struct, aes, pacing_val, aesthetic_val, arch_hash, motion_val, yp, ys, ya]


def cosine_similarity(v1: list, v2: list) -> float:
    """
    Cosine similarity between two equal-length numeric vectors.
    Returns value in [-1, 1]; practically [0, 1] for non-negative vectors.
    Falls back to pure math if numpy is unavailable.
    """
    try:
        import numpy as np
        a = np.array(v1, dtype=float)
        b = np.array(v2, dtype=float)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
    except ImportError:
        dot = sum(x * y for x, y in zip(v1, v2))
        norm_a = math.sqrt(sum(x * x for x in v1))
        norm_b = math.sqrt(sum(y * y for y in v2))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


def vector_similarity(v1: list, v2: list) -> float:
    """
    Similarity metric designed for bounded [0,1] feature vectors.

    Pure cosine similarity clusters near 1.0 when all components are positive,
    making it ineffective for discrimination here. This function uses normalised
    Euclidean distance as the primary measure, with a calibration factor to
    spread the similarity range across [0, 1] for typical creative signatures.

    Returns similarity in [0, 1] — higher means more similar.

    Calibration:
      - Max possible Euclidean distance in [0,1]^n is sqrt(n) ≈ 3.16 for n=10
      - Typical observed distances between distinct signatures: 0.3–0.55 of max
      - We rescale so that ~0.55*max_dist maps to similarity=0.0 (very different)
        and 0 distance maps to 1.0 (identical)
      - effective_max = 0.55 * sqrt(n)  (signatures differing by ~half max = 0 similarity)
    """
    n = len(v1)
    if n == 0:
        return 0.0

    try:
        import numpy as np
        euc_dist = float(np.linalg.norm(np.array(v1, dtype=float) - np.array(v2, dtype=float)))
    except ImportError:
        euc_dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))

    # Calibrated normalisation: signatures at ~55% of max_dist are considered 0-similar
    effective_max = 0.55 * math.sqrt(n)
    similarity = 1.0 - (euc_dist / effective_max)
    return max(0.0, min(1.0, similarity))


def get_diversity_score(
    current_signature: dict,
    history: list,
    top_k: int = 5,
    archetypes_dir: str = "contracts/narrative/archetypes",
) -> float:
    """
    Return a diversity score in [0.0, 1.0]:
      1.0 = completely unique compared to recent history
      0.0 = identical to the most recent entry

    Algorithm:
      1. Encode current_signature into a vector.
      2. Encode up to top_k most recent history entries.
      3. Compute cosine similarity between current and each history vector.
      4. Take the MAXIMUM similarity (worst-case / most-similar comparison).
      5. diversity_score = 1.0 - max_similarity
         → High similarity → low diversity (penalised)
         → Low similarity → high diversity (rewarded)
    """
    if not history:
        return 1.0

    current_vec = encode_signature(current_signature, archetypes_dir)

    recent = history[-top_k:] if len(history) >= top_k else history
    similarities = []
    for entry in recent:
        try:
            hist_vec = encode_signature(entry, archetypes_dir)
            sim = vector_similarity(current_vec, hist_vec)
            similarities.append(sim)
        except Exception:
            continue

    if not similarities:
        return 1.0

    max_sim = max(similarities)
    # Clamp to [0, 1] to handle floating-point edge cases
    diversity = 1.0 - max(0.0, min(1.0, max_sim))
    return round(diversity, 4)
