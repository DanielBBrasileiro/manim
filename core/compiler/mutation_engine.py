from __future__ import annotations

import random
from typing import Optional

from core.compiler.latent_space import map_intent_to_vector, get_signature_from_vector, CreativeVector


def mutate_entropy(plan: dict, rng: Optional[random.Random] = None) -> dict:
    """Mutação via Espaço Latente (Vetores 5D).

    *rng* must be a seeded :class:`random.Random` instance when reproducibility
    is required.  If omitted, an unseeded instance is created (legacy behaviour,
    non-deterministic).
    """
    _rng = rng if rng is not None else random.Random()

    perturbation = CreativeVector(
        tension=_rng.uniform(0.0, 1.0),
        density=_rng.uniform(0.0, 1.0),
        chaos=_rng.uniform(0.0, 1.0),
        rhythm=_rng.uniform(0.0, 1.0),
        stability=_rng.uniform(0.0, 1.0),
    )

    base_v = CreativeVector(0.5, 0.5, 0.5, 0.5, 0.5)
    new_v = base_v.blend(perturbation, factor=0.15)

    plan["entropy"] = new_v.to_entropy()
    return plan


def mutate_motion(plan: dict, rng: Optional[random.Random] = None) -> dict:
    """Mutação Direcional: pula para um quadrante vizinho do Latent Space.

    *rng* must be a seeded :class:`random.Random` instance when reproducibility
    is required.
    """
    _rng = rng if rng is not None else random.Random()

    perturbation = CreativeVector(
        tension=_rng.uniform(0.0, 1.0),
        density=_rng.uniform(0.0, 1.0),
        chaos=_rng.uniform(0.0, 1.0),
        rhythm=_rng.uniform(0.0, 1.0),
        stability=_rng.uniform(0.0, 1.0),
    )

    base_v = CreativeVector(0.5, 0.5, 0.5, 0.5, 0.5)
    new_v = base_v.blend(perturbation, factor=0.6)

    new_sig = get_signature_from_vector(new_v)
    plan["interpretation"]["motion_signature"] = new_sig
    return plan


def mutate(plan: dict, rng: Optional[random.Random] = None) -> dict:
    """Orquestrador de Mutação Genética."""
    import copy

    _rng = rng if rng is not None else random.Random()
    mutated = copy.deepcopy(plan)
    mutated = mutate_entropy(mutated, _rng)

    if _rng.random() > 0.5:
        mutated = mutate_motion(mutated, _rng)

    return mutated
