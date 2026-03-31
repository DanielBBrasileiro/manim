from .intent_parser import parse_intent
from .render_manifest import build_render_manifest
from .rule_engine import apply_rules
from .mutation_engine import mutate_entropy, mutate_motion
from .scoring_engine import novelty_score, coherence_score
from .signature_simulator import simulate_signature
from core.agents import zara
from core.intelligence.model_router import TASK_PLAN

import copy

BEHAVIOR_BY_PRIMITIVE = {
    "living_curve": "coherent_flow",
    "particle_system": "chaotic_burst",
    "physics_field": "vortex_pull",
    "fbm_noise": "oscillatory_wave",
    "neural_grid": "laminar_flow",
    "narrative_container": "convergence_field",
    "storage_hex": "convergence_field",
}

TENSION_BY_EFFECT = {
    "grain_overlay": "medium",
    "motion_blur": "medium",
    "color_inversion": "high",
    "post_glitch_light": "high",
    "diagonal_accent": "medium",
}


def apply_scene_plan_guidance(plan: dict, scene_plan: dict) -> dict:
    guided = copy.deepcopy(plan)
    guided["duration"] = scene_plan.get("duration", guided.get("duration", 12))
    guided["assets"] = scene_plan.get("assets", {})
    guided["effects"] = scene_plan.get("effects", [])

    scenes = scene_plan.get("scenes", [])
    if not isinstance(scenes, list) or not scenes:
        return guided

    total_duration = sum(float(scene.get("duration", 0) or 0) for scene in scenes) or 1.0
    cursor = 0.0
    timeline = []

    for scene in scenes:
        scene_duration = float(scene.get("duration", 0) or 0)
        phase_start = cursor / total_duration
        cursor += scene_duration
        phase_end = min(1.0, cursor / total_duration)

        primitives = scene.get("primitives", []) if isinstance(scene.get("primitives"), list) else []
        effects = guided["effects"]
        behavior = _behavior_from_scene(primitives)
        tension = _tension_from_scene(primitives, effects)

        timeline.append(
            {
                "phase": [round(phase_start, 3), round(phase_end, 3)],
                "behavior": behavior,
                "tension": tension,
            }
        )

    if timeline:
        timeline[-1]["phase"][1] = 1.0
        guided["timeline"] = timeline

    return guided


def _behavior_from_scene(primitives: list) -> str:
    for primitive in primitives:
        behavior = BEHAVIOR_BY_PRIMITIVE.get(str(primitive).lower())
        if behavior:
            return behavior
    return "coherent_flow"


def _tension_from_scene(primitives: list, effects: list) -> str:
    for effect in effects:
        tension = TENSION_BY_EFFECT.get(str(effect).lower())
        if tension == "high":
            return tension

    primitive_set = {str(item).lower() for item in primitives}
    if {"particle_system", "fbm_noise"} & primitive_set:
        return "high"
    if {"living_curve", "neural_grid"} & primitive_set:
        return "low"
    return "medium"


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
    if float(plan.get("llm_confidence", 0.0)) >= 0.85:
        return copy.deepcopy(plan)

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

def compile_seed(
    seed: dict,
    identity: str = 'aiox_default',
    asset_registry: dict | None = None,
    task_type: str = TASK_PLAN,
):
    """Ponto de Entrada Mestre do AIOX OS v5 (Autonomia Elite)."""

    intent = parse_intent(seed, asset_registry=asset_registry, task_type=task_type)
    plan = apply_rules(intent, identity)
    plan = enrich_with_entropy(plan)

    if getattr(intent, "scene_plan", None):
        plan["llm_scene_plan"] = intent.scene_plan
        plan["llm_confidence"] = getattr(intent, "confidence", 0.0)
        plan["llm_metadata"] = getattr(intent, "llm_metadata", {})
        plan = apply_scene_plan_guidance(plan, intent.scene_plan)
    
    # 4. Negociação Darwiniana (Crítica Multi-Agente)
    plan = negotiate(plan)
    render_manifest = build_render_manifest(plan, seed)
    plan["render_manifest"] = render_manifest
    
    # 5. Simulador Final
    signature = simulate_signature(plan)
    
    return {
        "intent": str(intent),
        "creative_plan": plan,
        "output_signature": signature,
        "render_manifest": render_manifest
    }
