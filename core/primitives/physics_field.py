"""
AIOX Physics Fields — v4.3
============================
Campos de força físicos para animações matematicamente corretas.
Integração via Verlet (estável) para uso em Manim updaters.

Primitivos:
  GravityField   — atração direcional (queda, flutuação)
  SpringForce    — atração elástica para um ponto âncora
  VortexField    — rotação espiral ao redor de um centro
  DampingForce   — resistência ao movimento (fricção do ar)
  PhysicsBody    — corpo com massa, posição, velocidade — integra todos os campos

Uso em Manim:
    body = PhysicsBody(position=[0, 2, 0], mass=1.0)
    body.add_field(GravityField(strength=0.5))
    body.add_field(VortexField(center=ORIGIN, strength=1.2))

    dot = Dot()
    dot.add_updater(lambda m, dt: m.move_to(body.step(dt)))
"""
import numpy as np
from typing import List


# ── Campos de Força ──────────────────────────────────────────────────────────

class GravityField:
    """
    Força gravitacional constante em uma direção.
    direction: vetor unitário (ex: [0, -1, 0] = cai para baixo)
    strength:  aceleração em unidades Manim/s²
    """
    def __init__(self, strength: float = 0.5, direction=None):
        self.strength = strength
        d = np.array(direction if direction is not None else [0, -1, 0], dtype=float)
        norm = np.linalg.norm(d)
        self.direction = d / norm if norm > 1e-6 else d

    def force(self, body: "PhysicsBody") -> np.ndarray:
        return self.direction * self.strength * body.mass


class SpringForce:
    """
    Força de mola: puxa o corpo para um ponto âncora.
    Lei de Hooke: F = -k * (pos - anchor) - damping * vel
    """
    def __init__(self, anchor=None, stiffness: float = 4.0, damping: float = 1.2):
        self.anchor = np.array(anchor if anchor is not None else [0, 0, 0], dtype=float)
        self.stiffness = stiffness
        self.damping = damping

    def force(self, body: "PhysicsBody") -> np.ndarray:
        displacement = body.position - self.anchor
        return -self.stiffness * displacement - self.damping * body.velocity


class VortexField:
    """
    Campo de vórtice: orbita o corpo ao redor de um centro.
    Combina força centrípeta (mantém órbita) + atração (espiral para dentro).
    """
    def __init__(self, center=None, strength: float = 1.0,
                 inward: float = 0.1, radius: float = 2.0):
        self.center = np.array(center if center is not None else [0, 0, 0], dtype=float)
        self.strength = strength
        self.inward = inward     # 0 = órbita pura, >0 = espiral para dentro
        self.radius = radius

    def force(self, body: "PhysicsBody") -> np.ndarray:
        r = body.position - self.center
        dist = np.linalg.norm(r)
        if dist < 1e-6:
            return np.zeros(3)

        # Força tangencial (rotação)
        tangent = np.array([-r[1], r[0], 0]) / dist
        f_tangent = tangent * self.strength

        # Força radial (atração para o raio alvo)
        f_radial = -r / dist * self.inward * abs(dist - self.radius)

        return f_tangent + f_radial


class DampingForce:
    """
    Resistência ao movimento proporcional à velocidade.
    Simula fricção viscosa do ar.
    """
    def __init__(self, coefficient: float = 0.3):
        self.coefficient = coefficient

    def force(self, body: "PhysicsBody") -> np.ndarray:
        return -self.coefficient * body.velocity


class NoiseForce:
    """
    Força baseada no AIOXNoiseField — turbulência orgânica.
    """
    def __init__(self, noise_field=None, entropy: float = 0.5, strength: float = 0.5):
        if noise_field is not None:
            self.field = noise_field
        else:
            from core.primitives.fields import AIOXNoiseField
            self.field = AIOXNoiseField(entropy=entropy)
        self.strength = strength

    def force(self, body: "PhysicsBody", time: float = 0.0) -> np.ndarray:
        v = self.field.get_vector(body.position, time)
        return v * self.strength


# ── Corpo Físico ─────────────────────────────────────────────────────────────

class PhysicsBody:
    """
    Partícula/corpo com massa que acumula campos de força.
    Integração via Velocity Verlet — mais estável que Euler simples.

    Uso:
        body = PhysicsBody([1, 2, 0], mass=1.0, velocity=[0.5, 0, 0])
        body.add_field(GravityField())
        body.add_field(SpringForce(anchor=ORIGIN))

        # Em Manim updater:
        dot.add_updater(lambda m, dt: m.move_to(body.step(dt)))
    """

    def __init__(self, position=None, velocity=None, mass: float = 1.0,
                 bounds=None, restitution: float = 0.6):
        self.position = np.array(position if position is not None else [0, 0, 0], dtype=float)
        self.velocity = np.array(velocity if velocity is not None else [0, 0, 0], dtype=float)
        self.mass = mass
        self.bounds = bounds      # [xmin, xmax, ymin, ymax] para bounce
        self.restitution = restitution
        self._fields: List = []
        self._acceleration = np.zeros(3)
        self._time = 0.0

    def add_field(self, field) -> "PhysicsBody":
        self._fields.append(field)
        return self

    def _compute_acceleration(self) -> np.ndarray:
        total_force = np.zeros(3)
        for field in self._fields:
            if isinstance(field, NoiseForce):
                total_force += field.force(self, self._time)
            else:
                total_force += field.force(self)
        return total_force / max(self.mass, 1e-6)

    def step(self, dt: float) -> np.ndarray:
        """Velocity Verlet integration. Retorna nova posição."""
        dt = min(dt, 0.05)  # Clamp para evitar instabilidade em frames lentos
        self._time += dt

        # Verlet: x(t+dt) = x(t) + v(t)*dt + 0.5*a(t)*dt²
        new_pos = self.position + self.velocity * dt + 0.5 * self._acceleration * dt ** 2

        # Nova aceleração na posição atualizada
        self.position = new_pos
        new_acc = self._compute_acceleration()

        # v(t+dt) = v(t) + 0.5*(a(t) + a(t+dt))*dt
        self.velocity += 0.5 * (self._acceleration + new_acc) * dt
        self._acceleration = new_acc

        # Bounce nos limites
        if self.bounds is not None:
            xmin, xmax, ymin, ymax = self.bounds
            if self.position[0] < xmin or self.position[0] > xmax:
                self.velocity[0] *= -self.restitution
                self.position[0] = np.clip(self.position[0], xmin, xmax)
            if self.position[1] < ymin or self.position[1] > ymax:
                self.velocity[1] *= -self.restitution
                self.position[1] = np.clip(self.position[1], ymin, ymax)

        return self.position.copy()

    def reset(self, position=None, velocity=None):
        if position is not None:
            self.position = np.array(position, dtype=float)
        if velocity is not None:
            self.velocity = np.array(velocity, dtype=float)
        self._acceleration = np.zeros(3)
        self._time = 0.0


# ── Preset de Física Narrativa ────────────────────────────────────────────────

def narrative_body(act: str, position=None, entropy: float = 0.5) -> PhysicsBody:
    """
    Retorna um PhysicsBody pré-configurado para cada ato narrativo.
    Uso rápido em cenas sem precisar configurar campos manualmente.
    """
    pos = position or [0, 0, 0]

    if act == "genesis":
        body = PhysicsBody(pos, mass=1.2)
        body.add_field(SpringForce(anchor=[0, 0, 0], stiffness=2.0, damping=2.5))
        body.add_field(DampingForce(0.4))

    elif act == "turbulence":
        body = PhysicsBody(pos, velocity=[0.3, 0.1, 0], mass=0.8)
        body.add_field(VortexField(strength=1.5, inward=0.2))
        body.add_field(NoiseForce(entropy=min(entropy + 0.3, 1.0), strength=0.8))
        body.add_field(DampingForce(0.1))

    elif act == "resolution":
        body = PhysicsBody(pos, mass=1.0)
        body.add_field(SpringForce(anchor=[0, 0, 0], stiffness=6.0, damping=3.5))
        body.add_field(DampingForce(0.6))

    else:
        body = PhysicsBody(pos)

    return body
