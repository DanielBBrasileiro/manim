import random
import math

class CreativeVector:
    """O DNA do plano transformado em um vetor (Latent Space 5D)."""
    def __init__(self, tension=0.0, density=0.0, chaos=0.0, rhythm=0.0, stability=0.0):
        # Todos normalizados [0.0, 1.0]
        self.tension = tension
        self.density = density
        self.chaos = chaos
        self.rhythm = rhythm
        self.stability = stability

    def to_array(self):
        return [self.tension, self.density, self.chaos, self.rhythm, self.stability]

    @classmethod
    def from_array(cls, arr):
        return cls(*arr)

    def blend(self, other, factor=0.5):
        """Interpolação linear genética entre duas almas comportamentais."""
        arr1 = self.to_array()
        arr2 = other.to_array()
        new_arr = [(a * (1.0 - factor)) + (b * factor) for a, b in zip(arr1, arr2)]
        return self.from_array(new_arr)

    def distance_to(self, other):
        """Cosine/Euclidean Similarity (usado pela Persona UMA)"""
        arr1 = self.to_array()
        arr2 = other.to_array()
        return math.sqrt(sum((a - b)**2 for a, b in zip(arr1, arr2)))

    def to_entropy(self) -> dict:
        """Converte o vetor semântico obscuro de volta para a física do Manim."""
        # mapeamento simplificado
        return {
            "physical": self.chaos,
            "structural": 1.0 - self.tension, # Alta tensão = menos estrutura predefinida
            "aesthetic": self.density
        }

def map_intent_to_vector(intent_obj) -> CreativeVector:
    """Heurística Semântica -> Espaço Latente (Aria e Zara encapsulados)."""
    t = 0.8 if intent_obj.tension == "high" else 0.2 if intent_obj.tension == "low" else 0.5
    d = 0.8 if intent_obj.density == "high" else 0.2 if intent_obj.density == "low" else 0.5
    
    # Chaos e Stability derivados do Transformation
    c = 0.5
    s = 0.5
    trans = intent_obj.transformation
    if trans == "chaos_to_order":
        c, s = 0.8, 0.2  # Tende à ordem no final, mas o vetor base tem muito caos inicial
    elif trans == "order_to_chaos":
        c, s = 0.2, 0.8
    elif trans == "emergence":
        c, s = 0.3, 0.7
    elif trans == "gravitational_collapse":
        c, s = 0.6, 0.4
        
    r = 0.8 if intent_obj.pacing == "dynamic" else 0.3
    
    return CreativeVector(tension=t, density=d, chaos=c, rhythm=r, stability=s)

def get_signature_from_vector(vector: CreativeVector) -> str:
    """Engenharia Reversa: O vetor pousa no espaço latente em qual zona de motion?"""
    # Isso simula o KNN (K-Nearest Neighbors) offline.
    # Definição dos centróides (Assinaturas Clássicas Mapeadas no Espaço Latente)
    centroids = {
        "laminar_flow":         CreativeVector(0.1, 0.5, 0.1, 0.2, 0.9),
        "chaotic_burst":        CreativeVector(0.9, 0.8, 0.9, 0.9, 0.1),
        "oscillatory_wave":     CreativeVector(0.5, 0.5, 0.4, 0.7, 0.6),
        "vortex_pull":          CreativeVector(0.8, 0.9, 0.6, 0.4, 0.4),
        "breathing_field":      CreativeVector(0.2, 0.6, 0.2, 0.3, 0.8),
        "scattered_to_aligned": CreativeVector(0.6, 0.4, 0.7, 0.5, 0.3)
    }
    
    min_dist = float('inf')
    best_sig = "laminar_flow" # default
    
    for sig_name, centroid in centroids.items():
        dist = vector.distance_to(centroid)
        if dist < min_dist:
            min_dist = dist
            best_sig = sig_name
            
    return best_sig
