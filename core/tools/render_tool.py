import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def _derive_seed(data: dict) -> int:
    """Deterministic integer seed derived from a dict via SHA-256."""
    key = json.dumps(data, sort_keys=True, default=str)
    return int(hashlib.sha256(key.encode()).hexdigest()[:16], 16) & 0x7FFFFFFFFFFFFFFF

def run_manim(scene_name: str, script_path: str):
    print(f"💎 [Manim Tool] Renderizando geometria de {scene_name}...")
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    cmd = ["manim", "-f", "-qh", script_path, scene_name]
    subprocess.run(cmd, check=True, cwd=str(ROOT / "engines" / "manim"), env=env)

def bridge_engines(scene_name: str, script_path: str):
    script_name = Path(script_path).stem
    manim_output = ROOT / "engines" / "manim" / "media" / "videos" / script_name / "1080p60" / f"{scene_name}.mp4"
    remotion_public = ROOT / "engines" / "remotion" / "public" / "manim_base.mp4"
    if manim_output.exists():
        print(f"🌉 [Bridge Tool] Injetando {scene_name} no React...")
        os.makedirs(remotion_public.parent, exist_ok=True)
        shutil.copy(manim_output, remotion_public)

def run_remotion(comp="CinematicNarrative-v4"):
    print(f"🎬 [Remotion Tool] Compondo narrativa final...")
    os.makedirs(ROOT / "output" / "renders", exist_ok=True)
    cmd = ["npx", "remotion", "render", "src/index.tsx", comp, f"../../output/renders/{comp}.mp4", "--force"]
    subprocess.run(cmd, check=True, cwd=str(ROOT / "engines" / "remotion"))

def render_pipeline(plan: dict):
    """Encapsula a mecânica dura do antigo Orchestrator."""
    scene_name = "EntropyDemo"
    script_path = "scenes/cde_entropy_demo.py"
    
    # Write dynamic_data.json — contract: tech_plan + design_overlay + seed only
    entropy_package = plan["interpretation"].copy()
    entropy_package["raw"] = plan["entropy"]
    dynamic_payload = {
        "tech_plan": {
            "archetype": plan["archetype"],
            "entropy": entropy_package,
        },
        "design_overlay": {
            "aesthetic_family": plan["aesthetic_family"],
        },
        "seed": plan.get("rng_seed") or _derive_seed({
            "archetype": plan["archetype"],
            "entropy": plan["entropy"],
        }),
    }
    with open(ROOT / "assets" / "brand" / "dynamic_data.json", "w") as f:
        json.dump(dynamic_payload, f, indent=2)

    try:
        run_manim(scene_name, script_path)
        bridge_engines(scene_name, script_path)
        run_remotion()
        return True
    except subprocess.CalledProcessError:
        return False
