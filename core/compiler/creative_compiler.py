from .intent_parser import parse_intent
from .plan_generator import generate_plan
from .signature_simulator import simulate_signature
from core.agents import uma

def compile_seed(seed: dict, identity: str = 'aiox_default'):
    intent = parse_intent(seed)
    
    plan = generate_plan(intent, identity)
    
    # Mutação (Validação)
    signature = simulate_signature(plan)
    if not uma.evaluate(signature):
        plan = generate_plan(intent + ' alternate', identity)
        signature = simulate_signature(plan)
        
    return {
        "intent": intent,
        "creative_plan": plan,
        "output_signature": signature,
        "render_manifest": plan
    }
