import random
import os
import yaml
from pathlib import Path

# AI Native Brain — optional LLM integration (graceful fallback se indisponível)
try:
    from core.intelligence import ai_brain as _ai_brain
except ImportError:
    _ai_brain = None


def _load_archetypes(archetypes_dir="contracts/narrative/archetypes"):
    archetypes = {}
    if not os.path.exists(archetypes_dir):
        return archetypes
    for f in os.listdir(archetypes_dir):
        if f.endswith(".yaml"):
            with open(os.path.join(archetypes_dir, f), 'r') as file:
                data = yaml.safe_load(file)
                archetypes[Path(f).stem] = data
    return archetypes


def decide_archetype(intent: str) -> str:
    """
    Persona Aria: Decisão criativa do Arco Narrativo.
    Analisa a intenção e define o arquétipo.

    Tenta Claude Haiku via ai_brain primeiro; fallback para heurísticas de keywords.
    """
    archetypes = _load_archetypes()
    available = list(archetypes.keys())

    # --- AI Native Brain (LLM path) ---
    if _ai_brain is not None and available:
        llm_result = _ai_brain.call_aria_llm(intent, available, archetypes)
        if llm_result:
            return llm_result

    # --- Fallback: heurísticas por keyword (comportamento original intacto) ---
    intent_lower = intent.lower()

    if any(w in intent_lower for w in ["scale", "growth", "birth", "emergence", "starting"]):
        return "emergence"
    if any(w in intent_lower for w in ["chaos_to_order", "alignment", "harmony"]):
        return "chaos_to_order"
    if any(w in intent_lower for w in ["speed", "tension", "fragment", "complex", "chaos"]):
        return "fragmented_reveal"
    if any(w in intent_lower for w in ["attraction", "collapse", "singularity"]):
        return "gravitational_collapse"

    return random.choice(available) if available else "emergence"


def select_aesthetic_family(identity: str, intent: str = "") -> str:
    """
    Persona Aria: Escolha da linguagem estética.

    Tenta Claude Haiku via ai_brain primeiro; fallback para lógica original.
    """
    # --- AI Native Brain (LLM path) ---
    if _ai_brain is not None:
        llm_result = _ai_brain.call_aesthetic_llm(identity, intent)
        if llm_result:
            return llm_result

    # --- Fallback: lógica original intacta ---
    families = ["silent_architecture", "brutalist_signal", "organic_field", "data_narrative"]
    if identity == "aiox_default":
        return "silent_architecture"
    return random.choice(families)
