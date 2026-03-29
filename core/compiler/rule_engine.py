from typing import Callable, Dict
from core.compiler.intent_parser import Intent
import random

class Rule:
    def __init__(self, condition: Callable[[Intent], bool], action: Callable[[Dict], None]):
        self.condition = condition
        self.action = action

def apply_rules(intent: Intent, identity: str = "aiox_default") -> dict:
    """O Cérebro Racional Offline. Compila o plano-base a partir das Regras."""
    plan = {
        "archetype": "emergence",  # fallback master
        "aesthetic_family": "silent_architecture",
        "pacing": "cinematic"
    }
    
    # === RULES DSL ===
    RULES = [
        # Transformation -> Archetype Mapping
        Rule(
            condition=lambda i: i.transformation == "chaos_to_order",
            action=lambda p: p.update({"archetype": "chaos_to_order"})
        ),
        Rule(
            condition=lambda i: i.transformation == "order_to_chaos",
            action=lambda p: p.update({"archetype": "order_to_chaos"})
        ),
        Rule(
            condition=lambda i: i.transformation == "gravitational_collapse",
            action=lambda p: p.update({"archetype": "gravitational_collapse"})
        ),
        
        # Tension Exceptions -> Force Archetypes
        Rule(
            condition=lambda i: i.tension == "high" and i.density == "high",
            action=lambda p: p.update({"archetype": "fragmented_reveal"})
        ),
        Rule(
            condition=lambda i: i.tension == "low" and i.density == "low",
            action=lambda p: p.update({"archetype": "loop_stability"})
        ),
        
        # Pacing Rules
        Rule(
            condition=lambda i: i.pacing == "dynamic",
            action=lambda p: p.update({"pacing": "dynamic"})
        ),
        
        # Aesthetic Theme Rules (Simulação do Design_System)
        Rule(
            condition=lambda i: i.tone == "light",
            action=lambda p: p.update({"aesthetic_family": "corporate_lucid"})
        ),
        Rule(
            condition=lambda i: i.tone == "dark" and identity == "aiox_default",
            action=lambda p: p.update({"aesthetic_family": "silent_architecture"})
        )
    ]
    
    # Motor de Execução Linear das Leis
    for rule in RULES:
        if rule.condition(intent):
            rule.action(plan)
            
    return plan
