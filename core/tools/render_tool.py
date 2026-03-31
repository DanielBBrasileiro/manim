import os
import subprocess
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

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
    output_path = ROOT / "output" / "renders" / f"{comp}.mp4"
    previous_mtime = output_path.stat().st_mtime if output_path.exists() else 0
    runner = str(ROOT / "scripts" / "run_remotion_node.sh")
    cli_cmd = [
        "/bin/zsh",
        "-lc",
        f"cd {ROOT / 'engines' / 'remotion'} && npm exec remotion render src/index.tsx {comp} ../../output/renders/{comp}.mp4 --force",
    ]
    direct_cmd = [
        "bash",
        runner,
        str(ROOT / "scripts" / "remotion_direct.js"),
        "render",
        comp,
        str(output_path),
    ]
    render_mode = os.getenv("AIOX_REMOTION_RENDER_MODE", "auto").strip().lower()
    cli_timeout = int(os.getenv("AIOX_REMOTION_CLI_TIMEOUT_SECONDS", "45"))

    if render_mode == "direct":
        subprocess.run(direct_cmd, check=True, cwd=str(ROOT))
    elif render_mode == "cli":
        subprocess.run(cli_cmd, check=True, cwd=str(ROOT))
    else:
        try:
            subprocess.run(
                direct_cmd,
                check=True,
                cwd=str(ROOT),
            )
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            print("⚠️ [Remotion Tool] Renderer direto falhou. Tentando CLI...")
            subprocess.run(
                cli_cmd,
                check=True,
                cwd=str(ROOT),
                timeout=cli_timeout,
            )

    if not output_path.exists():
        raise RuntimeError(f"Render final nao gerou arquivo: {output_path}")

    current_mtime = output_path.stat().st_mtime
    if current_mtime <= previous_mtime:
        raise RuntimeError(
            f"Render final nao atualizou o arquivo esperado: {output_path}"
        )

def render_pipeline(plan: dict):
    """Encapsula a mecânica dura do antigo Orchestrator."""
    scene_name = "EntropyDemo"
    script_path = "scenes/cde_entropy_demo.py"
    
    # Simula gravação do tech_plan para a cena ler
    import json
    with open(ROOT / "assets" / "brand" / "dynamic_data.json", "w") as f:
        # Retrocompatibilidade com IntelligenceLoader
        entropy_package = plan["interpretation"].copy()
        entropy_package["raw"] = plan["entropy"]
        
        json.dump({
            "tech_plan": {
                "archetype": plan["archetype"],
                "entropy": entropy_package
            },
            "design_overlay": {
                "aesthetic_family": plan["aesthetic_family"]
            }
        }, f, indent=2)

    try:
        run_manim(scene_name, script_path)
        bridge_engines(scene_name, script_path)
        run_remotion()
        return True
    except (subprocess.CalledProcessError, RuntimeError) as error:
        print(f"❌ [Render Tool] Falha no pipeline final: {error}")
        return False
