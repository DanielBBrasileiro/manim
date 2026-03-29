# core/creative/zara.py
class EntropyAgentZara:
    """
    Persona: Engenheira Física e de Caos (Zara)
    Objetivo: Transformar valores escalares de entropia em 'Motion Signatures' com personalidade.
    Em vez de dizer 'noise_strength = 0.8', ela dita 'regime = turbulent, flow = non-linear'.
    """
    
    @staticmethod
    def interpret(entropy_dict):
        phys = entropy_dict.get("physical", 0.5)
        struc = entropy_dict.get("structural", 0.5)
        aesth = entropy_dict.get("aesthetic", 0.5)
        
        # 1. Regime Físico e Assinatura de Movimento
        if phys < 0.25:
            regime = "laminar"
            rhythm = "breathing"
            flow = "linear"
            primary_signature = "breathing_field"
        elif phys < 0.60:
            regime = "transitional"
            rhythm = "pulsing"
            flow = "vortex"
            primary_signature = "vortex_pull"
        elif phys < 0.85:
            regime = "turbulent"
            rhythm = "irregular"
            flow = "non-linear"
            primary_signature = "chaotic_dispersion"
        else:
            regime = "chaotic"
            rhythm = "snapping"
            flow = "fractured"
            primary_signature = "elastic_snap"
            
        # 2. Estabilidade Estrutural
        if struc < 0.3:
            stability = "high"
            grid_type = "ordered"
        elif struc < 0.7:
            stability = "medium"
            grid_type = "adaptive"
        else:
            stability = "low"
            grid_type = "fragmented"

        return {
            "regime": regime,
            "rhythm": rhythm,
            "flow": flow,
            "stability": stability,
            "grid_type": grid_type,
            "primary_signature": primary_signature,
            "raw": entropy_dict
        }
