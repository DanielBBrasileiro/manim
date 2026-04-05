import json
from pathlib import Path
from typing import Any

import numpy as np
import pymunk


ROOT = Path(__file__).resolve().parent.parent.parent


class PhysicsOrchestratorMixin:
    """Pequeno orquestrador Pymunk para cenas Manim com teardown explícito."""

    _physics_space: pymunk.Space | None = None
    _physics_bodies: list[pymunk.Body]
    _physics_shapes: list[pymunk.Shape]
    _physics_constraints: list[pymunk.Constraint]
    _physics_seed: int | None = None
    _physics_rng: np.random.Generator | None = None

    def setup_physics_environment(
        self,
        *,
        seed: int,
        gravity: tuple[float, float] = (0.0, 0.0),
        damping: float = 0.985,
        bounds: tuple[float, float, float, float] = (-6.4, 6.4, -3.6, 3.6),
    ) -> pymunk.Space:
        self._physics_seed = int(seed)
        self._physics_rng = np.random.default_rng(self._physics_seed)
        self._physics_bodies = []
        self._physics_shapes = []
        self._physics_constraints = []

        space = pymunk.Space(threaded=False)
        space.gravity = gravity
        space.damping = damping
        self._physics_space = space
        self._add_world_bounds(bounds)
        return space

    def _add_world_bounds(self, bounds: tuple[float, float, float, float]) -> None:
        if self._physics_space is None:
            raise RuntimeError("Physics environment not initialized.")
        xmin, xmax, ymin, ymax = bounds
        static_body = self._physics_space.static_body
        segments = [
            pymunk.Segment(static_body, (xmin, ymin), (xmax, ymin), 0.05),
            pymunk.Segment(static_body, (xmax, ymin), (xmax, ymax), 0.05),
            pymunk.Segment(static_body, (xmax, ymax), (xmin, ymax), 0.05),
            pymunk.Segment(static_body, (xmin, ymax), (xmin, ymin), 0.05),
        ]
        for segment in segments:
            segment.elasticity = 0.82
            segment.friction = 0.12
        self._physics_space.add(*segments)
        self._physics_shapes.extend(segments)

    def create_probe_body(
        self,
        *,
        position: tuple[float, float],
        velocity: tuple[float, float],
        mass: float = 1.0,
        radius: float = 0.18,
        elasticity: float = 0.82,
        friction: float = 0.12,
    ) -> pymunk.Body:
        if self._physics_space is None:
            raise RuntimeError("Physics environment not initialized.")
        moment = pymunk.moment_for_circle(mass, 0.0, radius)
        body = pymunk.Body(mass, moment)
        body.position = position
        body.velocity = velocity
        shape = pymunk.Circle(body, radius)
        shape.elasticity = elasticity
        shape.friction = friction
        self._physics_space.add(body, shape)
        self._physics_bodies.append(body)
        self._physics_shapes.append(shape)
        return body

    def evaluate_physics_step(self, *, dt: float, steps: int = 1) -> None:
        if self._physics_space is None:
            raise RuntimeError("Physics environment not initialized.")
        for _ in range(max(steps, 1)):
            self._physics_space.step(dt)

    def capture_physics_state(self, body: pymunk.Body, *, label: str = "probe") -> dict[str, Any]:
        vx, vy = float(body.velocity.x), float(body.velocity.y)
        speed = float(np.hypot(vx, vy))
        return {
            "label": label,
            "seed": self._physics_seed,
            "position": {
                "x": float(body.position.x),
                "y": float(body.position.y),
            },
            "velocity": {
                "x": vx,
                "y": vy,
                "magnitude": speed,
            },
            "normalized_velocity": float(np.clip(speed / 420.0, 0.0, 1.0)),
        }

    def export_physics_state(self, payload: dict[str, Any]) -> Path:
        output_path = ROOT / "output" / "context" / "physics_state.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        return output_path

    def teardown_physics(self) -> None:
        if self._physics_space is None:
            return
        removable = [*self._physics_constraints, *self._physics_shapes, *self._physics_bodies]
        if removable:
            try:
                self._physics_space.remove(*removable)
            except Exception:
                pass
        self._physics_constraints = []
        self._physics_shapes = []
        self._physics_bodies = []
        self._physics_space = None
        self._physics_rng = None
