from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from core.intelligence.model_capabilities import build_capability_snapshot
from core.intelligence.model_profiles import get_active_profile
from core.runtime.capability_registry import build_capability_registry
from core.runtime.model_runtime import build_runtime_os_report

ROOT = Path(__file__).resolve().parent.parent.parent


def _command_ok(cmd: list[str], cwd: Path | None = None, timeout: float = 5.0) -> bool:
    try:
        subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
        return True
    except Exception:
        return False


def build_capability_pool(artifact_plan: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = build_capability_registry()
    profile = get_active_profile()
    runtime_os = build_runtime_os_report(profile.name)
    style_pack_ids = list((artifact_plan or {}).get("style_pack_ids", []))
    renderers = {
        "remotion_native": _command_ok(["/bin/bash", str(ROOT / "scripts" / "run_remotion_node.sh"), "-v"], cwd=ROOT),
        "manim": _command_ok(["python3", "-m", "manim", "--version"], cwd=ROOT),
        "fallback": True,
    }
    valid_style_packs = [pack for pack in style_pack_ids if pack in registry.style_packs]
    return {
        "profile": profile.name,
        "provider": profile.provider,
        "runtime_os": runtime_os,
        "models": build_capability_snapshot(),
        "renderers": renderers,
        "native_targets": [entry["id"] for entry in registry.targets if renderers["remotion_native"] and entry.get("native_support", True)],
        "style_packs": {
            "requested": style_pack_ids,
            "valid": valid_style_packs,
            "available": list(registry.style_packs),
        },
        "quality_gates": list(registry.quality_gates),
    }
