def parse_intent(seed: dict) -> str:
    """Extrai uma string semântica descritiva a partir do YAML criativo."""
    if "creative_seed" in seed:
        s = seed["creative_seed"]
        return f"{s.get('transformation','')} {s.get('pacing','')} tension {s.get('tension','')}"
    # Formato legado fallback
    return seed.get("meta", {}).get("project", "") + " " + str(seed.get("scenes", []))
