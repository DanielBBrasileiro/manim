"""
AIOX Particle System — v4.3
=============================
Sistema de partículas cinematográfico para Manim CE.

Performance:
  - Até ~500 partículas: numpy puro (sempre disponível)
  - 500–10.000 partículas: Numba JIT (se instalado)
  - Trail rendering para efeito de rastro temporal

Primitivos:
  ParticlePool  — pool principal com emitter, força e renderer
  TrailPool     — variante com rastros (trail history)

Uso em Manim:
    class MyScene(Scene):
        def construct(self):
            pool = ParticlePool(
                max_particles=800,
                emitter_pos=LEFT * 3,
                forces=[VortexField(strength=1.2), DampingForce(0.2)],
                entropy=0.7,
            )
            self.add(pool)
            self.play(pool.animate_birth(run_time=2))
            self.wait(5)  # updater roda automaticamente
"""
import numpy as np
from manim import *
from typing import List, Optional

try:
    from numba import njit, prange
    _HAS_NUMBA = True
except ImportError:
    _HAS_NUMBA = False

# ── Kernel de integração (Numba JIT se disponível) ───────────────────────────

if _HAS_NUMBA:
    @njit(parallel=True, cache=True)
    def _step_particles_jit(
        positions: np.ndarray,   # (N, 3)
        velocities: np.ndarray,  # (N, 3)
        lifetimes: np.ndarray,   # (N,)
        alive: np.ndarray,       # (N,) bool
        gravity: np.ndarray,     # (3,)
        noise_vecs: np.ndarray,  # (N, 3) pré-calculado fora do JIT
        damping: float,
        dt: float,
        bounds: np.ndarray,      # [xmin, xmax, ymin, ymax]
        restitution: float,
    ):
        N = positions.shape[0]
        for i in prange(N):
            if not alive[i]:
                continue
            lifetimes[i] -= dt
            if lifetimes[i] <= 0:
                alive[i] = False
                continue

            force = gravity + noise_vecs[i] - damping * velocities[i]
            velocities[i] += force * dt
            positions[i] += velocities[i] * dt

            # Bounce
            if positions[i, 0] < bounds[0]:
                velocities[i, 0] = abs(velocities[i, 0]) * restitution
                positions[i, 0] = bounds[0]
            elif positions[i, 0] > bounds[1]:
                velocities[i, 0] = -abs(velocities[i, 0]) * restitution
                positions[i, 0] = bounds[1]
            if positions[i, 1] < bounds[2]:
                velocities[i, 1] = abs(velocities[i, 1]) * restitution
                positions[i, 1] = bounds[2]
            elif positions[i, 1] > bounds[3]:
                velocities[i, 1] = -abs(velocities[i, 1]) * restitution
                positions[i, 1] = bounds[3]

else:
    def _step_particles_jit(positions, velocities, lifetimes, alive,
                             gravity, noise_vecs, damping, dt, bounds, restitution):
        mask = alive
        lifetimes[mask] -= dt
        dead = mask & (lifetimes <= 0)
        alive[dead] = False
        mask = alive

        force = gravity + noise_vecs - damping * velocities
        velocities[mask] += force[mask] * dt
        positions[mask] += velocities[mask] * dt

        # Bounce
        hit_xl = mask & (positions[:, 0] < bounds[0])
        hit_xr = mask & (positions[:, 0] > bounds[1])
        hit_yb = mask & (positions[:, 1] < bounds[2])
        hit_yt = mask & (positions[:, 1] > bounds[3])
        velocities[hit_xl, 0] = np.abs(velocities[hit_xl, 0]) * restitution
        velocities[hit_xr, 0] = -np.abs(velocities[hit_xr, 0]) * restitution
        velocities[hit_yb, 1] = np.abs(velocities[hit_yb, 1]) * restitution
        velocities[hit_yt, 1] = -np.abs(velocities[hit_yt, 1]) * restitution
        positions[:, 0] = np.clip(positions[:, 0], bounds[0], bounds[1])
        positions[:, 1] = np.clip(positions[:, 1], bounds[2], bounds[3])


# ── Particle Pool ─────────────────────────────────────────────────────────────

class ParticlePool(VGroup):
    """
    Pool de partículas com física integrada para Manim CE.

    Args:
        max_particles:   Número máximo de partículas simultâneas.
        emitter_pos:     Posição inicial do emitter (array 3D ou Manim vector).
        emitter_spread:  Raio de dispersão inicial das partículas.
        forces:          Lista de campos de força (PhysicsField instances).
        entropy:         0.0–1.0 (controla aleatoriedade via Zara).
        lifetime_range:  (min, max) em segundos de vida de cada partícula.
        emit_rate:       Partículas emitidas por segundo.
        dot_radius:      Raio visual de cada partícula.
        color:           Cor das partículas (usa WHITE por padrão — brand safe).
        bounds:          [xmin, xmax, ymin, ymax] para bounce.
        gravity:         Vetor de gravidade [dx, dy, dz].
        damping:         Coeficiente de amortecimento (0.0–1.0).
    """

    def __init__(
        self,
        max_particles: int = 200,
        emitter_pos=None,
        emitter_spread: float = 0.3,
        forces: Optional[List] = None,
        entropy: float = 0.5,
        lifetime_range: tuple = (2.0, 5.0),
        emit_rate: float = 40,
        dot_radius: float = 0.025,
        color=WHITE,
        bounds=(-7, 7, -4, 4),
        gravity=None,
        damping: float = 0.15,
        seed: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.max_particles = max_particles
        self.emitter_pos = np.array(emitter_pos if emitter_pos is not None else [0, 0, 0], dtype=float)
        self.emitter_spread = emitter_spread
        self.forces = forces or []
        self.entropy = entropy
        self.lifetime_range = lifetime_range
        self.emit_rate = emit_rate
        self.dot_radius = dot_radius
        self.particle_color = color
        self.bounds = np.array(bounds, dtype=float)
        self.gravity_vec = np.array(gravity if gravity is not None else [0, 0, 0], dtype=float)
        self.damping = damping

        # Estado interno
        self._positions = np.zeros((max_particles, 3))
        self._velocities = np.zeros((max_particles, 3))
        self._lifetimes = np.zeros(max_particles)
        self._alive = np.zeros(max_particles, dtype=bool)
        self._emit_accumulator = 0.0
        self._time = 0.0
        # Seeded RNG — reproducible when seed is provided, random otherwise
        self._rng = np.random.default_rng(seed)

        # Conecta a Inteligência Semântica da Zona Zara
        from core.primitives.theme_loader import intelligence
        self._intelligence = intelligence
        
        signature = self._intelligence.get("interpretation", {}).get("motion_signature", "breathing_field")
        timeline = self._intelligence.get("timeline")
        
        # Ajustes orgânicos baseados na "Personality" do movimento inicial
        if signature == "elastic_snap":
            self.damping *= 0.3  # Menos atrito, "estala" rápido
        elif signature == "breathing_field":
            self.damping *= 1.5  # Mais arrasto, lento
            
        # Noise field para variância orgânica (Assinatura Semântica Temporal ou Baseline)
        from core.primitives.fields import AIOXNoiseField, TemporalNoiseField
        
        if timeline:
            print("⏳ [TemporalEngine] Inicializando motor contínuo 0s~10s na piscina de partículas.")
            self._noise = TemporalNoiseField(timeline=timeline, duration=8.0)
        else:
            self._noise = AIOXNoiseField(signature=signature)

        # Dots Manim pré-alocados (pool estático para performance)
        self._dots = [
            Dot(radius=dot_radius, color=color, fill_opacity=0)
            for _ in range(max_particles)
        ]
        for dot in self._dots:
            self.add(dot)

        self.add_updater(self._update)

    def _emit_particle(self, index: int):
        spread = self.emitter_spread
        self._positions[index] = self.emitter_pos + self._rng.uniform(-spread, spread, 3) * [1, 1, 0]

        # Velocidade atrelada à entropia física bruta (a intensidade verdadeira)
        phys = self._intelligence.get("entropy", {}).get("physical", 0.5)
        speed = np.interp(phys, [0, 1], [0.3, 2.5])

        # O Regime Comportamental e flow direcionam a dispersão
        flow = self._intelligence.get("interpretation", {}).get("flow", "nonlinear")
        if flow == "linear":
            angle = self._rng.uniform(-np.pi / 16, np.pi / 16)
        else:
            angle = self._rng.uniform(0, 2 * np.pi)

        self._velocities[index] = np.array([
            np.cos(angle) * speed * self._rng.uniform(0.5, 1.5),
            np.sin(angle) * speed * self._rng.uniform(0.5, 1.5),
            0,
        ])
        lmin, lmax = self.lifetime_range
        self._lifetimes[index] = self._rng.uniform(lmin, lmax)
        self._alive[index] = True

    def _find_dead(self) -> Optional[int]:
        dead = np.where(~self._alive)[0]
        return int(dead[0]) if len(dead) > 0 else None

    def _compute_noise_vecs(self) -> np.ndarray:
        """Pré-computa vetores de ruído para todas as partículas vivas."""
        vecs = np.zeros((self.max_particles, 3))
        alive_idx = np.where(self._alive)[0]
        for i in alive_idx:
            vecs[i] = self._noise.get_vector(self._positions[i], self._time)
        return vecs

    def _update(self, mob, dt: float):
        dt = min(dt, 0.05)
        self._time += dt
        self._emit_accumulator += dt * self.emit_rate

        # Emitir novas partículas
        while self._emit_accumulator >= 1.0:
            idx = self._find_dead()
            if idx is not None:
                self._emit_particle(idx)
            self._emit_accumulator -= 1.0

        # Integrar física
        noise_vecs = self._compute_noise_vecs()
        _step_particles_jit(
            self._positions, self._velocities, self._lifetimes, self._alive,
            self.gravity_vec, noise_vecs, self.damping, dt,
            self.bounds, restitution=0.55,
        )

        # Sincronizar posições Manim
        for i, dot in enumerate(self._dots):
            if self._alive[i]:
                # Opacidade baseada no lifetime restante
                lmin, lmax = self.lifetime_range
                t_norm = np.clip(self._lifetimes[i] / lmax, 0, 1)
                opacity = float(np.interp(t_norm, [0, 0.1, 0.8, 1.0], [0, 1, 1, 0]))
                dot.move_to(self._positions[i])
                dot.set_fill(opacity=opacity)
            else:
                dot.set_fill(opacity=0)
                dot.move_to(self.emitter_pos)  # Esconde fora da cena

    def animate_birth(self, run_time: float = 2.0) -> Animation:
        """Anima a emissão inicial das primeiras partículas."""
        return FadeIn(self, run_time=run_time, rate_func=smooth)

    def set_emitter(self, new_pos) -> "ParticlePool":
        """Move o emitter em runtime."""
        self.emitter_pos = np.array(new_pos, dtype=float)
        return self

    @property
    def alive_count(self) -> int:
        return int(np.sum(self._alive))

    @property
    def engine(self) -> str:
        return "numba_jit" if _HAS_NUMBA else "numpy"


# ── Trail Pool ────────────────────────────────────────────────────────────────

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
        color=WHITE,
        bounds=(-7, 7, -4, 4),
        gravity=None,
        damping: float = 0.1,
        seed: Optional[int] = None,
        **kwargs,
    ):
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
        self._rng = np.random.default_rng(seed)
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
        self._positions[idx] = self.emitter_pos + self._rng.uniform(-spread, spread, 3) * [1, 1, 0]
        speed = float(np.interp(self.entropy, [0, 1], [0.5, 2.5]))
        angle = self._rng.uniform(0, 2 * np.pi)
        self._velocities[idx] = [np.cos(angle) * speed, np.sin(angle) * speed, 0]
        lmin, lmax = self.lifetime_range
        self._lifetimes[idx] = self._rng.uniform(lmin, lmax)
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
