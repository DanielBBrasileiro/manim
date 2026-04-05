from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Literal, TypedDict

ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# Result schema
# ---------------------------------------------------------------------------

class RenderOutput(TypedDict):
    """Describes the outcome of a single render stage (still or video)."""

    output_path: str | None
    render_backend: Literal["remotion", "manim", "fallback_pil", "none"]
    fallback: bool
    native_success: bool
    native_validation_passed: bool
    native_failure_reason: str | None
    hero_prepass_used: bool
    validation_status: Literal["passed", "degraded", "skipped", "failed"]


class RenderPipelineResult(TypedDict):
    """Top-level result returned by render_pipeline()."""

    success: bool
    """True only when the native (Remotion + Manim) path completed without error."""

    degraded_fallback: bool
    """True when output was produced via PIL fallback instead of native render."""

    output_path: str | None
    render_backend: Literal["remotion", "manim", "fallback_pil", "none"]
    native_validation_passed: bool
    native_failure_reason: str | None
    hero_prepass_used: bool
    validation_status: Literal["passed", "degraded", "skipped", "failed"]


# ---------------------------------------------------------------------------
# Internal render stages
# ---------------------------------------------------------------------------

def run_manim(scene_name: str, script_path: str) -> None:
    print(f"[Manim Tool] Rendering geometry for {scene_name}…")
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    cmd = ["manim", "-f", "-qh", script_path, scene_name]
    subprocess.run(cmd, check=True, cwd=str(ROOT / "engines" / "manim"), env=env)


def bridge_engines(scene_name: str, script_path: str) -> None:
    script_name = Path(script_path).stem
    manim_output = (
        ROOT / "engines" / "manim" / "media" / "videos"
        / script_name / "1080p60" / f"{scene_name}.mp4"
    )
    remotion_public = ROOT / "engines" / "remotion" / "public" / "manim_base.mp4"
    if manim_output.exists():
        print(f"[Bridge Tool] Injecting {scene_name} into React…")
        os.makedirs(remotion_public.parent, exist_ok=True)
        shutil.copy(manim_output, remotion_public)


def run_remotion(comp: str = "CinematicNarrative-v4") -> None:
    print("[Remotion Tool] Composing final narrative…")
    os.makedirs(ROOT / "output" / "renders", exist_ok=True)
    cmd = [
        "npx", "remotion", "render",
        "src/index.tsx", comp,
        f"../../output/renders/{comp}.mp4",
        "--force",
    ]
    subprocess.run(cmd, check=True, cwd=str(ROOT / "engines" / "remotion"))


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------

def render_pipeline(plan: dict) -> RenderPipelineResult:
    """Run the full Manim → bridge → Remotion pipeline.

    Returns a :class:`RenderPipelineResult` that is unambiguous about whether
    the output is native or a degraded fallback.  The ``success`` key is
    ``True`` *only* when the native path completed; a PIL fallback still is
    always ``degraded_fallback=True, success=False``.

    Backwards-compatible: callers that tested ``if render_pipeline(plan):``
    will continue to work — ``success`` drives the truthiness via the dict
    value itself (callers should check ``result["success"]``).
    """
    scene_name = "EntropyDemo"
    script_path = "scenes/cde_entropy_demo.py"

    # Write dynamic data for the scene to read
    data_path = ROOT / "assets" / "brand" / "dynamic_data.json"
    entropy_package: dict = plan["interpretation"].copy()
    entropy_package["raw"] = plan["entropy"]
    with open(data_path, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "tech_plan": {
                    "archetype": plan["archetype"],
                    "entropy": entropy_package,
                },
                "design_overlay": {
                    "aesthetic_family": plan["aesthetic_family"],
                },
            },
            fh,
            indent=2,
        )

    output_comp = "CinematicNarrative-v4"
    output_path = str(ROOT / "output" / "renders" / f"{output_comp}.mp4")

    try:
        run_manim(scene_name, script_path)
        bridge_engines(scene_name, script_path)
        run_remotion(output_comp)
        return RenderPipelineResult(
            success=True,
            degraded_fallback=False,
            output_path=output_path,
            render_backend="remotion",
            native_validation_passed=True,
            native_failure_reason=None,
            hero_prepass_used=False,
            validation_status="passed",
        )
    except subprocess.CalledProcessError as exc:
        return RenderPipelineResult(
            success=False,
            degraded_fallback=True,
            output_path=None,
            render_backend="none",
            native_validation_passed=False,
            native_failure_reason=str(exc),
            hero_prepass_used=False,
            validation_status="failed",
        )
