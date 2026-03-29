from core.agents.aria import _load_archetypes

def define_entropy(archetype_name: str, base_entropy=0.5) -> dict:
    """
    Persona Zara: Engenharia Física e Comportamental.
    Define as escalas brutas de entropia que alimentarão o Interpreter.
    """
    archetypes = _load_archetypes()
    archetype = archetypes.get(archetype_name, {})
    profile = archetype.get("entropy_profile", "medium")
    
    # Mapeamento do perfil string para mix escalar bruto
    if profile == "low_to_medium":
        return {"physical": 0.3, "structural": 0.2, "aesthetic": 0.4}
    elif profile == "high_to_low":
        return {"physical": 0.8, "structural": 0.6, "aesthetic": 0.7}
    elif profile == "low_to_high":
        return {"physical": 0.4, "structural": 0.3, "aesthetic": 0.5}
    elif profile == "high_structural":
        return {"physical": 0.6, "structural": 0.9, "aesthetic": 0.6}
    elif profile == "rhythmic":
        return {"physical": 0.5, "structural": 0.5, "aesthetic": 0.5}
    
    return {"structural": base_entropy, "aesthetic": base_entropy, "physical": base_entropy}

def resolve_motion_bias(archetype_name: str) -> str:
    """Extrai a assinatura primária forçada pelo arquétipo (se houver)."""
    archetypes = _load_archetypes()
    arch_data = archetypes.get(archetype_name, {})
    return arch_data.get("motion_bias")
