import json

def compare_novelty(plan: dict, past_entry: dict) -> float:
    """Calcula a similaridade reversa. Retorna 1 se for 100% diferente, 0 se idêntico."""
    score = 0.0
    past_plan = past_entry.get("creative_plan", {})
    past_interp = past_plan.get("interpretation", {})
    
    # Similaridade Estrutural (Peso alto para arquétipo)
    if plan["archetype"] != past_plan.get("archetype"): score += 0.4
        
    # Similaridade Física
    if plan["interpretation"]["motion_signature"] != past_interp.get("motion_signature"): score += 0.4
        
    # Mutabilidade Fina
    diff_phys = abs(plan.get("entropy", {}).get("physical", 0.5) - past_plan.get("entropy", {}).get("physical", 0.5))
    score += min(0.2, diff_phys)
    
    return min(1.0, score)

def novelty_score(plan: dict, memory_path: str = "core/memory/creative_memory.json") -> float:
    try:
        with open(memory_path, 'r') as f:
            data = json.load(f)
            history = data.get("history", [])
            
            if not history:
                return 1.0 # Primeiro da história => 100% Original
                
            similarities = []
            # Verifica apenas os últimos 5 para velocidade e relevância
            for past in history[-5:]:
                similarities.append(1.0 - compare_novelty(plan, past))
                
            return 1.0 - max(similarities)
            
    except FileNotFoundError:
        return 1.0

def coherence_score(plan: dict) -> float:
    """
    Motor Lógico: Aplica Leis do Design Limite. Se a Engine estiver propondo algo 
    esteticamente inválido ou fisicamente inviável, corta aqui.
    """
    archetype = plan.get("archetype")
    phys_ent = plan.get("entropy", {}).get("physical", 0.0)
    
    if archetype == "emergence" and phys_ent > 0.7:
        # Nascer de forma turbulenta e violenta é paradoxo inaceitável para AIOX
        return 0.3
        
    if archetype == "loop_stability" and phys_ent > 0.4:
        # Loops devem ser imutáveis e constantes, entropia precisa estar super baixa
        return 0.2
        
    if archetype == "chaos_to_order" and plan.get("pacing") == "dynamic":
        # Ordenação veloz demais soa como explosão em reverso (glitchy). Coerência mediada.
        return 0.6
        
    return 0.9

def evaluate_plan(plan: dict) -> dict:
    """Devolve a Matriz de Sanidade para o Loop."""
    return {
        "novelty": novelty_score(plan),
        "coherence": coherence_score(plan)
    }
