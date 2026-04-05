import numpy as np
from manim import Scene, FadeOut
from core.primitives.particle_system import ParticlePool
from core.primitives.theme_loader import theme, intelligence
from engines.manim.physics_mixin import PhysicsOrchestratorMixin

class EntropyDemo(Scene, PhysicsOrchestratorMixin):
    """
    Cena guiada 100% pela Inteligência Física da Zara (CDE).
    Não há hardcodes de física; o Motion Signature é injetado via `intelligence.entropy`.
    """
    def construct(self):
        runtime_seed = int(intelligence.get("seed", 42) or 42)
        np.random.seed(runtime_seed)
        physics_rng = np.random.default_rng(runtime_seed)

        # Fundo dinâmico da marca
        self.camera.background_color = theme.colors["background"]
        
        # 🧠 O NOVO PARADIGMA: Lendo interpretações, não apenas números
        interp = intelligence.get("interpretation", {})
        regime = interp.get("regime", "laminar")
        signature = interp.get("motion_signature", "breathing_field")
        stability = interp.get("stability", "high")
        
        # Ajusta parâmetros de setup do pool baseado na estabilidade ditada por Zara
        pt_radius = 0.04 if stability == "high" else 0.02
        emit_rate = 40 if stability == "high" else 150
        physical_entropy = float(intelligence.get("entropy", {}).get("physical", 0.5))

        self.setup_physics_environment(seed=runtime_seed)
        try:
            launch_angle = float(physics_rng.uniform(-np.pi / 6, np.pi / 6))
            launch_speed = float(np.interp(physical_entropy, [0.0, 1.0], [120.0, 420.0]))
            probe = self.create_probe_body(
                position=(-2.8, 0.0),
                velocity=(
                    np.cos(launch_angle) * launch_speed,
                    np.sin(launch_angle) * launch_speed,
                ),
                mass=float(np.interp(physical_entropy, [0.0, 1.0], [0.9, 1.4])),
                radius=0.18,
            )
            self.evaluate_physics_step(dt=1 / 60, steps=180)
            physics_state = self.capture_physics_state(probe, label="entropy_probe")
            physics_state["motion_signature"] = signature
            physics_state["stability"] = stability
            physics_state["physical_entropy"] = physical_entropy
            self.export_physics_state(physics_state)
        
            # A própria ParticlePool puxa o motion_signature no seu construtor
            pool = ParticlePool(
                max_particles=400,
                emit_rate=emit_rate,
                dot_radius=pt_radius,
                color=theme.accent_color,
                lifetime_range=(1.5, 4.0),
                seed=runtime_seed,
            )
            
            self.add(pool)
            
            # Revelação
            self.play(pool.animate_birth(run_time=2))
            
            # Tempo para admirar o Motion Signature da Zara
            self.wait(5)
            
            self.play(FadeOut(pool))
        finally:
            self.teardown_physics()
