from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from core.intelligence.model_profiles import available_profiles

ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass(frozen=True)
class CapabilityRegistry:
    targets: tuple[dict[str, Any], ...]
    renderers: tuple[dict[str, Any], ...]
    style_packs: tuple[str, ...]
    quality_gates: tuple[str, ...]
    profiles: tuple[str, ...]
    model_roles: tuple[str, ...]


def _load_layout_contract() -> dict[str, Any]:
    path = ROOT / "contracts" / "layout.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def build_capability_registry() -> CapabilityRegistry:
    layout = _load_layout_contract()
    raw_targets = layout.get("output_targets", {}) if isinstance(layout.get("output_targets"), dict) else {}
    targets = []
    renderers = []
    for target_id, target in raw_targets.items():
        if not isinstance(target, dict):
            continue
        render_mode = str(target.get("render_mode", "video")).strip().lower()
        composition = str(target.get("composition", "")).strip()
        targets.append(
            {
                "id": target_id,
                "composition": composition,
                "render_mode": render_mode,
                "purpose": target.get("purpose"),
                "priority": target.get("priority"),
            }
        )
        renderers.append(
            {
                "target_id": target_id,
                "engine": "remotion",
                "native": True,
                "render_mode": render_mode,
                "composition": composition,
            }
        )
        renderers.append(
            {
                "target_id": target_id,
                "engine": "fallback",
                "native": False,
                "render_mode": render_mode,
                "composition": composition,
            }
        )

    style_pack_dir = ROOT / "contracts" / "references"
    style_packs = tuple(sorted(path.stem for path in style_pack_dir.glob("*.yaml")))
    quality_gates = (
        "story_atoms_required",
        "max_words_per_screen",
        "negative_space_target",
        "safe_zone_conformance",
        "contrast_floor",
        "artifact_updated",
    )
    model_roles = ("fast_plan", "plan", "quality_plan", "vision_plan", "copy_refiner", "variant_ranker")
    return CapabilityRegistry(
        targets=tuple(targets),
        renderers=tuple(renderers),
        style_packs=style_packs,
        quality_gates=quality_gates,
        profiles=tuple(sorted(available_profiles().keys())),
        model_roles=model_roles,
    )
