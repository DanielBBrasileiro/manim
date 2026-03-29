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
        
    # Fase 1: A Nova Linguagem Temporal (DSL)
    # Aqui entra o bloco cronológico ao invés de 'status estático'
    timeline = []
    
    if archetype == "emergence":
        timeline = [
             {"phase": "0.0 -> 0.4", "behavior": "coherent_flow", "tension": "low"},
             {"phase": "0.4 -> 0.8", "behavior": bias or "scattered_to_aligned", "tension": "medium"},
             {"phase": "0.8 -> 1.0", "behavior": "convergence_field", "tension": "high"}
        ]
    elif archetype == "chaos_to_order":
        timeline = [
             {"phase": "0.0 -> 0.3", "behavior": "chaotic_burst", "tension": "high"},
             {"phase": "0.3 -> 0.7", "behavior": bias or "vortex_pull", "tension": "medium"},
             {"phase": "0.7 -> 1.0", "behavior": "laminar_flow", "tension": "low"}
        ]
    elif archetype == "order_to_chaos":
        timeline = [
             {"phase": "0.0 -> 0.4", "behavior": "laminar_flow", "tension": "low"},
             {"phase": "0.4 -> 0.7", "behavior": bias or "oscillatory_wave", "tension": "medium"},
             {"phase": "0.7 -> 1.0", "behavior": "chaotic_dispersion", "tension": "high"}
        ]
    else:
        # Fallback Master
        timeline = [
             {"phase": "0.0 -> 0.5", "behavior": bias or "laminar_flow", "tension": "medium"},
             {"phase": "0.5 -> 1.0", "behavior": bias or "breathing_field", "tension": "medium"}
        ]
    
    return {
        'archetype': archetype,
        'aesthetic_family': aesthetic,
        'entropy': entropy_base,
        'interpretation': interpretation,
        'pacing': pacing,
        'timeline': timeline
    }
