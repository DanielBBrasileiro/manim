from core.agents import aria, zara, kael
from core.intelligence.entropy_interpreter import interpret_entropy

def generate_plan(intent: str, identity: str = 'aiox_default') -> dict:
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
        
    pacing = kael.define_pacing(intent, archetype)
    
    return {
        'archetype': archetype,
        'aesthetic_family': aesthetic,
        'entropy': entropy_base,
        'interpretation': interpretation,
        'pacing': pacing
    }
