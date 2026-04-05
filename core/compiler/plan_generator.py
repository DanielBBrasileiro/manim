from core.agents import aria, zara, kael
from core.intelligence.entropy_interpreter import interpret_entropy

STYLE_PACKS = {
    "silent_luxury": {
        "motion_grammar": "cinematic_restrained",
        "typography_system": "editorial_minimal",
        "still_family": "poster_minimal",
        "color_mode": "monochrome_pure",
        "negative_space_target": 0.65,
        "accent_intensity": 0.1,
        "grain": 0.04,
    },
    "kinetic_editorial": {
        "motion_grammar": "kinetic_editorial",
        "typography_system": "editorial_dense",
        "still_family": "editorial_portrait",
        "color_mode": "monochrome_warm",
        "negative_space_target": 0.40,
        "accent_intensity": 0.5,
        "grain": 0.08,
    },
}


def _select_style_pack(intent: str, archetype: str, explicit_style_pack: str | None = None) -> str:
    requested = str(explicit_style_pack or "").strip()
    if requested in STYLE_PACKS:
        return requested

    normalized_intent = str(intent or "").lower()
    if any(
        token in normalized_intent
        for token in ["editorial", "kinetic", "dynamic", "fast", "energetic", "urgent"]
    ):
        return "kinetic_editorial"

    if archetype in {"order_to_chaos", "fragmented_reveal"}:
        return "kinetic_editorial"

    return "silent_luxury"


def _style_pack_contract(style_pack: str) -> dict:
    return dict(STYLE_PACKS.get(style_pack, STYLE_PACKS["silent_luxury"]))


def _timeline_for(archetype: str, bias: str | None, motion_grammar: str, pacing: dict) -> list[dict]:
    transition = str(pacing.get('transitions', {}).get('act_to_act', 'cut') or 'cut')
    rhythm = str(pacing.get('rhythm', 'uniform') or 'uniform')
    stagger = list(pacing.get('stagger_profile', [])) if isinstance(pacing.get('stagger_profile', []), list) else []

    if archetype == "emergence":
        timeline = [
             {"phase": [0.0, 0.4], "behavior": "coherent_flow", "tension": "low"},
             {"phase": [0.4, 0.8], "behavior": bias or "scattered_to_aligned", "tension": "medium"},
             {"phase": [0.8, 1.0], "behavior": "convergence_field", "tension": "high"}
        ]
    elif archetype == "chaos_to_order":
        timeline = [
             {"phase": [0.0, 0.3], "behavior": "chaotic_burst", "tension": "high"},
             {"phase": [0.3, 0.7], "behavior": bias or "vortex_pull", "tension": "medium"},
             {"phase": [0.7, 1.0], "behavior": "laminar_flow", "tension": "low"}
        ]
    elif archetype == "order_to_chaos":
        timeline = [
             {"phase": [0.0, 0.4], "behavior": "laminar_flow", "tension": "low"},
             {"phase": [0.4, 0.7], "behavior": bias or "oscillatory_wave", "tension": "medium"},
             {"phase": [0.7, 1.0], "behavior": "chaotic_dispersion", "tension": "high"}
        ]
    else:
        timeline = [
             {"phase": [0.0, 0.5], "behavior": bias or "laminar_flow", "tension": "medium"},
             {"phase": [0.5, 1.0], "behavior": bias or "breathing_field", "tension": "medium"}
        ]

    for index, block in enumerate(timeline):
        block["motion_grammar"] = motion_grammar
        block["rhythm"] = rhythm
        block["transition_to"] = transition if index < len(timeline) - 1 else "cut"
        block["stagger_profile"] = stagger
    return timeline


def generate_plan(intent: str, identity: str = 'aiox_default', style_pack: str | None = None) -> dict:
    """
    Compiler Phase 2: A espinha neural criativa (antigo CDE)
    """
    archetype = aria.decide_archetype(intent)
    aesthetic = aria.select_aesthetic_family(identity)
    entropy_base = zara.define_entropy(archetype)
    
    # Semantic interpretation by Zara v2
    interpretation = interpret_entropy(entropy_base)
    
    # Motion bias extraction
    bias = zara.resolve_motion_bias(archetype)
    if bias: 
        interpretation['motion_signature'] = bias
    selected_style_pack = _select_style_pack(intent, archetype, explicit_style_pack=style_pack)
    style_pack_contract = _style_pack_contract(selected_style_pack)
    pacing = kael.define_pacing(
        intent,
        archetype,
        motion_grammar=style_pack_contract.get("motion_grammar"),
    )
    motion_grammar = str(pacing.get('motion_grammar', 'cinematic_restrained') or 'cinematic_restrained')
        
    timeline = _timeline_for(archetype, bias, motion_grammar, pacing)
    
    return {
        'archetype': archetype,
        'aesthetic_family': aesthetic,
        'entropy': entropy_base,
        'interpretation': interpretation,
        'style_pack': selected_style_pack,
        'style_pack_ids': [selected_style_pack],
        'style_pack_contract': style_pack_contract,
        'motion_grammar': motion_grammar,
        'pacing': pacing,
        'motion_sequences': pacing.get('motion_sequences', []),
        'timeline': timeline
    }
