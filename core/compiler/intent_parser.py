import re
from dataclasses import dataclass, field
from typing import List

@dataclass
class Intent:
    tension: str
    density: str
    transformation: str
    pacing: str
    tone: str
    raw_tokens: List[str] = field(default_factory=list)

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

def parse_intent(seed: dict) -> Intent:
    """Transforma o briefing natural (YAML ou texto livre) em um Objeto de Intenção Semântica."""
    
    # Extrai o texto consolidado
    if isinstance(seed, dict):
        # Se for um YAML estruturado
        raw_text = " ".join([str(v) for v in seed.values() if isinstance(v, str)])
    else:
        # Se for string livre
        raw_text = str(seed)
        
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
        raw_tokens=tokens
    )
