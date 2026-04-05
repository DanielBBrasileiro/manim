"""physics_mixin.py — Pymunk rigid-body physics for Manim scenes.

Provides three explicit lifecycle functions:

    space = setup_physics(seed, entropy, regime)   # initialise
    state = evaluate_physics(space, steps, dt)     # run + extract state
    teardown_physics(space)                         # explicit cleanup

The extracted :class:`PhysicsState` is written to
``engines/remotion/src/generated/physics_state.ts`` via
:func:`write_physics_state` so that Remotion compositions can import
real physics data at build time without an async fetch.

Gracefully degrades to neutral defaults when pymunk is not installed.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import TypedDict

try:
    import pymunk as _pymunk

    _PYMUNK_AVAILABLE = True
except ImportError:  # pragma: no cover
    _pymunk = None  # type: ignore[assignment]
    _PYMUNK_AVAILABLE = False

ROOT = Path(__file__).resolve().parent.parent.parent
_GENERATED_TS = ROOT / "engines" / "remotion" / "src" / "generated" / "physics_state.ts"
_N_BODIES = 20  # lightweight — 20 bodies is sufficient for state extraction


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


class PhysicsState(TypedDict):
    dominant_velocity: float   # RMS speed, normalised [0, 1]
    velocity_x: float          # mean Vx, clamped [-1, 1]
    velocity_y: float          # mean Vy, clamped [-1, 1]
    kinetic_energy: float      # total KE, normalised [0, 1]
    regime: str                # 'laminar' | 'oscillatory' | 'turbulent'
    seed: int
    steps_evaluated: int


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


def setup_physics(
    seed: int,
    entropy: dict,
    regime: str,
) -> "pymunk.Space | None":  # type: ignore[name-defined]  # noqa: F821
    """Create and seed a pymunk :class:`Space` from briefing entropy values.

    Returns ``None`` when pymunk is unavailable (graceful degradation).
    """
    if not _PYMUNK_AVAILABLE:
        return None

    phys = float(entropy.get("physical", 0.5))
    struct = float(entropy.get("structural", 0.5))

    space = _pymunk.Space()
    space.gravity = (0.0, -struct * 400.0)
    space.damping = 0.92  # mild air resistance

    rng = random.Random(seed)
    for _ in range(_N_BODIES):
        moment = _pymunk.moment_for_circle(1.0, 0, 6)
        body = _pymunk.Body(mass=1.0, moment=moment)
        body.position = (rng.uniform(-180.0, 180.0), rng.uniform(-180.0, 180.0))

        speed = phys * 280.0
        angle = rng.uniform(0.0, 2.0 * math.pi)
        body.velocity = (math.cos(angle) * speed, math.sin(angle) * speed)

        shape = _pymunk.Circle(body, radius=6)
        shape.elasticity = max(0.1, 1.0 - struct * 0.6)
        shape.friction = 0.3
        space.add(body, shape)

    return space


def evaluate_physics(
    space: "pymunk.Space | None",  # type: ignore[name-defined]  # noqa: F821
    *,
    steps: int = 60,
    dt: float = 1.0 / 60.0,
    seed: int = 0,
) -> PhysicsState:
    """Step the simulation *steps* times and return a :class:`PhysicsState` snapshot.

    Returns neutral defaults when *space* is ``None``.
    """
    if space is None or not _PYMUNK_AVAILABLE:
        return PhysicsState(
            dominant_velocity=0.5,
            velocity_x=0.0,
            velocity_y=0.0,
            kinetic_energy=0.5,
            regime="laminar",
            seed=seed,
            steps_evaluated=0,
        )

    for _ in range(steps):
        space.step(dt)

    bodies = [b for b in space.bodies if b.body_type == _pymunk.Body.DYNAMIC]
    if not bodies:
        return PhysicsState(
            dominant_velocity=0.0, velocity_x=0.0, velocity_y=0.0,
            kinetic_energy=0.0, regime="laminar", seed=seed, steps_evaluated=steps,
        )

    vxs = [b.velocity.x for b in bodies]
    vys = [b.velocity.y for b in bodies]
    speeds = [math.sqrt(vx ** 2 + vy ** 2) for vx, vy in zip(vxs, vys)]
    mean_speed = sum(speeds) / len(speeds)
    mean_vx = sum(vxs) / len(vxs)
    mean_vy = sum(vys) / len(vys)
    ke = sum(0.5 * b.mass * (b.velocity.x ** 2 + b.velocity.y ** 2) for b in bodies)

    # Classify regime by coefficient of variation of speed
    variance = sum((s - mean_speed) ** 2 for s in speeds) / len(speeds)
    cv = math.sqrt(variance) / (mean_speed + 1e-9)
    if cv > 0.7:
        regime = "turbulent"
    elif cv < 0.2:
        regime = "laminar"
    else:
        regime = "oscillatory"

    _NORM = 400.0  # max expected speed in units/s
    _KE_MAX = _N_BODIES * 0.5 * 1.0 * _NORM ** 2

    return PhysicsState(
        dominant_velocity=min(1.0, mean_speed / _NORM),
        velocity_x=max(-1.0, min(1.0, mean_vx / _NORM)),
        velocity_y=max(-1.0, min(1.0, mean_vy / _NORM)),
        kinetic_energy=min(1.0, ke / _KE_MAX),
        regime=regime,
        seed=seed,
        steps_evaluated=steps,
    )


def teardown_physics(
    space: "pymunk.Space | None",  # type: ignore[name-defined]  # noqa: F821
) -> None:
    """Remove all shapes and bodies from *space* — explicit teardown required."""
    if space is None or not _PYMUNK_AVAILABLE:
        return
    for shape in list(space.shapes):
        space.remove(shape)
    for body in list(space.bodies):
        space.remove(body)


# ---------------------------------------------------------------------------
# Manifest writer
# ---------------------------------------------------------------------------


def write_physics_state(state: PhysicsState) -> Path:
    """Serialise *state* to ``engines/remotion/src/generated/physics_state.ts``.

    The generated TypeScript constant is imported at Remotion build time by
    ``NarrativeText`` and ``CinematicNarrative``, making real physics data
    available without async fetches.
    """
    _GENERATED_TS.parent.mkdir(parents=True, exist_ok=True)
    ts_content = (
        "// ⚠️ AUTO-GENERATED — DO NOT EDIT\n"
        "// Written by engines/manim/physics_mixin.py after EntropyDemo evaluation.\n"
        "\n"
        "export interface PhysicsState {\n"
        "  dominantVelocity: number;\n"
        "  velocityX: number;\n"
        "  velocityY: number;\n"
        "  kineticEnergy: number;\n"
        "  regime: 'laminar' | 'oscillatory' | 'turbulent';\n"
        "  seed: number;\n"
        "  stepsEvaluated: number;\n"
        "}\n"
        "\n"
        f"export const PHYSICS_STATE: PhysicsState = {{\n"
        f"  dominantVelocity: {state['dominant_velocity']:.4f},\n"
        f"  velocityX: {state['velocity_x']:.4f},\n"
        f"  velocityY: {state['velocity_y']:.4f},\n"
        f"  kineticEnergy: {state['kinetic_energy']:.4f},\n"
        f"  regime: '{state['regime']}',\n"
        f"  seed: {state['seed']},\n"
        f"  stepsEvaluated: {state['steps_evaluated']},\n"
        "}};\n"
    )
    _GENERATED_TS.write_text(ts_content, encoding="utf-8")
    return _GENERATED_TS
