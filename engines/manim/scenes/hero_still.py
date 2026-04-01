import numpy as np
from manim import *
from core.primitives.particle_system import ParticlePool
from core.primitives.containers import NarrativeContainer
from core.primitives.curves import LivingCurve
from core.primitives.geometry import NeuralGrid
from core.primitives.theme_loader import theme, intelligence

class HeroStillGeometry(Scene):
    """
    Cenas desenhadas puramente para composição de "Hero Stills" geométricos,
    como o linkedin_feed_4_5. Em vez de uma animação longa, renderiza 
    uma composição matematicamente densa num único frame estático, usando o 
    arquétipo da narrativa.
    """
    def construct(self):
        self.camera.background_color = theme.colors.get("background", "#000000")

        interp = intelligence.get("interpretation", {})
        emotion = interp.get("emotion", "mastery")
        foreground = theme.colors.get("foreground", "#FFFFFF")
        accent = theme.accent_color

        pool = ParticlePool(
            max_particles=140,
            emit_rate=28,
            dot_radius=0.02,
            color=foreground,
            emitter_spread=0.12,
            bounds=(-7.0, 7.0, -5.0, 5.0),
            lifetime_range=(1.0, 5.0)
        )
        pool.set_act_profile("resolution", signature="convergence_field")
        for _ in range(30):
            pool.update(0.1)
        pool.set_opacity(0.07)

        grid = NeuralGrid(rows=5, cols=5, spacing=1.05)
        grid.scale(1.15)
        grid.set_stroke(color=foreground, width=1.0, opacity=0.08)

        entropy_level = 0.05 if emotion == "mastery" else (0.4 if emotion == "tension" else 0.15)
        curve = LivingCurve(
            resolution=300,
            growth_progress=1.0,
            noise_amplitude=0.015,
            entropy=entropy_level,
            stroke_color=foreground,
            stroke_width=4.2,
        ).scale(1.22).shift(UP * 0.35 + LEFT * 0.1)

        glow_curve = LivingCurve(
            resolution=150,
            growth_progress=1.0,
            noise_amplitude=0.015,
            entropy=entropy_level,
            stroke_color=foreground,
            stroke_width=14.0,
        ).scale(1.22).shift(UP * 0.35 + LEFT * 0.1).set_opacity(0.055)

        resolve_dot = Dot(radius=0.055, color=accent)
        resolve_dot.move_to(curve.points[-1])

        guide = NarrativeContainer(width=5.3, height=7.0, corner_radius=0.28)
        guide.set_stroke(color=foreground, width=1.0, opacity=0.06)
        guide.shift(RIGHT * 0.35 + DOWN * 0.15)

        self.add(pool, grid, glow_curve, curve, resolve_dot, guide)
