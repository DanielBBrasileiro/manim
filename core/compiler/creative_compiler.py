from __future__ import annotations

import copy
import hashlib
import json
import random as _random_module

from .intent_parser import parse_intent
from .rule_engine import apply_rules
from .mutation_engine import mutate_entropy, mutate_motion
from .scoring_engine import novelty_score, coherence_score
from .signature_simulator import simulate_signature
from core.agents import zara, kael


def _rng_from_seed(seed: dict) -> _random_module.Random:
    """Derive a deterministic :class:`random.Random` instance from *seed*.

    Serialises the seed dict to canonical JSON (sorted keys) and hashes it
    with SHA-256 so the same briefing always produces the same RNG state.
    """
    key = json.dumps(seed, sort_keys=True, default=str)
    seed_int = int(hashlib.sha256(key.encode()).hexdigest()[:16], 16) & 0x7FFFFFFFFFFFFFFF
    return _random_module.Random(seed_int)

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

def negotiate(plan: dict, rng: _random_module.Random | None = None) -> dict:
    """Fase 4 (Elite): Negociação Multi-Agente Darwiniana.

    *rng* is a seeded :class:`random.Random` threaded from :func:`compile_seed`
    so that mutation outcomes are deterministic for a given briefing seed.
    """
    best_plan = copy.deepcopy(plan)
    max_score = 0.0

    for _ in range(5):
        # 1. Uma: A fiscal do Histórico Repetitivo
        uma_score = novelty_score(best_plan)

        # 2. Aria: A diretora de coerência semântica e estética
        aria_score = coherence_score(best_plan)

        # 3. Zara: A diretora de comportamento e caos
        fiz = best_plan.get("entropy", {}).get("physical", 0.0)
        stru = best_plan.get("entropy", {}).get("structural", 0.0)
        zara_score = (fiz + (1.0 - stru)) / 2.0

        total = (uma_score * 0.4) + (aria_score * 0.4) + (zara_score * 0.2)

        if uma_score > 0.6 and aria_score > 0.8:
            return best_plan

        if total > max_score:
            max_score = total

        # Negação/Conflito: Mutação via Espaço Latente com RNG determinístico
        best_plan = mutate_entropy(best_plan, rng)
        if uma_score < 0.4:
            best_plan = mutate_motion(best_plan, rng)

    return best_plan

def compile_seed(seed: dict, identity: str = "aiox_default") -> dict:
    """Ponto de Entrada Mestre do AIOX OS v5 (Autonomia Elite).

    Derives a deterministic RNG from *seed* so that every mutation in the
    Darwinian negotiation loop produces the same result for the same briefing.
    The derived integer seed is returned in the manifest for traceability.
    """
    rng = _rng_from_seed(seed)
    rng_seed_int = int(
        hashlib.sha256(json.dumps(seed, sort_keys=True, default=str).encode())
        .hexdigest()[:16],
        16,
    ) & 0x7FFFFFFFFFFFFFFF

    intent = parse_intent(seed)
    plan = apply_rules(intent, identity)
    plan = enrich_with_entropy(plan)

    # 4. Negociação Darwiniana (Crítica Multi-Agente) — seed determinístico
    plan = negotiate(plan, rng)

    # 5. Simulador Final
    signature = simulate_signature(plan)

    return {
        "intent": str(intent),
        "creative_plan": plan,
        "output_signature": signature,
        "render_manifest": plan,
        "rng_seed": rng_seed_int,
    }
