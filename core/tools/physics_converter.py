import math
from typing import Dict, Any

def convert_apple_to_framer_manim(
    damping: float, 
    stiffness: float, 
    mass: float = 1.0, 
    initial_velocity: float = 0.0
) -> Dict[str, Any]:
    """
    Apple Spring native formats:
    damping (c), stiffness (k), mass (m)
    
    Converts directly to Framer Motion parameters and extracts analytical 
    components (omega_n, zeta) for the Manim FluidSpringScene.
    """
    omega_n = math.sqrt(stiffness / mass)
    # damping ratio zeta = c / (2 * sqrt(k * m))
    zeta = damping / (2 * math.sqrt(stiffness * mass))
    
    # Calculate a rough settling time for visual duration estimation (envelope < 1%)
    if 0.0 < zeta < 1.0:
        settling_time = 4.6 / (zeta * omega_n)
    else:
        # Critically or overdamped
        real_pole = omega_n * (zeta - math.sqrt(max(0.0, zeta**2 - 1.0)))
        settling_time = 4.6 / real_pole if real_pole > 0 else 2.0

    return {
        "framer": {
            "stiffness": stiffness,
            "damping": damping,
            "mass": mass,
            "velocity": initial_velocity,
            "dampingRatio": zeta,
            "visualDuration": settling_time
        },
        "manim_analytical": {
            "omega_n": omega_n,
            "zeta": zeta,
            "v0": initial_velocity,
            "settling_time": settling_time
        }
    }
