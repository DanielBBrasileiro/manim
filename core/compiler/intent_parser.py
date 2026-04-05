import re
from dataclasses import dataclass, field
from typing import List

from core.intelligence.model_router import TASK_PLAN
from core.intelligence.ollama_client import generate_scene_plan


@dataclass
class Intent:
    tension: str
    density: str
    transformation: str
    pacing: str
    tone: str
    raw_tokens: List[str] = field(default_factory=list)
    source: str = "heuristic"
    confidence: float = 0.0
    scene_plan: dict = field(default_factory=dict)
    llm_metadata: dict = field(default_factory=dict)

# Dicionários Semânticos (Lexicon)
TENSION_MAP = {
    "high": ["chaos", "explosion", "intense", "violent", "fragmented", "sharp", "fast", "tension", "turbulent"],
    "low": ["calm", "minimal", "soft", "slow", "peaceful", "fluid", "continuous", "gentle"]
}

DENSITY_MAP = {
    "high": ["dense", "crowded", "complex", "stars", "thousands", "particles", "heavy", "grid"],
    "low": ["sparse", "clean", "minimalist", "empty", "void", "single", "focus", "light"]
}

TRANSFORMATION_MAP = {
    "chaos_to_order": ["organize", "align", "structure", "harmony", "chaos to order", "sort"],
    "order_to_chaos": ["explode", "shatter", "disperse", "entropy", "break", "order to chaos"],
    "emergence": ["birth", "grow", "emerge", "scale", "appear", "starting", "reveal"],
    "gravitational_collapse": ["attract", "collapse", "singularity", "pull", "center", "vortex"]
}

PACING_MAP = {
    "cinematic": ["slow", "gradual", "epic", "cinematic", "smooth", "breathe"],
    "dynamic": ["fast", "dynamic", "glitch", "sudden", "rhythmic", "beat", "snap"]
}

TONE_MAP = {
    "dark": ["dark", "shadow", "cyber", "brutal", "abyss", "unknown"],
    "light": ["light", "bright", "neon", "clean", "corporate", "lucid"]
}

def normalize(text: str) -> List[str]:
    # Converte para minúsculas e remove pontuação não-essencial
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s_]', '', text)
    return text.split()

def detect_score(tokens: List[str], concept_map: dict, default: str) -> str:
    scores = {key: 0 for key in concept_map.keys()}
    
    # 1-gram
    for word in tokens:
        for key, keywords in concept_map.items():
            if word in keywords:
                scores[key] += 1
                
    # 2-grams (simplificado para "chaos to order" etc)
    text_joined = " ".join(tokens)
    for key, keywords in concept_map.items():
        for kw in keywords:
            if " " in kw and kw in text_joined:
                scores[key] += 2  # Bigrams têm mais peso
                
    # Vencedor
    best_match = max(scores.items(), key=lambda x: x[1])
    if best_match[1] > 0:
        return best_match[0]
        
    return default


def _extract_raw_text(seed: dict | str) -> str:
    if isinstance(seed, (dict, list)):
        fragments = _collect_text_fragments(seed)
        return " ".join(fragment for fragment in fragments if fragment)
    return str(seed)


def _collect_text_fragments(value) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []

    if isinstance(value, dict):
        fragments: list[str] = []
        for item in value.values():
            fragments.extend(_collect_text_fragments(item))
        return fragments

    if isinstance(value, list):
        fragments: list[str] = []
        for item in value:
            fragments.extend(_collect_text_fragments(item))
        return fragments

    return []


def _map_scene_plan_to_intent(raw_text: str, scene_plan) -> Intent:
    tone = "light"
    palette = str(scene_plan.assets.get("palette", "")).lower()
    effects = {effect.lower() for effect in scene_plan.effects}
    if "dark" in palette or "grain_overlay" in effects or "post_glitch_light" in effects:
        tone = "dark"

    transformation = scene_plan.archetype
    if transformation == "fragmented_reveal":
        tension = "high"
        density = "high"
    elif transformation == "loop_stability":
        tension = "low"
        density = "low"
    elif transformation == "gravitational_collapse":
        tension = "high"
        density = "medium"
    elif transformation == "chaos_to_order":
        tension = "medium"
        density = "high"
    elif transformation == "order_to_chaos":
        tension = "high"
        density = "medium"
    else:
        tension = "medium"
        density = "medium"

    tokens = normalize(raw_text)
    return Intent(
        tension=tension,
        density=density,
        transformation=transformation,
        pacing=scene_plan.pacing,
        tone=tone,
        raw_tokens=tokens,
        source="ollama",
        confidence=scene_plan.confidence,
        scene_plan=scene_plan.to_dict(),
        llm_metadata=dict(scene_plan.llm_metadata),
    )


def parse_intent(seed: dict, asset_registry: dict | None = None, task_type: str = TASK_PLAN) -> Intent:
    """Transforma o briefing natural (YAML ou texto livre) em um Objeto de Intenção Semântica."""

    raw_text = _extract_raw_text(seed)

    scene_plan = generate_scene_plan(raw_text, asset_registry=asset_registry, task_type=task_type)
    if scene_plan is not None:
        return _map_scene_plan_to_intent(raw_text, scene_plan)

    tokens = normalize(raw_text)

    tension = detect_score(tokens, TENSION_MAP, "medium")
    density = detect_score(tokens, DENSITY_MAP, "medium")
    transformation = detect_score(tokens, TRANSFORMATION_MAP, "emergence")
    pacing = detect_score(tokens, PACING_MAP, "cinematic")
    tone = detect_score(tokens, TONE_MAP, "dark")

    return Intent(
        tension=tension,
        density=density,
        transformation=transformation,
        pacing=pacing,
        tone=tone,
        raw_tokens=tokens,
        source="heuristic",
        confidence=0.0,
        scene_plan={},
        llm_metadata={},
    )
