from manim import FadeOut, Scene

from core.primitives.particle_system import ParticlePool
from core.primitives.theme_loader import intelligence, theme
from engines.manim.physics_mixin import (
    evaluate_physics,
    setup_physics,
    teardown_physics,
    write_physics_state,
)


class EntropyDemo(Scene):
    """
    Cena guiada 100% pela Inteligência Física da Zara (CDE).
    Não há hardcodes de física; o Motion Signature é injetado via `intelligence.entropy`.

    Physics lifecycle (PR-10):
      1. setup_physics()     — creates seeded pymunk Space
      2. evaluate_physics()  — steps simulation, extracts PhysicsState
      3. teardown_physics()  — explicit cleanup (always runs via finally)
      4. write_physics_state() — writes TS constant for Remotion to import
    """

    def construct(self) -> None:
        self.camera.background_color = theme.colors["background"]

        interp = intelligence.get("interpretation", {})
        stability = interp.get("stability", "high")
        regime = interp.get("regime", "laminar")

        entropy = intelligence.get("entropy", {"physical": 0.5, "structural": 0.5, "aesthetic": 0.5})
        render_seed = intelligence.get("seed") or 42

        # ── Physics lifecycle ──────────────────────────────────────────────
        space = setup_physics(seed=render_seed, entropy=entropy, regime=regime)
        try:
            phys_state = evaluate_physics(space, steps=60, dt=1.0 / 60.0, seed=render_seed)
        finally:
            teardown_physics(space)

        # Persist physics state for Remotion (written to generated/physics_state.ts)
        write_physics_state(phys_state)

        # ── Particle setup — kinetic energy modulates particle entropy ─────
        pt_radius = 0.04 if stability == "high" else 0.02
        emit_rate = 40 if stability == "high" else 150

        # Use normalised kinetic energy from real physics to calibrate particle entropy
        particle_entropy = float(entropy.get("physical", 0.5)) * (0.7 + phys_state["kinetic_energy"] * 0.6)

        pool = ParticlePool(
            max_particles=400,
            emit_rate=emit_rate,
            dot_radius=pt_radius,
            color=theme.accent_color,
            lifetime_range=(1.5, 4.0),
            entropy=particle_entropy,
            seed=render_seed,
        )

        self.add(pool)
        self.play(pool.animate_birth(run_time=2))
        self.wait(5)
        self.play(FadeOut(pool))
