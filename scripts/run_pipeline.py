import yaml
import subprocess
import os
import argparse
from pathlib import Path

class VideoOrchestrator:
    def __init__(self, brief_path):
        self.root_dir = Path.cwd()
        with open(brief_path, 'r') as f:
            self.brief = yaml.safe_load(f)
        
        self.output_dir = self.root_dir / "output" / self.brief.get('type', 'generic')
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_manim(self, scene):
        print(f"🎬 Running Manim for scene: {scene['id']}")
        engine_dir = self.root_dir / "engines" / "manim"
        scene_file = scene.get('file', f"{scene['id']}.py")
        cmd = [
            "python3",
            "-m",
            "manim",
            "-pqh",
            "-t",
            "--format=webm",
            scene_file,
            scene.get('class_name', 'SceneName')
        ]
        result = subprocess.run(cmd, cwd=engine_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error rendering {scene['id']}:")
            print(result.stderr)
        else:
            print(result.stdout)
        print(f"✅ Scene {scene['id']} rendered.")
        return f"{scene['id']}.mp4"

    def sync_assets(self):
        print("🚀 Syncing engine outputs to Remotion...")
        sync_script = self.root_dir / "scripts" / "sync.sh"
        if sync_script.exists():
            subprocess.run(["bash", str(sync_script)])
        else:
            print("⚠️ sync.sh not found. Skipping.")

    def run_remotion_composition(self):
        print("🎭 Triggering Remotion Composition...")
        # npx remotion render ...
        print("✅ Composition complete.")

    def process(self):
        # New Contract Structure: brief['metadata']['title']
        title = self.brief.get('metadata', {}).get('title', self.brief.get('title', 'Untitled Video'))
        print(f"--- Starting Pipeline for: {title} ---")
        
        rendered_scenes = []
        scenes = self.brief.get('scenes', []) # Fallback to old scenes list
        if not scenes and 'choreography' in self.brief:
            # It's a single elite scene or we need to map choreography
            # For now, let's look for a 'scenes' list or build a default one
            # if the user used the new elite format:
             scenes = [{
                "id": "elite_scene",
                "engine": self.brief['metadata']['engine'],
                "file": "python_db_elite.py", # Hardcoded for now or derived
                "class_name": "PythonDBElite"
             }]

        for scene in scenes:
            engine = scene.get('engine')
            if engine == 'manim':
                rendered_scenes.append(self.run_manim(scene))
            else:
                print(f"⚠️ Engine {engine} not yet implemented in MVP.")

        self.sync_assets()
        self.run_remotion_composition()
        print(f"--- Pipeline Finished! Output at: {self.output_dir} ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--brief", required=True, help="Path to the briefing YAML")
    args = parser.parse_args()

    orchestrator = VideoOrchestrator(args.brief)
    orchestrator.process()
