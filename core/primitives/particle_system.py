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
        self._timeline_duration = 8.0
        self._active_signature = None

        # Conecta a Inteligência Semântica da Zona Zara
        from core.primitives.theme_loader import intelligence
        self._intelligence = intelligence
        
        signature = self._intelligence.get("interpretation", {}).get("motion_signature", "breathing_field")
        timeline = self._intelligence.get("timeline")
        self._base_signature = signature
        self._timeline = timeline
        
        # Ajustes orgânicos baseados na "Personality" do movimento inicial
        if signature == "elastic_snap":
            self.damping *= 0.3  # Menos atrito, "estala" rápido
        elif signature == "breathing_field":
            self.damping *= 1.5  # Mais arrasto, lento
            
        self._set_noise_source(signature, use_timeline=bool(timeline))

        # Dots Manim pré-alocados (pool estático para performance)
        self._dots = [
            Dot(radius=dot_radius, color=color, fill_opacity=0)
            for _ in range(max_particles)
        ]
        for dot in self._dots:
            self.add(dot)

        self.add_updater(self._update)

    def _set_noise_source(self, signature: str, use_timeline: bool = False):
        """Atualiza a fonte de ruído sem reinicializar o pool."""
        from core.primitives.fields import AIOXNoiseField, TemporalNoiseField

        if use_timeline and self._timeline:
            print("⏳ [TemporalEngine] Inicializando motor contínuo 0s~10s na piscina de partículas.")
            self._noise = TemporalNoiseField(timeline=self._timeline, duration=self._timeline_duration)
            self._active_signature = "timeline"
        else:
            self._noise = AIOXNoiseField(signature=signature)
            self._active_signature = signature

    def set_particle_color(self, color) -> "ParticlePool":
        self.particle_color = color
        for dot in self._dots:
            dot.set_color(color)
        return self

    def set_motion_signature(self, signature: str, use_timeline: bool = False) -> "ParticlePool":
        self._set_noise_source(signature, use_timeline=use_timeline)
        return self

    def set_act_profile(
        self,
        act_name: str,
        *,
        signature: Optional[str] = None,
        emit_rate: Optional[float] = None,
        emitter_spread: Optional[float] = None,
        damping: Optional[float] = None,
        gravity=None,
        lifetime_range: Optional[tuple] = None,
        bounds=None,
        color=None,
    ) -> "ParticlePool":
        """
        Reconfigura o pool para um ato narrativo sem recriar as partículas.

        Perfis default:
          - genesis: nascente, coeso, baixa densidade
          - turbulence: expansão, ruptura, alta energia
          - resolution: convergência, disciplina e limpeza
        """
        presets = {
            "genesis": {
                "signature": "breathing_field",
                "emit_rate": 24,
                "emitter_spread": 0.14,
                "damping": 0.22,
                "gravity": [0.0, 0.02, 0.0],
                "lifetime_range": (2.4, 4.8),
            },
            "turbulence": {
                "signature": "chaotic_burst",
                "emit_rate": 110,
                "emitter_spread": 1.8,
                "damping": 0.05,
                "gravity": [0.0, -0.08, 0.0],
                "lifetime_range": (1.1, 3.2),
            },
            "resolution": {
                "signature": "convergence_field",
                "emit_rate": 36,
                "emitter_spread": 0.28,
                "damping": 0.28,
                "gravity": [0.0, 0.0, 0.0],
                "lifetime_range": (1.6, 3.8),
            },
        }
        config = dict(presets.get(act_name, {}))
        overrides = {
            "signature": signature,
            "emit_rate": emit_rate,
            "emitter_spread": emitter_spread,
            "damping": damping,
            "gravity": gravity,
            "lifetime_range": lifetime_range,
            "bounds": bounds,
            "color": color,
        }
        for key, value in overrides.items():
            if value is not None:
                config[key] = value

        next_signature = config.get("signature", self._base_signature)
        self.set_motion_signature(next_signature)
        self.emit_rate = config.get("emit_rate", self.emit_rate)
        self.emitter_spread = config.get("emitter_spread", self.emitter_spread)
        self.damping = config.get("damping", self.damping)
        if "gravity" in config:
            self.gravity_vec = np.array(config["gravity"], dtype=float)
        if "lifetime_range" in config:
            self.lifetime_range = tuple(config["lifetime_range"])
        if "bounds" in config:
            self.bounds = np.array(config["bounds"], dtype=float)
        if "color" in config:
            self.set_particle_color(config["color"])
        return self

    def _emit_particle(self, index: int):
        spread = self.emitter_spread
        rng = np.random
        self._positions[index] = self.emitter_pos + rng.uniform(-spread, spread, 3) * [1, 1, 0]
        
        # Velocidade atrelada à entropia física bruta (a intensidade verdadeira)
        phys = self._intelligence.get("entropy", {}).get("physical", 0.5)
        speed = np.interp(phys, [0, 1], [0.3, 2.5])
        
        # O Regime Comportamental e flow direcionam a dispersão
        flow = self._intelligence.get("interpretation", {}).get("flow", "nonlinear")
        if flow == "linear":
            # Emissão direcional
            angle = rng.uniform(-np.pi/16, np.pi/16)
        else:
            angle = rng.uniform(0, 2 * np.pi)
            
        self._velocities[index] = np.array([
            np.cos(angle) * speed * rng.uniform(0.5, 1.5),
            np.sin(angle) * speed * rng.uniform(0.5, 1.5),
            0
        ])
        lmin, lmax = self.lifetime_range
        self._lifetimes[index] = rng.uniform(lmin, lmax)
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

__all__ = ["ParticlePool", "TrailPool"]


def __getattr__(name: str):
    if name == "TrailPool":
        from .trail_pool import TrailPool as extracted_trail_pool

        return extracted_trail_pool
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
