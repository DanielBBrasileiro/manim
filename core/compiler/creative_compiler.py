from .intent_parser import parse_intent
from .rule_engine import apply_rules
from .mutation_engine import mutate_entropy, mutate_motion
from .scoring_engine import novelty_score, coherence_score
from .signature_simulator import simulate_signature
from core.agents import zara, kael

import copy

def enrich_with_entropy(plan: dict) -> dict:
    """Invoca as personas físicas reais (Zara/Kael) com o arquétipo já escolhido pela Rule Engine."""
    archetype = plan.get("archetype", "emergence")
    
    # Define entropia numérica bruta via regra ZARA
    entropy_base = zara.define_entropy(archetype)
    plan["entropy"] = entropy_base
    
    # Interpreta Semântica (turbulento, etc)
    from core.intelligence.entropy_interpreter import interpret_entropy
    interpretation = interpret_entropy(entropy_base)
    
    # Force bias if exists
    bias = zara.resolve_motion_bias(archetype)
    if bias:
        interpretation["motion_signature"] = bias
        
    plan["interpretation"] = interpretation
    
    # ---------------------------------------------
    # FASE 1 (ELITE): A Linguagem Temporal (Timeline)
    # ---------------------------------------------
    timeline = []
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
             {"phase": [0.5, 1.0], "behavior": "breathing_field", "tension": "medium"}
        ]
        
    plan["timeline"] = timeline
    
    return plan

def negotiate(plan: dict) -> dict:
    """Fase 4 (Elite): Negociação Multi-Agente Darwiniana."""
    best_plan = copy.deepcopy(plan)
    max_score = 0.0
    
    for _ in range(5):
        # 1. Uma: A fiscal do Histórico Repetitivo
        uma_score = novelty_score(best_plan)
        
        # 2. Aria: A diretora de coerência semântica e estética
        aria_score = coherence_score(best_plan)
        
        # 3. Zara: A diretora de comportamento e caos
        # Zara recompensa planos que ousam na escala física (Entropia alta e Rhythm alto)
        fiz = best_plan.get("entropy", {}).get("physical", 0.0)
        stru = best_plan.get("entropy", {}).get("structural", 0.0)
        zara_score = (fiz + (1.0 - stru)) / 2.0
        
        # Somatório ponderado do conflito
        # A coerência (Aria) é o peso principal, mas a Novidade (Uma) é o veto final.
        total = (uma_score * 0.4) + (aria_score * 0.4) + (zara_score * 0.2)
        
        # Consenso Absoluto Encontrado
        if uma_score > 0.6 and aria_score > 0.8:
            return best_plan
            
        if total > max_score:
            max_score = total
            
        # Negação/Conflito: Votação para Mutação via Espaço Latente (Vetores)
        best_plan = mutate_entropy(best_plan)
        if uma_score < 0.4:
            # Uma exige mudança drástica no DNA vetorial
            best_plan = mutate_motion(best_plan)
            
    return best_plan

def compile_seed(seed: dict, identity: str = 'aiox_default'):
    """Ponto de Entrada Mestre do AIOX OS v5 (Autonomia Elite)."""
    
    intent = parse_intent(seed)
    plan = apply_rules(intent, identity)
    plan = enrich_with_entropy(plan)
    
    # 4. Negociação Darwiniana (Crítica Multi-Agente)
    plan = negotiate(plan)
    
    # 5. Simulador Final
    signature = simulate_signature(plan)
    
    return {
        "intent": str(intent),
        "creative_plan": plan,
        "output_signature": signature,
        "render_manifest": plan
    }
