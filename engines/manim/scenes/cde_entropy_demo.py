import numpy as np
from manim import (
    AnimationGroup,
    Create,
    FadeIn,
    FadeOut,
    LaggedStart,
    RIGHT,
    LEFT,
    ORIGIN,
    Scene,
    DOWN,
    UP,
    Transform,
    VGroup,
    smooth,
)
from core.primitives.particle_system import ParticlePool
from core.primitives.containers import NarrativeContainer
from core.primitives.curves import LivingCurve
from core.primitives.geometry import NeuralGrid
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
        stability = interp.get("stability", "high")
        signature = interp.get("motion_signature", "breathing_field")
        
        # Ajusta parâmetros de setup do pool baseado na estabilidade ditada por Zara
        pt_radius = 0.036 if stability == "high" else 0.026
        emit_rate = 24 if stability == "high" else 40
        foreground = theme.colors.get("foreground", theme.accent_color)
        stroke = theme.colors.get("stroke", foreground)
        
        # A própria ParticlePool puxa a inteligência base, mas a cena troca perfis por ato.
        pool = ParticlePool(
            max_particles=480,
            emit_rate=emit_rate,
            dot_radius=pt_radius,
            color=theme.accent_color,
            emitter_spread=0.14,
            bounds=(-6.2, 6.2, -3.6, 3.6),
            lifetime_range=(2.2, 4.6),
        )
        pool.set_act_profile("genesis", signature=signature if signature != "chaotic_burst" else "breathing_field")

        frame = NarrativeContainer(width=4.6, height=5.8)
        frame.rect.set_stroke(color=stroke, width=1.1, opacity=0.45)
        frame.rect.scale(0.92)

        curve = LivingCurve(
            resolution=260,
            growth_progress=0.16,
            noise_amplitude=0.015,
            entropy=0.35,
            stroke_color=theme.accent_color,
            stroke_width=3.6,
        ).scale(0.86).shift(DOWN * 0.15)

        fracture_frames = VGroup(*frame.split_horizontal(gap=0.8))
        fracture_frames.set_stroke(color=theme.accent_color, width=1.6, opacity=0.55)
        fracture_frames.move_to(ORIGIN)

        turbulence_curve = curve.grow_to(1.0, noise=0.32)
        turbulence_curve.set_stroke(color=theme.accent_color, width=4.8, opacity=0.95)
        turbulence_curve.scale(1.08).shift(UP * 0.08)

        resolve_curve = curve.grow_to(1.0, noise=0.045)
        resolve_curve.set_stroke(color=foreground, width=3.2, opacity=0.95)
        resolve_curve.scale(1.1).shift(UP * 0.18)

        grid = NeuralGrid(rows=6, cols=6, spacing=0.78)
        grid.scale(0.92)
        grid.set_opacity(0.0)

        self.add(pool)
        
        # Ato 1 — Genesis: um único organismo nasce com contenção e silêncio visual.
        self.play(
            LaggedStart(
                Create(frame.rect),
                pool.animate_birth(run_time=2.4),
                Create(curve),
                lag_ratio=0.18,
            ),
            run_time=2.8,
        )
        self.wait(0.4)
        self.play(
            Transform(curve, curve.grow_to(0.52, noise=0.035).scale(0.92).shift(DOWN * 0.08)),
            run_time=1.2,
            rate_func=smooth,
        )
        self.wait(0.4)

        # Ato 2 — Turbulence: a moldura fratura, a curva distorce e o campo explode.
        pool.set_act_profile(
            "turbulence",
            signature="chaotic_burst",
            color=theme.accent_color,
            bounds=(-6.8, 6.8, -3.8, 3.8),
        )
        self.play(
            AnimationGroup(
                FadeOut(frame.rect, shift=DOWN * 0.12),
                FadeIn(fracture_frames, shift=UP * 0.12),
                Transform(curve, turbulence_curve),
                lag_ratio=0.12,
            ),
            run_time=1.5,
            rate_func=smooth,
        )
        self.play(
            fracture_frames[0].animate.shift(LEFT * 1.25 + UP * 0.18).rotate(-10 * np.pi / 180),
            fracture_frames[1].animate.shift(RIGHT * 1.25 + DOWN * 0.18).rotate(10 * np.pi / 180),
            curve.animate.shift(UP * 0.14).scale(1.02),
            run_time=2.0,
            rate_func=smooth,
        )
        self.wait(1.5)

        # Ato 3 — Resolution: o caos converge para estrutura e a curva se disciplina.
        pool.set_act_profile(
            "resolution",
            signature="convergence_field",
            color=foreground,
            bounds=(-5.6, 5.6, -3.3, 3.3),
        )
        self.play(
            AnimationGroup(
                FadeOut(fracture_frames, scale=0.96),
                FadeIn(grid, shift=UP * 0.15),
                Transform(curve, resolve_curve),
                lag_ratio=0.1,
            ),
            run_time=1.8,
            rate_func=smooth,
        )
        self.play(
            grid.animate.set_opacity(0.55).scale(1.03),
            curve.animate.shift(UP * 0.08),
            run_time=1.4,
            rate_func=smooth,
        )
        self.wait(1.6)

        self.play(FadeOut(VGroup(pool, curve, grid)), run_time=1.2)
