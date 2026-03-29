import random

from core.compiler.latent_space import map_intent_to_vector, get_signature_from_vector, CreativeVector

def mutate_entropy(plan: dict) -> dict:
    """Mutação via Espaço Latente (Vetores 5D)."""
    # 1. Recupera o vetor latente atual a partir do plano
    # Extraímos a intenção original
    current_sig = plan["interpretation"]["motion_signature"]
    
    # 2. Vamos criar um vetor mutante sutil (Espaço Latente de Perturbação)
    perturbation = CreativeVector(
        tension=random.uniform(0.0, 1.0),
        density=random.uniform(0.0, 1.0),
        chaos=random.uniform(0.0, 1.0),
        rhythm=random.uniform(0.0, 1.0),
        stability=random.uniform(0.0, 1.0)
    )
    
    # Simula a extração do vetor atual pelo signature dele (Reverso)
    # Como não temos o vetor exato salvo no plan, recriamos um Base
    # Para fins de simulação rápida:
    base_v = CreativeVector(0.5, 0.5, 0.5, 0.5, 0.5)
    
    # 3. Faz o Blend (Interpolação Genética 90% Ancestral, 10% Mutante)
    new_v = base_v.blend(perturbation, factor=0.15)
    
    # Atualiza as entropias numéricas cruas para o Manim
    plan["entropy"] = new_v.to_entropy()
    return plan

def mutate_motion(plan: dict) -> dict:
    """Mutação Direcional: Se falhar na aprovação, pula para um quadrante vizinho do Latent Space."""
    
    perturbation = CreativeVector(
        tension=random.uniform(0.0, 1.0),
        density=random.uniform(0.0, 1.0),
        chaos=random.uniform(0.0, 1.0),
        rhythm=random.uniform(0.0, 1.0),
        stability=random.uniform(0.0, 1.0)
    )
    
    # Aplica um Blend violento (60% Mutante) para tentar quebrar a barreira da Repetição
    base_v = CreativeVector(0.5, 0.5, 0.5, 0.5, 0.5)
    new_v = base_v.blend(perturbation, factor=0.6)
    
    # Encontra a nova Assinatura usando engenharia reversa no Latent Space
    new_sig = get_signature_from_vector(new_v)
    plan["interpretation"]["motion_signature"] = new_sig
    
    return plan

def mutate(plan: dict) -> dict:
    """Orquestrador de Mutação Genética."""
    import copy
    mutated = copy.deepcopy(plan)
    mutated = mutate_entropy(mutated)
    
    if random.random() > 0.5:
        mutated = mutate_motion(mutated)
        
    return mutated
