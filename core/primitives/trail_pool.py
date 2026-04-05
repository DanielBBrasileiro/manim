"""
AIOX Trail Pool — Particle trails with temporal history.

Extracted from particle_system.py to keep modules under 500 lines.
Each particle leaves a fading trail of dots for flow/wind effects.
"""
import numpy as np
from manim import Dot, VGroup

from .particle_system import _step_particles_jit


class TrailPool(VGroup):
    """
    Variante do ParticlePool com rastros temporais.
    Cada partícula deixa uma trilha de pontos que fadeia com o tempo.

    Ideal para: fluxo de dados, trajetórias de partículas, wind trails.

    Args:
        trail_length: Número de pontos no rastro de cada partícula.
        (demais args idênticos ao ParticlePool)
    """

    def __init__(
        self,
        max_particles: int = 80,
        trail_length: int = 12,
        emitter_pos=None,
        entropy: float = 0.5,
        lifetime_range: tuple = (3.0, 6.0),
        emit_rate: float = 15,
        color=None,
        bounds=(-7, 7, -4, 4),
        gravity=None,
        damping: float = 0.1,
        **kwargs,
    ):
        from manim import WHITE
        if color is None:
            color = WHITE

        super().__init__(**kwargs)
        self.max_particles = max_particles
        self.trail_length = trail_length
        self.emitter_pos = np.array(emitter_pos if emitter_pos is not None else [0, 0, 0], dtype=float)
        self.entropy = entropy
        self.lifetime_range = lifetime_range
        self.emit_rate = emit_rate
        self.trail_color = color
        self.bounds_arr = np.array(bounds, dtype=float)
        self.gravity_vec = np.array(gravity if gravity is not None else [0, 0, 0], dtype=float)
        self.damping = damping

        self._positions = np.zeros((max_particles, 3))
        self._velocities = np.zeros((max_particles, 3))
        self._lifetimes = np.zeros(max_particles)
        self._alive = np.zeros(max_particles, dtype=bool)
        # Histórico de posições para o rastro
        self._history = np.zeros((max_particles, trail_length, 3))
        self._emit_acc = 0.0
        self._time = 0.0

        from core.primitives.theme_loader import intelligence
        signature = intelligence.get("interpretation", {}).get("motion_signature", "breathing_field")
        timeline = intelligence.get("timeline")

        from core.primitives.fields import AIOXNoiseField, TemporalNoiseField
        if timeline:
            self._noise = TemporalNoiseField(timeline=timeline, duration=8.0)
        else:
            self._noise = AIOXNoiseField(signature=signature)

        # Pré-aloca linhas de rastro
        self._trails = [
            VGroup(*[
                Dot(radius=0.015, color=color, fill_opacity=0)
                for _ in range(trail_length)
            ])
            for _ in range(max_particles)
        ]
        for trail in self._trails:
            self.add(trail)

        self.add_updater(self._update)

    def _emit(self, idx: int):
        spread = float(np.interp(self.entropy, [0, 1], [0.1, 0.6]))
        self._positions[idx] = self.emitter_pos + np.random.uniform(-spread, spread, 3) * [1, 1, 0]
        speed = float(np.interp(self.entropy, [0, 1], [0.5, 2.5]))
        angle = np.random.uniform(0, 2 * np.pi)
        self._velocities[idx] = [np.cos(angle) * speed, np.sin(angle) * speed, 0]
        lmin, lmax = self.lifetime_range
        self._lifetimes[idx] = np.random.uniform(lmin, lmax)
        self._alive[idx] = True
        self._history[idx] = self._positions[idx]

    def _update(self, mob, dt: float):
        dt = min(dt, 0.05)
        self._time += dt
        self._emit_acc += dt * self.emit_rate

        while self._emit_acc >= 1.0:
            dead = np.where(~self._alive)[0]
            if len(dead):
                self._emit(int(dead[0]))
            self._emit_acc -= 1.0

        alive_idx = np.where(self._alive)[0]
        noise_vecs = np.zeros((self.max_particles, 3))
        for i in alive_idx:
            noise_vecs[i] = self._noise.get_vector(self._positions[i], self._time)

        _step_particles_jit(
            self._positions, self._velocities, self._lifetimes, self._alive,
            self.gravity_vec, noise_vecs, self.damping, dt,
            self.bounds_arr, 0.5,
        )

        # Atualiza histórico e rastros visuais
        for i in alive_idx:
            # Shift history (mais recente no início)
            self._history[i] = np.roll(self._history[i], 1, axis=0)
            self._history[i, 0] = self._positions[i]

            lmin, lmax = self.lifetime_range
            life_t = np.clip(self._lifetimes[i] / lmax, 0, 1)

            for j, dot in enumerate(self._trails[i]):
                age = j / max(self.trail_length - 1, 1)
                opacity = float(np.interp(age, [0, 1], [0.9 * life_t, 0.0]))
                radius = float(np.interp(age, [0, 1], [0.02, 0.006]))
                dot.move_to(self._history[i, j])
                dot.set_fill(opacity=opacity)
                dot.width = radius * 2

        # Esconde partículas mortas
        for i in np.where(~self._alive)[0]:
            for dot in self._trails[i]:
                dot.set_fill(opacity=0)
