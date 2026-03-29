import random
import os
import yaml
from pathlib import Path

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
    """
    archetypes = _load_archetypes()
    available = list(archetypes.keys())
    
    intent_lower = intent.lower()
    
    # Heurística temporal (será substituída por LLM API)
    if any(w in intent_lower for w in ["scale", "growth", "birth", "emergence", "starting"]):
        return "emergence"
    if any(w in intent_lower for w in ["chaos_to_order", "alignment", "harmony"]):
        return "chaos_to_order"
    if any(w in intent_lower for w in ["speed", "tension", "fragment", "complex", "chaos"]):
        return "fragmented_reveal"
    if any(w in intent_lower for w in ["attraction", "collapse", "singularity"]):
        return "gravitational_collapse"
    
    return random.choice(available) if available else "emergence"

def select_aesthetic_family(identity: str) -> str:
    """
    Persona Aria: Escolha da linguagem estética.
    """
    families = ["silent_architecture", "brutalist_signal", "organic_field", "data_narrative"]
    if identity == "aiox_default":
        return "silent_architecture"
    return random.choice(families)
