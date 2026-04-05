import math
from typing import Any, List, Tuple

class PhysicsOrchestratorMixin:
    """
    Mixin to convert a Manim Scene/SpaceScene into a deterministic Convergence Engine
    using Pymunk/manim-physics. Supports Adaptive sub-stepping and Universal Gravitation.
    
    Can be used by appending to the class definition:
    `class ChaosToOrderScene(SpaceScene, PhysicsOrchestratorMixin):`
    """
    
    def setup_physics_environment(self, step_size: float = 1/60.0, sub_steps: int = 10) -> None:
        """
        Configures the Space's chronological bounds to avoid high-velocity tunneling constraints
        on M-series chips.
        """
        if not hasattr(self, "space"):
            self._physics_active = False
            return
            
        self._physics_dt = step_size
        self._sub_steps = sub_steps
        self._physics_active = True
        
    def add_universal_convergence_field(
        self, 
        atoms: List[Any], 
        singularity_pos: Tuple[float, float], 
        G: float = 1000.0, 
        singularity_mass: float = 100.0
    ) -> None:
        """
        Infers an Inverse-Square Law gravitation field pulling scattered atoms 
        towards the brand singularity.
        
        Formula: F = G * (m1 * m2) / r^2
        """
        if not getattr(self, "_physics_active", False):
            return
            
        def _apply_gravity(mob: Any, dt: float) -> None:
            if not hasattr(mob, "body") or mob.body is None:
                return
                
            atom_mass = mob.body.mass
            rx = singularity_pos[0] - mob.body.position.x
            ry = singularity_pos[1] - mob.body.position.y
            
            r_sq = rx**2 + ry**2
            if r_sq < 0.1:  # Core softening to prevent infinite acceleration tunneling
                r_sq = 0.1
                
            # Newton's Law of Universal Gravitation
            force_mag = G * (atom_mass * singularity_mass) / r_sq
            
            r_dist = math.sqrt(r_sq)
            fx = force_mag * (rx / r_dist)
            fy = force_mag * (ry / r_dist)
            
            mob.body.apply_force_at_local_point((fx, fy), (0, 0))

        for atom in atoms:
            atom.add_updater(_apply_gravity)

    def evaluate_physics_step(self) -> None:
        """
        Alternative to default updaters. Allows for explicit decoupled integration.
        Sub-steps Pymunk logic `self._sub_steps` times per `_physics_dt`.
        """
        if getattr(self, "_physics_active", False) and hasattr(self, "space"):
            sub_dt = self._physics_dt / float(self._sub_steps)
            for _ in range(self._sub_steps):
                self.space.step(sub_dt)
                
    def teardown_physics(self) -> None:
        """
        Scorched earth cleanup policy for physical bodies to prevent memory leaks 
        during heavy multi-briefing compilation queues.
        """
        if getattr(self, "_physics_active", False) and hasattr(self, "space"):
            if self.space.bodies:
                self.space.remove(*self.space.bodies)
            if self.space.shapes:
                self.space.remove(*self.space.shapes)
            if self.space.constraints:
                self.space.remove(*self.space.constraints)
            self._physics_active = False
