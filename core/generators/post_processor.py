"""
AIOX Post Processor — v4.4
============================
Aplica efeitos cinematográficos em frames PNG ou vídeo MP4.
Funciona 100% com numpy + Pillow — sem dependência de moderngl.

Efeitos disponíveis:
  chromatic_aberration  — deslocamento RGB radial (lente analógica)
  film_grain            — ruído de película (vai além do grain CSS)
  vignette              — escurecimento das bordas
  glow                  — brilho suave em áreas claras
  scanlines             — linhas de scan (estética CRT/cinematográfica)

Uso standalone:
    python3 core/generators/post_processor.py \\
        --input output/renders/Main.mp4 \\
        --effects chromatic_aberration vignette grain \\
        --output output/renders/Main_grade.mp4

Uso via orchestrator:
    processor = PostProcessor()
    processor.process_video("Main.mp4", "Main_grade.mp4", effects=[...])
"""
import numpy as np
from pathlib import Path
from typing import List, Dict, Any


# ── Efeitos por Frame (numpy puro) ───────────────────────────────────────────

def chromatic_aberration(
    frame: np.ndarray,
    strength: float = 0.006,
    time: float = 0.0,
) -> np.ndarray:
    """
    Desloca canais R e B em direções opostas radialmente.
    Simula aberração cromática de lente cinematográfica.

    strength: 0.002 (sutil) → 0.015 (extremo)
    """
    h, w = frame.shape[:2]
    y_coords = (np.arange(h) / h - 0.5) * 2
    x_coords = (np.arange(w) / w - 0.5) * 2
    xx, yy = np.meshgrid(x_coords, y_coords)
    dist = np.sqrt(xx**2 + yy**2)

    shift = (strength * dist * dist * 3.5).clip(0, 0.05)
    # Micro-jitter orgânico
    jitter = np.sin(time * 17.3) * 0.0002

    def _warp_channel(ch_idx, scale):
        dx = (xx * shift * scale * w + jitter * w).astype(np.float32)
        dy = (yy * shift * scale * h).astype(np.float32)
        src_x = np.clip((xx * w * 0.5 + w * 0.5 + dx).astype(int), 0, w - 1)
        src_y = np.clip((yy * h * 0.5 + h * 0.5 + dy).astype(int), 0, h - 1)
        return frame[src_y, src_x, ch_idx]

    result = frame.copy()
    result[:, :, 0] = _warp_channel(0,  1.0)   # R desvia para fora
    result[:, :, 2] = _warp_channel(2, -1.0)   # B desvia para dentro
    return result


def film_grain(
    frame: np.ndarray,
    intensity: float = 0.04,
    temporal: bool = True,
    time: float = 0.0,
) -> np.ndarray:
    """
    Adiciona ruído de película com variação temporal.
    Mais realista que grain CSS porque varia frame a frame.

    intensity: 0.02 (invisível) → 0.12 (granulado pesado)
    """
    h, w = frame.shape[:2]
    rng = np.random.default_rng(int(time * 1000) if temporal else 42)
    noise = rng.normal(0, intensity * 255, (h, w)).astype(np.float32)
    result = frame.astype(np.float32)
    result[:, :, 0] = np.clip(result[:, :, 0] + noise, 0, 255)
    result[:, :, 1] = np.clip(result[:, :, 1] + noise * 0.97, 0, 255)
    result[:, :, 2] = np.clip(result[:, :, 2] + noise * 0.95, 0, 255)
    return result.astype(np.uint8)


def vignette(
    frame: np.ndarray,
    strength: float = 0.45,
    softness: float = 0.6,
) -> np.ndarray:
    """
    Escurece as bordas gradualmente — concentra atenção no centro.
    Essential para qualidade cinematográfica percebida.

    strength: 0.2 (quase invisível) → 0.8 (dramaticamente escuro)
    """
    h, w = frame.shape[:2]
    y = np.linspace(-1, 1, h)
    x = np.linspace(-1, 1, w)
    xx, yy = np.meshgrid(x, y)
    dist = np.sqrt(xx**2 + yy**2)

    # Smooth vignette via raised cosine
    mask = 1.0 - np.clip((dist - softness) / (1.0 - softness), 0, 1) * strength
    mask = mask[:, :, np.newaxis]  # broadcast over channels

    result = (frame.astype(np.float32) * mask).clip(0, 255).astype(np.uint8)
    return result


def glow(
    frame: np.ndarray,
    radius: int = 8,
    intensity: float = 0.25,
    threshold: float = 0.75,
) -> np.ndarray:
    """
    Brilho suave em áreas mais claras — emissão luminosa cinematográfica.
    Simula bloom de lente real.

    threshold: 0.0 = tudo brilha | 0.8 = só os mais brancos
    """
    try:
        from PIL import Image, ImageFilter
    except ImportError:
        return frame

    img = Image.fromarray(frame)
    luminance = img.convert("L")
    lum_arr = np.array(luminance) / 255.0
    mask = (lum_arr > threshold).astype(np.float32)

    bright = img.copy()
    bright_arr = np.array(bright).astype(np.float32)
    bright_arr *= mask[:, :, np.newaxis]
    bright_img = Image.fromarray(bright_arr.clip(0, 255).astype(np.uint8))

    # Blur para criar o halo
    blurred = bright_img.filter(ImageFilter.GaussianBlur(radius=radius))
    blurred_arr = np.array(blurred).astype(np.float32)

    result = (frame.astype(np.float32) + blurred_arr * intensity).clip(0, 255)
    return result.astype(np.uint8)


def scanlines(
    frame: np.ndarray,
    spacing: int = 3,
    darkness: float = 0.08,
) -> np.ndarray:
    """
    Linhas horizontais sutis — estética cinema/CRT vintage.
    spacing: linha a cada N pixels | darkness: 0.05–0.20
    """
    result = frame.copy().astype(np.float32)
    for y in range(0, frame.shape[0], spacing):
        result[y] *= (1.0 - darkness)
    return result.clip(0, 255).astype(np.uint8)


def halation(
    frame: np.ndarray,
    radius: int = 15,
    intensity: float = 0.35,
    threshold: float = 0.65,
) -> np.ndarray:
    """
    Bloom óptico com difusão avermelhada sutil nos highlights.
    Simula dispersão luminosa em película real.
    """
    try:
        from PIL import Image, ImageFilter
    except ImportError:
        return frame

    img = Image.fromarray(frame)
    lum = img.convert("L")
    mask = (np.array(lum) > (threshold * 255)).astype(np.float32)
    
    # Extract highlights
    bright_arr = frame.astype(np.float32) * mask[:, :, np.newaxis]
    
    # Red shift for halation (red spreads further than G/B)
    halation_red = Image.fromarray(bright_arr[:, :, 0].astype(np.uint8))
    halation_red = halation_red.filter(ImageFilter.GaussianBlur(radius=radius * 1.2))
    
    halation_full = Image.fromarray(bright_arr.astype(np.uint8))
    halation_full = halation_full.filter(ImageFilter.GaussianBlur(radius=radius))
    
    h_red_arr = np.array(halation_red).astype(np.float32)
    h_full_arr = np.array(halation_full).astype(np.float32)
    
    # Merge: red is prioritized in the spill
    result = frame.astype(np.float32)
    result[:, :, 0] += h_red_arr * intensity
    result[:, :, 1] += h_full_arr[:, :] * intensity * 0.4
    result[:, :, 2] += h_full_arr[:, :] * intensity * 0.3
    
    return result.clip(0, 255).astype(np.uint8)


def breath_exposure(
    frame: np.ndarray,
    time: float = 0.0,
    amplitude: float = 0.04,
    frequency: float = 0.25,
) -> np.ndarray:
    """
    Variação sinusoidal sutil da exposição — simula câmera real respirando.
    """
    shift = 1.0 + np.sin(time * 2 * np.pi * frequency) * amplitude
    return (frame.astype(np.float32) * shift).clip(0, 255).astype(np.uint8)


def color_grade(
    frame: np.ndarray,
    emotion: str = "mastery",
) -> np.ndarray:
    """
    Aplica shift tonal simplificado baseado na emoção do ato.
    """
    _GRADES = {
        "curiosity": [0.95, 1.0, 1.05], # Cool/Cyan tones
        "tension":   [1.1, 0.95, 0.9], # High contrast, Warm highlights
        "mastery":   [1.02, 1.02, 0.98], # Balanced, slight gold
    }
    multipliers = _GRADES.get(emotion, [1.0, 1.0, 1.0])
    result = frame.astype(np.float32)
    for i in range(3):
        result[:, :, i] *= multipliers[i]
    return result.clip(0, 255).astype(np.uint8)


# ── PostProcessor ─────────────────────────────────────────────────────────────

EFFECT_FNS = {
    "chromatic_aberration": chromatic_aberration,
    "film_grain": film_grain,
    "vignette": vignette,
    "glow": glow,
    "scanlines": scanlines,
    "halation": halation,
    "breath_exposure": breath_exposure,
    "color_grade": color_grade,
}

# Presets narrativos
PRESETS: Dict[str, List[Dict]] = {
    "cinematic": [
        {"name": "chromatic_aberration", "strength": 0.005},
        {"name": "film_grain", "intensity": 0.035},
        {"name": "vignette", "strength": 0.4},
        {"name": "breath_exposure", "amplitude": 0.02},
    ],
    "genesis": [
        {"name": "vignette", "strength": 0.55, "softness": 0.5},
        {"name": "film_grain", "intensity": 0.025},
        {"name": "color_grade", "emotion": "curiosity"},
    ],
    "turbulence": [
        {"name": "chromatic_aberration", "strength": 0.009},
        {"name": "film_grain", "intensity": 0.055},
        {"name": "halation", "intensity": 0.4, "threshold": 0.6},
        {"name": "color_grade", "emotion": "tension"},
    ],
    "resolution": [
        {"name": "vignette", "strength": 0.3},
        {"name": "halation", "intensity": 0.25, "threshold": 0.7},
        {"name": "film_grain", "intensity": 0.02},
        {"name": "color_grade", "emotion": "mastery"},
    ],
    "premium": [
        {"name": "chromatic_aberration", "strength": 0.004},
        {"name": "vignette", "strength": 0.35},
        {"name": "halation", "radius": 12, "intensity": 0.3, "threshold": 0.72},
        {"name": "film_grain", "intensity": 0.03},
        {"name": "breath_exposure", "amplitude": 0.03},
    ],
}


class PostProcessor:
    """
    Aplica pipeline de efeitos cinematográficos em vídeo ou frames.

    Uso rápido com preset:
        pp = PostProcessor(preset="cinematic")
        pp.process_video("Main.mp4", "Main_grade.mp4")

    Uso customizado:
        pp = PostProcessor(effects=[
            {"name": "chromatic_aberration", "strength": 0.007},
            {"name": "vignette", "strength": 0.4},
        ])
        pp.process_frames("frames/", "graded/")
    """

    def __init__(
        self,
        effects: List[Dict[str, Any]] = None,
        preset: str = None,
    ):
        if preset and preset in PRESETS:
            self.effects = PRESETS[preset]
        elif effects:
            self.effects = effects
        else:
            self.effects = PRESETS["cinematic"]

    def apply_frame(self, frame: np.ndarray, time: float = 0.0) -> np.ndarray:
        """Aplica todos os efeitos em um único frame numpy."""
        result = frame
        for effect in self.effects:
            fn_name = effect.get("name")
            fn = EFFECT_FNS.get(fn_name)
            if fn is None:
                print(f"⚠️  Efeito desconhecido: {fn_name}")
                continue
            kwargs = {k: v for k, v in effect.items() if k != "name"}
            # Injetar time onde o efeito aceitar
            import inspect
            sig = inspect.signature(fn)
            if "time" in sig.parameters:
                kwargs["time"] = time
            result = fn(result, **kwargs)
        return result

    def process_frames(
        self,
        input_dir: str,
        output_dir: str,
        fps: float = 60.0,
    ) -> List[str]:
        """Aplica efeitos em um diretório de PNGs."""
        try:
            from PIL import Image
        except ImportError:
            raise ImportError("pip install Pillow")

        in_dir = Path(input_dir)
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        frames = sorted(in_dir.glob("*.png"))
        processed = []
        for i, fp in enumerate(frames):
            t = i / fps
            frame = np.array(Image.open(fp).convert("RGB"))
            graded = self.apply_frame(frame, time=t)
            out_path = out_dir / fp.name
            Image.fromarray(graded).save(str(out_path))
            processed.append(str(out_path))

        print(f"✅ {len(processed)} frames gradeados → {out_dir}")
        return processed

    def process_image(
        self,
        input_path: str,
        output_path: str | None = None,
        time: float = 0.0,
    ) -> str:
        """Aplica efeitos cinematográficos em uma imagem única."""
        try:
            from PIL import Image
        except ImportError:
            raise ImportError("pip install Pillow")

        source = Path(input_path)
        target = Path(output_path) if output_path else source
        target.parent.mkdir(parents=True, exist_ok=True)

        frame = np.array(Image.open(source).convert("RGB"))
        graded = self.apply_frame(frame, time=time)
        Image.fromarray(graded).save(str(target))
        return str(target)

    def process_video(
        self,
        input_mp4: str,
        output_mp4: str,
        fps: float = 60.0,
        crf: int = 18,
    ) -> bool:
        """
        Aplica efeitos frame a frame em um MP4.
        Pipeline: ffmpeg decode → numpy grade → ffmpeg encode.
        """
        import subprocess, shutil, tempfile

        if not shutil.which("ffmpeg"):
            print("⚠️  ffmpeg não encontrado.")
            return False

        try:
            from PIL import Image
        except ImportError:
            raise ImportError("pip install Pillow")

        tmp_dir = Path(tempfile.mkdtemp(prefix="aiox_grade_"))
        in_frames = tmp_dir / "in"
        out_frames = tmp_dir / "out"
        in_frames.mkdir()
        out_frames.mkdir()

        print(f"🎬 Post-processor: extraindo frames de {Path(input_mp4).name}...")
        subprocess.run(
            ["ffmpeg", "-i", input_mp4, "-q:v", "1", str(in_frames / "f%05d.png")],
            check=True, capture_output=True
        )

        png_files = sorted(in_frames.glob("*.png"))
        n = len(png_files)
        print(f"🎨 Aplicando {len(self.effects)} efeitos em {n} frames...")

        for i, fp in enumerate(png_files):
            t = i / fps
            frame = np.array(Image.open(fp).convert("RGB"))
            graded = self.apply_frame(frame, time=t)
            Image.fromarray(graded).save(str(out_frames / fp.name))

        print(f"📦 Recodificando → {Path(output_mp4).name}...")
        Path(output_mp4).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-y",
             "-framerate", str(fps),
             "-i", str(out_frames / "f%05d.png"),
             "-c:v", "libx264", "-crf", str(crf),
             "-pix_fmt", "yuv420p",
             output_mp4],
            check=True, capture_output=True
        )

        shutil.rmtree(tmp_dir, ignore_errors=True)
        print(f"✅ Graded → {output_mp4}")
        return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AIOX Post Processor")
    parser.add_argument("--input", required=True, help="MP4 ou diretório de PNGs")
    parser.add_argument("--output", required=True)
    parser.add_argument("--preset", default="cinematic",
                        choices=list(PRESETS.keys()))
    parser.add_argument("--fps", type=float, default=60.0)
    args = parser.parse_args()

    pp = PostProcessor(preset=args.preset)
    inp = Path(args.input)
    if inp.is_dir():
        pp.process_frames(args.input, args.output, fps=args.fps)
    else:
        pp.process_video(args.input, args.output, fps=args.fps)
