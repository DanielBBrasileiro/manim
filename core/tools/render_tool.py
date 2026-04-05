from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
_PROPS_DIR = ROOT / "output" / "props"


# ---------------------------------------------------------------------------
# Props-file IPC helpers
# ---------------------------------------------------------------------------

def write_props_file(props: dict[str, Any], label: str) -> Path:
    """Serialise *props* to ``output/props/<label>.json`` and return the path.

    Writing props to a file instead of an env-var string eliminates the OS
    environment variable size limit (~128 KB on Linux, ~32 KB on macOS) that
    causes silent truncation for large render manifests.
    """
    _PROPS_DIR.mkdir(parents=True, exist_ok=True)
    # Sanitise label to a safe filename
    safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)
    props_path = _PROPS_DIR / f"{safe_label}.json"
    props_path.write_text(json.dumps(props, indent=2, ensure_ascii=False), encoding="utf-8")
    return props_path


# ---------------------------------------------------------------------------
# Render stage functions
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


def run_remotion(
    comp: str = "CinematicNarrative-v4",
    *,
    props: dict[str, Any] | None = None,
    props_path: Path | None = None,
) -> None:
    """Invoke Remotion via *remotion_direct.js* using file-based IPC.

    Exactly one of *props* or *props_path* must be provided:
    - *props*      — dict serialised to a temp file under ``output/props/``
    - *props_path* — pre-existing props file (caller owns lifecycle)

    The Node script receives ``REMOTION_INPUT_PROPS_PATH`` and calls
    ``remotion render --props <file>`` so payload size is not constrained by
    the OS environment variable limit.
    """
    if props is not None and props_path is None:
        props_path = write_props_file(props, label=comp)
    elif props_path is None:
        # Neither provided — write an empty object so the script doesn't fail
        # on compositions that don't require inputProps.
        props_path = write_props_file({}, label=comp)

    resolved_path = props_path.resolve()
    output_path = ROOT / "output" / "renders" / f"{comp}.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    env = dict(
        os.environ,
        REMOTION_INPUT_PROPS_PATH=str(resolved_path),
    )

    node_script = ROOT / "scripts" / "remotion_direct.js"
    cmd = [
        "node",
        str(node_script),
        "--comp", comp,
        "--output", str(output_path),
    ]
    print(f"[Remotion Tool] Composing {comp} via file IPC ({resolved_path.name})…")
    subprocess.run(cmd, check=True, cwd=str(ROOT), env=env)


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------

def render_pipeline(plan: dict[str, Any]) -> bool:
    """Encapsula a mecânica dura do antigo Orchestrator."""
    scene_name = "EntropyDemo"
    script_path = "scenes/cde_entropy_demo.py"

    # Write dynamic_data.json for the Manim scene (IntelligenceLoader compat)
    entropy_package: dict[str, Any] = plan["interpretation"].copy()
    entropy_package["raw"] = plan["entropy"]
    dynamic_data_path = ROOT / "assets" / "brand" / "dynamic_data.json"
    dynamic_data_path.parent.mkdir(parents=True, exist_ok=True)
    dynamic_data_path.write_text(
        json.dumps(
            {
                "tech_plan": {
                    "archetype": plan["archetype"],
                    "entropy": entropy_package,
                },
                "design_overlay": {
                    "aesthetic_family": plan["aesthetic_family"],
                },
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # Build Remotion inputProps from the plan (file-based IPC — no size limit)
    remotion_props: dict[str, Any] = {
        "archetype": plan["archetype"],
        "aesthetic_family": plan["aesthetic_family"],
        "interpretation": plan["interpretation"],
    }

    try:
        run_manim(scene_name, script_path)
        bridge_engines(scene_name, script_path)
        run_remotion(props=remotion_props)
        return True
    except subprocess.CalledProcessError:
        return False
