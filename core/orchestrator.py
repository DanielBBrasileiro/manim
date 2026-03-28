import yaml
import json
import subprocess
import os
import sys
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

class AgenticOrchestrator:
    def __init__(self, brief_path):
        self.brief_path = brief_path
        if not os.path.exists(brief_path):
            raise FileNotFoundError(f"❌ AIOX Falha: Briefing não encontrado em {brief_path}")
            
        with open(brief_path, "r") as f:
            self.brief = yaml.safe_load(f)
        
        os.makedirs("assets/brand", exist_ok=True)
        
    def sync_brand(self):
        print("🧬 AIOX: Sincronizando contratos de marca...")
        identity = self.brief.get("meta", {}).get("active_identity", "aiox_default")
        subprocess.run(["python3", "core/cli/brand.py", identity], check=True)

    def extract_intelligence(self):
        print("🧠 AIOX: Extraindo parâmetros do briefing...")
        required_keys = ["strategy", "tech_plan", "design_overlay"]
        for key in required_keys:
            if key not in self.brief:
                raise ValueError(f"❌ AIOX Falha: A chave obrigatória '{key}' sumiu. O Antigravity deve corrigir o YAML.")

        strategy = self.brief["strategy"]
        tech_plan = self.brief["tech_plan"]
        design = self.brief["design_overlay"]
        
        with open("assets/brand/dynamic_data.json", "w") as f:
            json.dump({
                "strategy": strategy,
                "tech_plan": tech_plan,
                "design": design
            }, f, indent=2)
            
        return tech_plan

    def run_manim(self, tech_plan):
        scenes = self.brief.get("scenes", [])
        if not scenes:
            print("⚠️ AIOX: Nenhuma cena Manim definida no briefing. Pulando...")
            return True

        for scene_data in scenes:
            if scene_data.get("engine") != "manim":
                continue
            
            scene_name = scene_data.get("scene")
            script = scene_data.get("script")
            print(f"💎 MANIM: Renderizando geometria de {scene_name}...")
            
            # Passa o PYTHONPATH silenciosamente para a IA não sofrer com ModuleNotFoundError
            env = dict(os.environ, PYTHONPATH=os.getcwd())
            cmd = ["manim", "-f", "-qh", script, scene_name]
            subprocess.run(cmd, check=True, cwd="engines/manim", env=env)
        return True

    def bridge_engines(self):
        """A Ponte Mágica: Copia o vídeo do Manim para o Remotion ler."""
        scenes = self.brief.get("scenes", [])
        for scene_data in scenes:
            if scene_data.get("engine") == "manim":
                scene_name = scene_data.get("scene")
                script_path = scene_data.get("script")
                script_name = Path(script_path).stem
                
                manim_output = Path(f"engines/manim/media/videos/{script_name}/1080p60/{scene_name}.mp4")
                remotion_public = Path("engines/remotion/public/manim_base.mp4")
                
                if manim_output.exists():
                    print(f"🌉 AIOX PONTE: Injetando vídeo {scene_name} na camada React...")
                    os.makedirs(remotion_public.parent, exist_ok=True)
                    shutil.copy(manim_output, remotion_public)
                else:
                    print(f"⚠️ AIOX Aviso: Vídeo do Manim não encontrado em {manim_output}")
                break

    def run_remotion(self):
        print(f"🎬 REMOTION: Compondo narrativa final...")
        comp = self.brief.get("composition", "Main")
        os.makedirs("output/renders", exist_ok=True)

        cmd = ["npx", "remotion", "render", "src/index.tsx", comp, f"../../output/renders/{comp}.mp4", "--force"]
        subprocess.run(cmd, check=True, cwd="engines/remotion")
        return True

    def run_post_processing(self):
        """Gera todos os formatos de output definidos no briefing."""
        output_cfg = self.brief.get("output", {})
        formats = output_cfg.get("formats", ["mp4"])
        social_variants = output_cfg.get("social_variants", [])
        timestamps = output_cfg.get("png_frame_timestamps", [])
        optimize = output_cfg.get("optimize", True)

        comp = self.brief.get("composition", "Main")
        source_mp4 = str(ROOT / "output" / "renders" / f"{comp}.mp4")

        if not Path(source_mp4).exists():
            print(f"⚠️  Post-processing: vídeo fonte não encontrado em {source_mp4}")
            return

        sys.path.insert(0, str(ROOT))
        from core.generators.gif_generator import encode_gif, encode_webm, extract_frames

        out_base = ROOT / "output"

        # ── Color Grading (sempre aplicado se preset definido) ──
        grade_preset = self.brief.get("creative", {}).get("grade_preset")
        if grade_preset:
            from core.generators.post_processor import PostProcessor
            graded_mp4 = str(out_base / "renders" / f"{comp}_graded.mp4")
            print(f"\n🎨 Color grading com preset '{grade_preset}'...")
            pp = PostProcessor(preset=grade_preset)
            if pp.process_video(source_mp4, graded_mp4):
                source_mp4 = graded_mp4  # Downstream usa o graded

        if "gif" in formats:
            gif_path = str(out_base / "gif" / f"{comp}.gif")
            print(f"\n🌀 Gerando GIF...")
            encode_gif(source_mp4, gif_path, fps=12, optimize=optimize)

        if "webm" in formats:
            webm_path = str(out_base / "webm" / f"{comp}.webm")
            print(f"\n📦 Gerando WebM...")
            encode_webm(source_mp4, webm_path)

        if "png_frames" in formats and timestamps:
            print(f"\n📸 Extraindo frames PNG em {timestamps}s...")
            extract_frames(source_mp4, timestamps, str(out_base / "frames"))

        if "carousel" in formats:
            print(f"\n🖼️  Gerando carrossel...")
            from core.generators.carousel_generator import carousel_from_video
            ts = timestamps or [0, 3, 6, 9, 12]
            platform = social_variants[0] if social_variants else "instagram"
            carousel_from_video(source_mp4, ts, str(out_base / "carousel"), platform=platform)

        if "svg" in formats:
            print(f"\n✏️  Exportando SVG...")
            from core.generators.svg_exporter import export_from_brief
            export_from_brief(self.brief_path)

        if "algo_art" in formats:
            print(f"\n🎨 Exportando arte generativa (p5.js)...")
            from core.generators.algo_art_exporter import export_from_brief as export_algo
            export_algo(self.brief_path)

        if "pdf" in formats:
            print(f"\n📄 Gerando PDF...")
            from core.generators.pdf_generator import generate_narrative_pdf
            title = self.brief.get("meta", {}).get("title", "AIOX")
            safe = title.lower().replace(" ", "_")[:40]
            pdf_path = str(out_base / "pdf" / f"{safe}.pdf")
            # Usa frames PNG extraídos se disponíveis, senão frames do output/frames/
            frames_dir = out_base / "frames"
            frame_paths = sorted([str(p) for p in frames_dir.glob("*.png")]) if frames_dir.exists() else []
            generate_narrative_pdf(self.brief_path, frame_paths=frame_paths or None, output_pdf=pdf_path)

        # Variants sociais: re-render Remotion com formato alvo
        for variant in social_variants:
            print(f"\n📱 Gerando variante social: {variant}...")
            variant_out = str(out_base / "renders" / f"{comp}_{variant}.mp4")
            try:
                cmd = [
                    "npx", "remotion", "render", "src/index.tsx", comp,
                    f"../../output/renders/{comp}_{variant}.mp4",
                    "--force",
                    f"--props={{\"social_variant\":\"{variant}\"}}"
                ]
                subprocess.run(cmd, check=True, cwd="engines/remotion")
                print(f"  ✅ {variant} → {variant_out}")
            except subprocess.CalledProcessError:
                print(f"  ⚠️  {variant}: render falhou (composição pode não suportar este variant ainda)")

    def run_pipeline(self):
        try:
            self.sync_brand()
            tech_plan = self.extract_intelligence()
            
            if self.run_manim(tech_plan):
                self.bridge_engines()
                self.run_remotion()
                self.run_post_processing()
                print("\n🏆 AIOX PIPELINE COMPLETE: Seu conteúdo está pronto em output/")
                return True
        except subprocess.CalledProcessError as e:
            print(f"\n❌ ERRO DE RENDERIZAÇÃO: O comando falhou.")
            print("Antigravity: Por favor, analise o código Manim ou React gerado e corrija-o.")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ ERRO FATAL: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    orch = AgenticOrchestrator(sys.argv[1])
    orch.run_pipeline()
