import numpy as np
from manim import Scene, FadeOut
from core.primitives.particle_system import ParticlePool
from core.primitives.theme_loader import theme, intelligence

class EntropyDemo(Scene):
    """
    Cena guiada 100% pela Inteligência Física da Zara (CDE).
    Não há hardcodes de física; o Motion Signature é injetado via `intelligence.entropy`.
    """
    def construct(self):
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
        
        # A própria ParticlePool puxa o motion_signature no seu construtor
        pool = ParticlePool(
            max_particles=400,
            emit_rate=emit_rate,
            dot_radius=pt_radius,
            color=theme.accent_color,
            lifetime_range=(1.5, 4.0),
        )
        
        self.add(pool)
        
        # Revelação
        self.play(pool.animate_birth(run_time=2))
        
        # Tempo para admirar o Motion Signature da Zara
        self.wait(5)
        
        self.play(FadeOut(pool))
