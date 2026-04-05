import math
from typing import Callable

def make_fluid_spring_rate_func(
    stiffness: float,
    damping: float,
    mass: float = 1.0,
    initial_velocity: float = 0.0,
    duration: float = 1.0
) -> Callable[[float], float]:
    """
    Creates a Manim RateFunc (f(progress) -> progress) that perfectly simulates 
    a physical spring conforming to Framer Motion and Apple Fluid Interfaces standards.
    
    Arguments:
        stiffness (k): Spring tension
        damping (c): Resistance force
        mass (m): Weight of the element
        initial_velocity (v0): Inheritable momentum
        duration: The Manim `Animation.run_time` so progress (0 to 1) 
                  can be scaled back into physical seconds.
    """
    omega_n = math.sqrt(stiffness / mass)
    zeta = damping / (2 * math.sqrt(stiffness * mass))
    v0 = initial_velocity

    def evaluate(progress: float) -> float:
        # Physical time in seconds
        t = progress * duration
        
        # Underdamped
        if zeta < 1.0:
            omega_d = omega_n * math.sqrt(1 - zeta**2)
            A = -1.0
            B = (v0 - zeta * omega_n) / omega_d
            decay = math.exp(-zeta * omega_n * t)
            return 1.0 + decay * (A * math.cos(omega_d * t) + B * math.sin(omega_d * t))
            
        # Critically damped
        elif zeta == 1.0:
            A = -1.0
            B = v0 - omega_n
            decay = math.exp(-omega_n * t)
            return 1.0 + decay * (A + B * t)
            
        # Overdamped
        else:
            root = omega_n * math.sqrt(zeta**2 - 1.0)
            r1 = -zeta * omega_n + root
            r2 = -zeta * omega_n - root
            
            A = (v0 + r2) / (r1 - r2)
            B = -(v0 + r1) / (r1 - r2)
            
            return 1.0 + A * math.exp(r1 * t) + B * math.exp(r2 * t)

    return evaluate
