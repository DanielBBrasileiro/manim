from typing import Any, Dict

class WaveBackgroundGenerator:
    """
    Generates dynamic background interference patterns driven by the physical 
    'tension' parameter of the active creative briefing, theoretically interacting 
    with the `manim_physics.Waves` mechanics.
    """
    
    def __init__(self, tension_normalized: float):
        """
        Args:
            tension_normalized: Float [0.0, 1.0] indicating narrative stress.
        """
        self.tension = max(0.0, min(1.0, tension_normalized))
        
    def generate_wave_parameters(self) -> Dict[str, Any]:
        """
        Maps tension to mathematical wave parameters.
        High tension (> 0.8) generates high frequency, short wavelength ($\lambda$), 
        and multiple coherent point sources, mimicking computational data noise.
        """
        # Parameter envelopes
        lambda_bounds = (3.0, 0.5)      # Low tension -> High tension
        freq_bounds = (0.2, 5.0)        # Low tension -> High tension
        source_count_bounds = (1, 5)    # Low tension -> High tension
        
        # Non-linear scaling mapping (sharp contrast at high tension)
        t_scaled = self.tension ** 2
        
        computed_lambda = lambda_bounds[0] + (lambda_bounds[1] - lambda_bounds[0]) * t_scaled
        computed_freq = freq_bounds[0] + (freq_bounds[1] - freq_bounds[0]) * t_scaled
        computed_sources = int(round(
            source_count_bounds[0] + (source_count_bounds[1] - source_count_bounds[0]) * t_scaled
        ))
        
        return {
            "wavelength": computed_lambda,
            "frequency": computed_freq,
            "sources_count": computed_sources,
            "amplitude": 1.0 + t_scaled * 2.5
        }
