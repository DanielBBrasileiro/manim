"""
Narrative curves: the main protagonists of v4.0.
Each curve has a behavior that evolves over time.
v4.3: Noise substituído por FBM via AIOXNoiseField (opensimplex quando disponível).
"""
from manim import *
import numpy as np
from core.primitives.fields import AIOXNoiseField


class LivingCurve(VMobject):
    """A curve that evolves from smooth to chaotic and back."""

    def __init__(self,
                 resolution=200,
                 noise_amplitude=0.0,
                 growth_progress=0.0,
                 entropy=0.5,
                 noise_field: AIOXNoiseField = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.resolution = resolution
        self.noise_amplitude = noise_amplitude
        self.growth_progress = growth_progress
        self.entropy = entropy
        # Reutiliza campo externo (para consistência entre frames) ou cria novo
        self._noise = noise_field or AIOXNoiseField(signature=_signature_from_entropy(entropy))
        self._build_curve()

    def _build_curve(self):
        """Generates sigmoid curve with FBM noise overlay."""
        points = []
        actual_points = max(2, int(self.resolution * self.growth_progress))

        for i in range(actual_points):
            t = i / self.resolution
            # Base: sigmoid growth metaphor
            y = 1 / (1 + np.exp(-8 * (t - 0.5)))

            # FBM noise overlay — orgânico, sem periodicidade visível
            if self.noise_amplitude > 0:
                x_manim = t * 6 - 3
                y_base = y * 4 - 2
                noise_vec = self._noise.get_vector([x_manim, y_base, 0], time=t * 2.0)
                y += noise_vec[1] * self.noise_amplitude

            points.append(np.array([
                t * 6 - 3,
                y * 4 - 2,
                0
            ]))

        if len(points) > 1:
            self.set_points_smoothly(points)

    def grow_to(self, progress, noise=0.0):
        """Returns a new state for the curve to animate into."""
        return LivingCurve(
            resolution=self.resolution,
            noise_amplitude=noise,
            growth_progress=progress,
            entropy=self.entropy,
            noise_field=self._noise,   # Mantém o mesmo campo = continuidade visual
            stroke_color=self.get_stroke_color(),
            stroke_width=self.get_stroke_width()
        ).match_style(self)


def _signature_from_entropy(entropy: float) -> str:
    if entropy >= 0.72:
        return "chaotic_dispersion"
    if entropy >= 0.45:
        return "oscillatory_wave"
    return "breathing_field"
