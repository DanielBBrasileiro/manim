from __future__ import annotations

import os
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ExecutionPolicy:
    mode: str
    description: str
    allow_preview: bool
    allow_render: bool
    allow_quality: bool
    allow_memory_persist: bool
    allow_governed_persist: bool
    judge_from_existing_outputs: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_POLICY_REGISTRY: dict[str, ExecutionPolicy] = {
    "planning_only": ExecutionPolicy(
        mode="planning_only",
        description="Compile intent and artifact planning only; stop before preview or render.",
        allow_preview=False,
        allow_render=False,
        allow_quality=False,
        allow_memory_persist=False,
        allow_governed_persist=True,
    ),
    "preview_only": ExecutionPolicy(
        mode="preview_only",
        description="Run planning plus preview/iteration loop; stop before final render.",
        allow_preview=True,
        allow_render=False,
        allow_quality=False,
        allow_memory_persist=False,
        allow_governed_persist=True,
    ),
    "judge_only": ExecutionPolicy(
        mode="judge_only",
        description="Skip render and judge existing outputs only.",
        allow_preview=False,
        allow_render=False,
        allow_quality=True,
        allow_memory_persist=False,
        allow_governed_persist=True,
        judge_from_existing_outputs=True,
    ),
    "benchmark": ExecutionPolicy(
        mode="benchmark",
        description="Lightweight benchmark mode for preview evidence and run summaries.",
        allow_preview=True,
        allow_render=False,
        allow_quality=False,
        allow_memory_persist=False,
        allow_governed_persist=True,
    ),
    "full_render": ExecutionPolicy(
        mode="full_render",
        description="Normal AIOX path: preview, render, final quality, and memory persistence.",
        allow_preview=True,
        allow_render=True,
        allow_quality=True,
        allow_memory_persist=True,
        allow_governed_persist=True,
    ),
    "safe_mode": ExecutionPolicy(
        mode="safe_mode",
        description="Non-destructive runtime inspection with preview allowed and no render/memory writes.",
        allow_preview=True,
        allow_render=False,
        allow_quality=False,
        allow_memory_persist=False,
        allow_governed_persist=False,
    ),
}

_ALIASES = {
    "plan": "planning_only",
    "preview": "preview_only",
    "judge": "judge_only",
    "full": "full_render",
    "render": "full_render",
    "read_only": "safe_mode",
    "safe": "safe_mode",
}


def available_execution_modes() -> list[str]:
    return sorted(_POLICY_REGISTRY.keys())


def resolve_execution_policy(mode: str | None = None) -> ExecutionPolicy:
    requested = str(mode or os.getenv("AIOX_EXECUTION_MODE", "full_render")).strip().lower()
    requested = _ALIASES.get(requested, requested)
    return _POLICY_REGISTRY.get(requested, _POLICY_REGISTRY["full_render"])
