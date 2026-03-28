"""
AIOX Algorithmic Art Exporter — v4.4
======================================
Conecta a skill `algorithmic-art` (p5.js) ao pipeline de output.
Abre sketches p5.js em browser headless (Playwright) e exporta:
  - PNG estático (frame único)
  - GIF animado (sequência de frames)
  - Sequência de PNGs

O sketch p5.js deve seguir o contrato:
  - Chamar `captureFrame()` quando um frame está pronto para export
  - Expor `window.AIOX_READY = true` quando o sketch inicializou
  - Expor `window.AIOX_TOTAL_FRAMES` para animações (opcional)

Usage standalone:
    python3 core/generators/algo_art_exporter.py \\
        --sketch engines/p5/my_sketch.js \\
        --format gif --frames 60 --fps 12 \\
        --output output/algo/my_art.gif

Uso via orchestrator: quando briefing.output.formats inclui "algo_art".
"""
import json
import os
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# Template HTML que embuta o sketch p5.js para headless capture
_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; }}
  body {{ background: {bg}; overflow: hidden; }}
  canvas {{ display: block; }}
</style>
</head>
<body>
<script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.4/p5.min.js"></script>
<script>
window.AIOX_READY = false;
window.AIOX_FRAME = 0;
window.AIOX_TOTAL_FRAMES = {total_frames};

// Injeta seed do briefing
window.AIOX_SEED = {seed};
window.AIOX_ENTROPY = {entropy};
window.AIOX_WIDTH = {width};
window.AIOX_HEIGHT = {height};

// Override p5 createCanvas para garantir dimensões corretas
const _origSetup = window.setup;

{sketch_code}

// Patch: expõe canvas após setup
window.addEventListener('load', () => {{
  setTimeout(() => {{ window.AIOX_READY = true; }}, 300);
}});
</script>
</body>
</html>"""


def _load_tokens() -> dict:
    token_path = ROOT / "assets/brand/tokens.json"
    if token_path.exists():
        with open(token_path) as f:
            return json.load(f)
    return {}


def _build_html(
    sketch_code: str,
    width: int,
    height: int,
    seed: int,
    entropy: float,
    bg: str = "#000000",
    total_frames: int = 1,
) -> str:
    return _HTML_TEMPLATE.format(
        sketch_code=sketch_code,
        width=width,
        height=height,
        seed=seed,
        entropy=entropy,
        bg=bg,
        total_frames=total_frames,
    )


def export_static(
    sketch_path: str,
    output_path: str,
    width: int = 1080,
    height: int = 1080,
    seed: int = None,
    entropy: float = 0.5,
    wait_ms: int = 800,
) -> str:
    """
    Renderiza um frame estático de um sketch p5.js.

    Args:
        sketch_path: Caminho para o arquivo .js do sketch.
        output_path: Caminho de saída (PNG).
        width, height: Dimensões do canvas.
        seed: Seed para reprodutibilidade.
        entropy: Nível de variância orgânica.
        wait_ms: Milissegundos para aguardar o sketch renderizar.
    Returns:
        Caminho do PNG gerado.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ImportError("pip install playwright && playwright install chromium")

    import numpy as np
    _seed = seed if seed is not None else int(np.random.randint(0, 99999))

    tokens = _load_tokens()
    bg = tokens.get("brand", {}).get("color_states", {}).get("dark", {}).get("background", "#000000")

    sketch_code = Path(sketch_path).read_text()
    html = _build_html(sketch_code, width, height, _seed, entropy, bg, total_frames=1)

    tmp_html = Path(tempfile.mktemp(suffix=".html", prefix="aiox_algo_"))
    tmp_html.write_text(html)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(f"file://{tmp_html}", wait_until="networkidle")
            page.wait_for_timeout(wait_ms)
            page.wait_for_function("window.AIOX_READY === true", timeout=5000)
            page.screenshot(path=output_path, full_page=False, clip={
                "x": 0, "y": 0, "width": width, "height": height
            })
            browser.close()
    finally:
        tmp_html.unlink(missing_ok=True)

    print(f"✅ Algo art PNG → {output_path} (seed={_seed})")
    return output_path


def export_animation(
    sketch_path: str,
    output_path: str,
    n_frames: int = 60,
    fps: int = 12,
    width: int = 1080,
    height: int = 1080,
    seed: int = None,
    entropy: float = 0.5,
    frame_delay_ms: int = 80,
    output_format: str = "gif",
) -> str:
    """
    Renderiza animação p5.js como GIF ou sequência PNG.

    O sketch deve chamar window.AIOX_READY = true após cada frame
    ou usar o padrão de draw() loop normal.

    Args:
        n_frames: Número de frames a capturar.
        fps: FPS do GIF de saída.
        frame_delay_ms: Delay entre capturas de frame (ms).
        output_format: "gif" | "png_sequence"
    Returns:
        Caminho do arquivo/diretório gerado.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ImportError("pip install playwright && playwright install chromium")

    import numpy as np
    _seed = seed if seed is not None else int(np.random.randint(0, 99999))

    tokens = _load_tokens()
    bg = tokens.get("brand", {}).get("color_states", {}).get("dark", {}).get("background", "#000000")

    sketch_code = Path(sketch_path).read_text()
    html = _build_html(sketch_code, width, height, _seed, entropy, bg, total_frames=n_frames)

    tmp_html = Path(tempfile.mktemp(suffix=".html", prefix="aiox_algo_anim_"))
    tmp_html.write_text(html)

    frames_dir = Path(tempfile.mkdtemp(prefix="aiox_algo_frames_"))
    frame_paths = []

    print(f"🎨 Capturando {n_frames} frames do sketch p5.js...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(f"file://{tmp_html}", wait_until="networkidle")
            page.wait_for_timeout(500)

            for i in range(n_frames):
                frame_path = str(frames_dir / f"frame_{i:05d}.png")
                page.screenshot(path=frame_path, full_page=False, clip={
                    "x": 0, "y": 0, "width": width, "height": height
                })
                frame_paths.append(frame_path)
                page.wait_for_timeout(frame_delay_ms)

            browser.close()
    finally:
        tmp_html.unlink(missing_ok=True)

    print(f"  ✅ {len(frame_paths)} frames capturados")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    if output_format == "gif":
        from core.generators.gif_generator import encode_gif
        # Monta MP4 temporário dos frames para usar o pipeline gif existente
        tmp_mp4 = str(frames_dir / "tmp_algo.mp4")
        import subprocess
        subprocess.run(
            ["ffmpeg", "-y", "-framerate", str(fps),
             "-i", str(frames_dir / "frame_%05d.png"),
             "-c:v", "libx264", "-pix_fmt", "yuv420p", tmp_mp4],
            check=True, capture_output=True
        )
        encode_gif(tmp_mp4, output_path, fps=fps, width=width)
        shutil.rmtree(frames_dir, ignore_errors=True)
        print(f"✅ Algo art GIF → {output_path} (seed={_seed})")
        return output_path

    elif output_format == "png_sequence":
        out_dir = Path(output_path)
        out_dir.mkdir(parents=True, exist_ok=True)
        for fp in frame_paths:
            shutil.copy(fp, out_dir / Path(fp).name)
        shutil.rmtree(frames_dir, ignore_errors=True)
        print(f"✅ Algo art PNG sequence → {out_dir} ({n_frames} frames, seed={_seed})")
        return str(out_dir)


def export_from_brief(brief_path: str) -> list:
    """
    Exporta arte generativa definida em um briefing YAML.
    Espera campos em: brief.algo_art (script, frames, fps, format, entropy)
    """
    import yaml
    with open(brief_path) as f:
        brief = yaml.safe_load(f)

    algo_cfg = brief.get("algo_art", {})
    if not algo_cfg:
        print("⚠️  Nenhuma config 'algo_art' no briefing.")
        return []

    script = algo_cfg.get("script")
    if not script or not Path(script).exists():
        print(f"⚠️  Sketch p5.js não encontrado: {script}")
        return []

    creative = brief.get("creative", {})
    entropy = creative.get("entropy", 0.5)
    fmt_id = brief.get("meta", {}).get("format", "square_1_1")
    dims = {"square_1_1": (1080, 1080), "vertical_9_16": (1080, 1920), "wide_16_9": (1920, 1080)}
    w, h = dims.get(fmt_id, (1080, 1080))

    title = brief.get("meta", {}).get("title", "algo_art")
    safe = title.lower().replace(" ", "_")[:30]
    outputs = []

    fmt = algo_cfg.get("format", "gif")
    if fmt == "static":
        out = str(ROOT / "output" / "algo" / f"{safe}.png")
        export_static(script, out, width=w, height=h, entropy=entropy)
        outputs.append(out)
    else:
        n_frames = algo_cfg.get("frames", 60)
        fps = algo_cfg.get("fps", 12)
        out = str(ROOT / "output" / "algo" / f"{safe}.{fmt}")
        export_animation(script, out, n_frames=n_frames, fps=fps,
                         width=w, height=h, entropy=entropy, output_format=fmt)
        outputs.append(out)

    return outputs


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AIOX Algorithmic Art Exporter")
    parser.add_argument("--sketch", required=True, help="Arquivo .js do sketch p5.js")
    parser.add_argument("--output", required=True, help="Arquivo de saída")
    parser.add_argument("--format", choices=["png", "gif", "png_sequence"], default="gif")
    parser.add_argument("--frames", type=int, default=60)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--entropy", type=float, default=0.5)
    args = parser.parse_args()

    if args.format == "png":
        export_static(args.sketch, args.output, args.width, args.height,
                      args.seed, args.entropy)
    else:
        export_animation(args.sketch, args.output, args.frames, args.fps,
                         args.width, args.height, args.seed, args.entropy,
                         output_format=args.format)
